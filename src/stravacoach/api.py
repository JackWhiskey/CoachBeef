from asyncio import tasks
from contextlib import asynccontextmanager
import json
import asyncio

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sync_manager import sync_detailed_activities, sync_strava_to_db
from stravalib.model import DetailedAthlete
from requests import Session
from openai_client import OpenAIManager, ChatRequest
from db_client import DBClient
from stravalib.strava_model import DetailedActivity, SummaryActivity, Zones
from datetime import datetime
from strava_client import StravaManager
from db_model import DBActivity, DBActivityDetail, DBChatMessage, PersistDBChatMessage

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server is spinning up...")
    tasks = []

    if strava_manager and db_client:
        print("Triggering automatic Strava sync...")
        # Manually extract a database session from the generator
        startup_sync_task = asyncio.create_task(run_initial_syncs())
        tasks.append(startup_sync_task)

    background_sync = asyncio.create_task(periodic_strava_sync())
    detailed_sync = asyncio.create_task(periodic_detailed_strava_sync())
    tasks.extend([background_sync, detailed_sync])

    yield # This yields control back to FastAPI so it can start accepting requests!
    
    # --- SHUTDOWN ---
    print("Server shutting down...")
    for task in tasks:
        task.cancel()

# Initialize the FastAPI app
app = FastAPI(title="StravaCoach API", lifespan=lifespan)

# Initialize your manager
try:   
    db_client = DBClient()
except Exception as e:
    print(f"Failed to initialize DBClient: {e}")
    db_client = None

# (For now, it uses your local tokens.json)
try:
    strava_manager = StravaManager()
except Exception as e:
    print(f"Failed to initialize StravaManager: {e}")
    strava_manager = None

try:
    openai_manager = OpenAIManager(
        athlete_intelligence=False
    )
except Exception as e:
    print(f"Failed to initialize OpenAIManager: {e}")
    openai_manager = None

# ==========================================
# CORS CONFIGURATION
# ==========================================
# React will run on a different port (like localhost:5173). 
# We MUST tell FastAPI to allow requests from that port, or the browser will block them.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# STRAVA EXPOSED API ENDPOINTS
# ==========================================

@app.get("/")
def read_root():
    return {"message": "StravaCoach API is running!"}

@app.get("/api/profile", response_model=None)
def get_profile() -> DetailedAthlete | None:
    if not strava_manager:
        raise HTTPException(status_code=500, detail="Strava API not initialized")
    
    profile = strava_manager.get_athlete()
    if profile:
        return profile
    raise HTTPException(status_code=404, detail="Profile not found")

@app.get("/api/athlete/zones", response_model=None)
def get_athlete_zones() -> Zones | None:
    if not strava_manager:
        raise HTTPException(status_code=500, detail="Strava API not initialized")
    
    zones = strava_manager.get_athlete_zones()
    if zones:
        return zones
    raise HTTPException(status_code=404, detail="Zones not found")

@app.get("/api/activities")
def get_activities(before: str | None = None, after: str | None = None, limit: int = 100, db: Session = Depends(db_client.get_db)):
    try:
        # Query the local database instead of Strava API!
        # Order by newest first
        db_activities = db.query(DBActivity
                                 ).filter(
                                        (DBActivity.start_date <= before) if before else True,
                                        (DBActivity.start_date >= after) if after else True
                                 ).order_by(DBActivity.start_date.desc()
                                            ).limit(limit).all()
        
        # Convert SQLAlchemy objects to standard dictionaries for the JSON response
        results = []
        for act in db_activities:
            # Instantiate the StravaLib Pydantic model directly
            summary = SummaryActivity(
                id=act.id,
                name=act.name,
                type=act.type,
                start_date=act.start_date,
                distance=act.distance,
                moving_time=act.moving_time,
                average_speed=act.average_speed,
                # stravalib expects a map object for the polyline
                map={"summary_polyline": act.summary_polyline},
                workout_type=act.workout_type_num
            )
            safe_dict = json.loads(summary.json())
            results.append(safe_dict)
            
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# TODO: add pagination parameters (like page number and page size) to this endpoint for better performance with large activity histories
# TODO: Query the database for activities instead of hitting the Strava API every time.
def get_activities_using_api(before: str | None = None, after: str | None = None, limit: int = 100):
    if not strava_manager:
        raise HTTPException(status_code=500, detail="Strava API not initialized")
    
    datetime_before = None
    datetime_after = None
    try:
        if before:
            datetime_before = datetime.strptime(before, "%Y-%m-%dT%H:%M:%SZ")
        if after:
            datetime_after = datetime.strptime(after, "%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")

    # This returns an iterator of SummaryActivity objects
    raw_activities = strava_manager.get_activities(before=datetime_before, after=datetime_after, limit=limit)

    # Unpack the iterator and safely serialize each object
    activities_list = []
    for act in raw_activities:
        # act.json() safely converts the Pydantic model and datetimes to a JSON string.
        # json.loads() instantly turns it back into a safe Python dictionary for JSONResponse.
        safe_dict = json.loads(act.json())
        activities_list.append(safe_dict)

    if activities_list:
        return JSONResponse(content=activities_list)
        
    raise HTTPException(status_code=404, detail="No activities found")

