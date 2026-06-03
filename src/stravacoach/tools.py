import json
# Make sure you are importing the instantiated client instance!
# If your main file creates `db_client = DBClient()`, import that instance here.
from db_client import DBClient
from db_model import DBActivity, DBChatMessage

local_db_client = DBClient()

def get_activity_list_over_time(before_date: str, after_date: str = None, type: str = None) -> str:
    """Tool: Fetches activity summaries from the local database."""
    print(f"🛠️ Coach Beef is using the tool: get_activity_summary_over_time(before_date={before_date}, after_date={after_date})")
    db = next(local_db_client.get_db())
    try:
        query = db.query(DBActivity).filter(DBActivity.start_date < before_date)
        if after_date:
            query = query.filter(DBActivity.start_date > after_date)
        if type:
            query = query.filter(DBActivity.type == type)
        
        activities = query.order_by(DBActivity.start_date.desc()).all()
        
        return json.dumps([
            {
                "id": activity.id,
                "name": activity.name,
                "type": activity.type,
                "start_date": activity.start_date,
                "distance": activity.distance,
                "moving_time": activity.moving_time,
                "average_speed": activity.average_speed,
                # Use .get() or getattr() if these might be missing/nullable in SQLite
                "calories": getattr(activity, "calories", 0),
                "average_heartrate": getattr(activity, "average_heartrate", None)
            }
            for activity in activities
        ])
    except Exception as e:
        print(f"❌ Error in get_activity_list_over_time: {e}")
        return json.dumps({"error": str(e)})
    finally:        
        db.close()

def get_summary_stats_over_time(before_date: str, after_date: str = None, type: str = None) -> str:
    """Tool: Fetches summary stats (total distance, total moving time, average speed) from the local database."""
    print(f"🛠️ Coach Beef is using the tool: get_summary_stats_over_time(before_date={before_date}, after_date={after_date})")
    db = next(local_db_client.get_db())
    try:
        query = db.query(DBActivity).filter(DBActivity.start_date < before_date)
        if after_date:
            query = query.filter(DBActivity.start_date > after_date)
        if type:
            query = query.filter(DBActivity.type == type)
        
        activities = query.all()
        
        total_distance = sum(activity.distance for activity in activities if activity.distance)
        total_moving_time = sum(activity.moving_time for activity in activities if activity.moving_time)
        average_speed = total_distance / total_moving_time if total_moving_time > 0 else 0
        
        return json.dumps({
            "total_distance": total_distance,
            "total_moving_time": total_moving_time,
            "average_speed": average_speed
        })
    except Exception as e:
        print(f"❌ Error in get_summary_stats_over_time: {e}")
        return json.dumps({"error": str(e)})
    finally:
        db.close()

def get_activity_from_db(activity_id: int) -> str:
    """Tool: Fetches a specific activity from the local database."""
    print(f"🛠️ Coach Beef is using the tool: get_activity_from_db({activity_id})")
    
    db = next(local_db_client.get_db())
    try:
        activity = db.query(DBActivity).filter(DBActivity.id == activity_id).one_or_none()
        
        if not activity:
            return json.dumps({"error": f"Activity with ID {activity_id} not found."})
            
        return json.dumps({
            "id": activity.id,
            "name": activity.name,
            "type": activity.type,
            "start_date": activity.start_date,
            "distance": activity.distance,
            "moving_time": activity.moving_time,
            "average_speed": activity.average_speed,
            "calories": getattr(activity, "calories", 0),
            "average_heartrate": getattr(activity, "average_heartrate", None)
        })
    except Exception as e:
        print(f"❌ Error in get_activity_from_db: {e}")
        return json.dumps({"error": str(e)})
    finally:
        db.close()

def search_past_advice(limit: int = 5) -> str:
    """Tool: Fetches older chat history from the database."""
    print(f"🛠️ Coach Beef is using the tool: search_past_advice(limit={limit})")
    
    db = next(local_db_client.get_db())
    try:
        messages = db.query(DBChatMessage).order_by(DBChatMessage.timestamp.desc()).limit(limit).all()
        
        # ✅ Added fallback logic for associated_activity_id in case it's missing or null
        history = [
            {
                "role": msg.role, 
                "content": msg.content, 
                "associated_activity_id": getattr(msg, "associated_activity_id", None)
            } 
            for msg in reversed(messages)
        ]
        return json.dumps(history)
    except Exception as e:
        print(f"❌ Error in search_past_advice: {e}")
        return json.dumps({"error": str(e)})
    finally:
        db.close()