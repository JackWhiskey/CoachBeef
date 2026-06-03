from contextlib import asynccontextmanager
import json
import asyncio

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from stravalib.model import DetailedAthlete
from requests import Session
from openai_client import OpenAIManager, ChatRequest
from db_client import DBClient
from stravalib.strava_model import DetailedActivity, SummaryActivity, Zones
from datetime import datetime
from strava_client import StravaManager
from db_model import DBActivity, DBChatMessage, PersistDBChatMessage

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server is spinning up...")
    if strava_manager and db_client:
        print("Triggering automatic Strava sync...")
        # Manually extract a database session from the generator
        db = next(db_client.get_db())
        try:
            # Assumes you defined sync_strava_to_db in this file or imported it
            sync_strava_to_db(db=db)
        except Exception as e:
            print(f"Startup sync failed: {e}")
        finally:
            db.close()

    background_sync = asyncio.create_task(periodic_strava_sync())
    
    yield # This yields control back to FastAPI so it can start accepting requests!
    
    # --- SHUTDOWN ---
    print("Server shutting down...")
    background_sync.cancel()

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
                map={"summary_polyline": act.summary_polyline} 
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
                sync_strava_to_db(db=db)
            except Exception as e:
                print(f"Periodic sync failed: {e}")
            finally:
                db.close()

def sync_strava_to_db(db: Session):
    print("Starting Strava Sync...")
    
    # 1. Find the most recent activity in the database
    latest_activity = db.query(DBActivity).order_by(DBActivity.start_date.desc()).first()
    
    after_date = None
    if latest_activity and latest_activity.start_date:
        try:
            # Convert the stored ISO string back to a datetime object for the Strava client
            after_date = datetime.strptime(latest_activity.start_date, "%Y-%m-%dT%H:%M:%SZ")
            print(f"Last activity found on: {after_date}. Fetching only newer activities...")
        except Exception as e:
            print(f"Error parsing date {latest_activity.start_date}: {e}. Defaulting to full sync.")

    # 2. Fetch from Strava (Pass 'after' to only get new stuff)
    # If after_date is None, this safely fetches your most recent activities up to the limit
    raw_activities = strava_manager.get_activities(before=None,after=after_date, limit=200)

    # 3. Upsert into the Database
    synced_count = 0
    for act in raw_activities:
        act_dict = json.loads(act.json())
        
        # Safely extract the polyline string (it's nested inside the 'map' object)
        polyline = ""
        if act_dict.get("map") and act_dict["map"].get("summary_polyline"):
            polyline = act_dict["map"]["summary_polyline"]

        # Map the Strava dictionary to your SQLAlchemy Model
        db_act = DBActivity(
            id=act_dict["id"],
            name=act_dict.get("name", "Unknown Activity"),
            type=act_dict.get("type", "Workout"),
            start_date=act_dict.get("start_date", ""),
            distance=act_dict.get("distance", 0.0),
            moving_time=act_dict.get("moving_time", 0),
            average_speed=act_dict.get("average_speed", 0.0),
            summary_polyline=polyline
        )
        
        # db.merge checks the Primary Key (id). Updates if found, inserts if new!
        db.merge(db_act)
        synced_count += 1

    # 4. Commit the transaction
    try:
        db.commit()
        print(f"Sync complete! Inserted/Updated {synced_count} activities.")
    except Exception as e:
        db.rollback()
        print(f"Database error during sync: {e}")
        raise e

    return synced_count