@app.get("/api/activities/{activity_id}", response_model=None)
def get_activity(activity_id: int, include_all_efforts: bool = False) -> DetailedActivity | None:
    if not strava_manager:
        raise HTTPException(status_code=500, detail="Strava API not initialized")
    
    activity = strava_manager.get_activity(activity_id, include_all_efforts=include_all_efforts)

    if activity:
        return JSONResponse(content=json.loads(activity.json()))
    
    raise HTTPException(status_code=404, detail=f"Activity with ID {activity_id} not found")

# ==========================================
# GEMINI EXPOSED API ENDPOINTS
# ==========================================

@app.post("/api/chat/athlete-intelligence")
async def generate_athlete_intelligence(request: ChatRequest):
    # Initialize the manager in the special mode
    ai_manager = OpenAIManager(
        athlete_intelligence=True
    )
    
    # The 'user_text' is ignored in this mode, so we can pass anything
    response = await ai_manager.send_message(
        user_text="", 
        context={"this_activity_id": request.this_activity_id}
    )

    ai_manager.client.close()
    
    return {"response": response}

@app.post("/api/chat")
async def chat_with_coach(request: ChatRequest, db: Session = Depends(db_client.get_db)):
    print(f"Received chat request with message: {request.message} and activity ID: {request.this_activity_id}")

    try:
        history_data = await get_chat_history_from_db(db=db, table=DBChatMessage)
        
        recent_history = history_data["history"][-10:] if len(history_data["history"]) > 10 else history_data["history"]

        await add_chat_message_to_history(role="user", content=request.message, db=db, table=DBChatMessage, associated_activity_id=request.this_activity_id)
        # await add_chat_message_to_history(role="user", content=request.message, db=db, table=PersistDBChatMessage)
        response: str = await openai_manager.send_message(user_text=request.message, context={"this_activity_id": request.this_activity_id}, chat_history=recent_history)
        await add_chat_message_to_history(role="assistant", content=response, db=db, table=DBChatMessage, associated_activity_id=request.this_activity_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content={"response": response})
    
@app.post("/api/chat/isolated")
async def isolated_chat_with_coach(request: ChatRequest):
    """Use this endpoint to fetch a quick summary of an activity with no additional context or history"""
    try:
        isolatedManager = OpenAIManager()

        # Start a chat session. (Note: in a production app, you'd want to store history!)
        chat = isolatedManager.model.start_chat(enable_automatic_function_calling=True)
        
        full_prompt = request.message
        
        # Send the message. enable_automatic_function_calling means Gemini will execute 
        # get_activity_summary on its own if it needs to, and then generate a final response!
        response = chat.send_message(full_prompt)
        
        return {"response": response.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/api/dashboard/generate")
async def generate_dashboard(activity_id: int):
    # -- Basic Activity Request
    db = next(db_client.get_db())
    activity_summary = db.query(DBActivity).filter(DBActivity.id == activity_id).first()
    activity_detail = db.query(DBActivityDetail).filter(DBActivity.id == activity_id).first()
    db.close()
    if not activity_summary:
        raise HTTPException(status_code=404, detail="Activity not found")
    if not activity_detail:
        print(f"Warning: detail for activity {activity_id} not found. Syncing...")
        await periodic_detailed_strava_sync()
        activity_detail = db.query(DBActivityDetail).filter(DBActivityDetail.id == activity_id).first()
        if not activity_detail:
            raise HTTPException(status_code=404, detail="Activity Detail not found")
    
    try:
        planner_system_prompt = (
            "You are an expert running coach. "
            "Look at the basic activity summary and recommend a MAX of 4 specific charts that would provide the best analytical value. "
            "Think about highlighting good/bad things or comparing effort to past activities"
        )
        planner_user_prompt = (
            f"Title: {activity_summary.name}\nActivity type: {activity_summary.type}\n"
            f"Workout type: {activity_summary.workout_type}\n"
        )

        plan_response = await openai_manager.generate_dashboard_plan(planner_system_prompt, planner_user_prompt)

        #
        #   TODO: DO SOMETHING TO THE DASHBOARD PLAN
        #

        executor_system = (
            "You are an expert sports data analyst and Apache ECharts developer. "
            "Your job is to take the Coach's requested charts and the raw activity data, "
            "and generate the exact JSON structure required to render those charts in ECharts.\n\n"
            "CRITICAL RULES:\n"
            "1. Only use the data provided in the prompt. DO NOT invent or hallucinate data points.\n"
            "2. For an xAxis with an array of string dates/labels, you MUST set the type to 'category'."
        )

        executor_user = (
            f"COACH'S PLAN:\n{plan_response.json()}\n\n"
            f"CURRENT ACTIVITY ID: {activity_id}\n\n"
            "Use your tools to fetch the necessary data for this plan. Once you have enough data, construct the dashboard."
        )

        executor_response = await openai_manager.execute_dashboard_with_plan(executor_system, executor_user, 5)
        print(plan_response.coach_insight)
        # executor_response.summary_text = plan_response.coach_insight

        return executor_response
   
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dashboard/generate")
async def generate_dashboard():
    pass


    
# ==========================================
# DB EXPOSED API ENDPOINTS
# ==========================================

@app.delete("/api/chat/history")
async def clear_chat_history(db: Session = Depends(db_client.get_db)):
    try:
        # Delete all records in the chat_history table
        db.query(DBChatMessage).delete()    
        db.commit()
        return {"status": "success", "message": "Chat history cleared."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/chat/history")
async def get_chat_history(db: Session = Depends(db_client.get_db)):
    try:
        return await get_chat_history_from_db(db=db, table=DBChatMessage)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
async def get_chat_history_from_db(db: Session = Depends(db_client.get_db), table: DBChatMessage | PersistDBChatMessage = DBChatMessage):
    # Fetch all messages, ordered by timestamp
    print(f"Fetching chat history from table {table.__tablename__}...")
    messages = db.query(table).order_by(table.timestamp.asc()).all()
    
    # Format them into a simple list of dicts for the frontend
    history = [
        {"role": msg.role, "content": msg.content} 
        for msg in messages
    ]
    return {"history": history}

async def add_chat_message_to_history(role: str, content: str, db: Session, table: DBChatMessage | PersistDBChatMessage = DBChatMessage, associated_activity_id: int = None):
    print(f"Adding message to {table.__tablename__} with role '{role}' and content: {content}")
    try:
        new_message = table(role=role, content=content, associated_activity_id=associated_activity_id)
        db.add(new_message)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to add message to history: {e}")

async def periodic_strava_sync():
    while(True):
        await asyncio.sleep(600)
        print("Running periodic Strava sync...")
        if strava_manager and db_client:
            db = next(db_client.get_db())
            try:
                sync_strava_to_db(db=db, strava_manager=strava_manager)
            except Exception as e:
                print(f"Periodic sync failed: {e}")
            finally:
                db.close()

async def periodic_detailed_strava_sync():
    while(True):
        await asyncio.sleep(3600)
        print("Running periodic Strava sync...")
        if strava_manager and db_client:
            db = next(db_client.get_db())
            try:
                sync_detailed_activities(db=db, strava_manager=strava_manager, limit=20)
            except Exception as e:
                print(f"Periodic sync failed: {e}")
            finally:
                db.close()

async def run_initial_syncs():
    """Runs the initial database syncs in the background without blocking the server."""
    print("Triggering automatic background Strava sync...")
    db = next(db_client.get_db())
    try:
        # asyncio.to_thread runs your synchronous function in a separate thread
        # so it physically cannot freeze the main FastAPI event loop!
        await asyncio.to_thread(sync_strava_to_db, db, strava_manager)
        
        await sync_detailed_activities(db=db, strava_manager=strava_manager, limit=50)
        print("Initial syncs complete")
        
    except Exception as e:
        print(f"Initial sync gracefully aborted (Rate Limit or Error): {e}")
    finally:
        db.close()