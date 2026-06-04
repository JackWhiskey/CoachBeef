from datetime import datetime
from enum import Enum
import json

from requests import Session

from db_model import DBActivity, DBActivityDetail
from strava_client import StravaManager


async def sync_detailed_activities(db: Session, strava_manager: StravaManager, limit: int = 50):
    """
    Finds activities missing detailed data, fetches them from Strava, and caches them.
    We cap it with a default 'limit' to prevent hitting Strava rate limits all at once.
    """
    # 1. Find basic activities that DO NOT have cached details yet
    missing_details = (
        db.query(DBActivity)
        .outerjoin(DBActivityDetail)
        .filter(DBActivityDetail.id == None)
        .order_by(DBActivity.start_date.desc())
        .limit(limit)
        .all()
    )

    if not missing_details:
        print("All activities are fully detailed and cached")
        return 0

    print(f"🔄 Syncing details for {len(missing_details)} activities...")
    synced_count = 0
    consecutive_errors = 0
    MAX_ERRORS = 3

    for basic_activity in missing_details:
        try:
            detailed_act = strava_manager.get_activity(basic_activity.id)
            laps_json = []
            if detailed_act.laps:
                for lap in detailed_act.laps:
                    laps_json.append({
                        "lap_index": lap.lap_index,
                        "name": lap.name,
                        "distance": float(lap.distance) if lap.distance else 0.0,
                        "moving_time": get_seconds(lap.moving_time),
                        "average_speed": float(lap.average_speed) if lap.average_speed else None,
                        "average_heartrate": float(lap.average_heartrate) if lap.average_heartrate else None,
                        "max_heartrate": float(lap.max_heartrate) if lap.max_heartrate else None,
                    })

            splits_json = []
            if detailed_act.splits_metric:
                for split in detailed_act.splits_metric:
                    splits_json.append({
                        "split": split.split,
                        "distance": float(split.distance) if split.distance else 0.0,
                        "elapsed_time": get_seconds(split.elapsed_time),
                        "moving_time": get_seconds(split.moving_time),
                        "average_speed": float(split.average_speed) if split.average_speed else None,
                        "average_heartrate": float(split.average_heartrate) if split.average_heartrate else None,
                    })

            streams_json = []
            try:
                # Ask Strava for the time, heartrate, and speed arrays
                raw_streams = strava_manager.client.get_activity_streams(
                    basic_activity.id, types=['time', 'heartrate', 'velocity_smooth']
                )
                
                if raw_streams:
                    time_arr = raw_streams.get('time').data if 'time' in raw_streams else []
                    hr_arr = raw_streams.get('heartrate').data if 'heartrate' in raw_streams else []
                    vel_arr = raw_streams.get('velocity_smooth').data if 'velocity_smooth' in raw_streams else []
                    
                    # DOWNSAMPLE: Only grab 1 data point every 60 seconds
                    for i in range(0, len(time_arr), 60):
                        speed_ms = vel_arr[i] if i < len(vel_arr) else 0
                        pace_decimal = round((1609.34 / speed_ms) / 60, 2) if speed_ms > 0 else 0
                        
                        streams_json.append({
                            "time_mins": round(time_arr[i] / 60, 1),
                            "hr": hr_arr[i] if i < len(hr_arr) else None,
                            "pace_min_mile": pace_decimal
                        })
            except Exception as stream_err:
                print(f"⚠️ Could not fetch streams for {basic_activity.id}: {stream_err}")

            db_detail = DBActivityDetail(
                id=basic_activity.id,
                laps=laps_json,
                splits=splits_json,
                streams=streams_json,  
                updated_at=datetime.utcnow()
            )
            db.add(db_detail)
            consecutive_errors = 0
            synced_count += 1
            print(f"Synced details for activity {basic_activity.id}")

            db.commit()

        except Exception as e:
            db.rollback()
            print(f"Failed to sync details for activity {basic_activity.id}: {e}")
            
            consecutive_errors += 1
            if consecutive_errors >= MAX_ERRORS:
                print(f"CRITICAL: Hit {MAX_ERRORS} consecutive errors. Aborting detailed sync")
                break
            
    return synced_count


def sync_strava_to_db(db: Session, strava_manager: StravaManager):
    print("Starting Strava Sync...")
    
    latest_activity = db.query(DBActivity).order_by(DBActivity.start_date.desc()).first()
    
    after_date = None
    if latest_activity and latest_activity.start_date:
        try:
            after_date = datetime.strptime(latest_activity.start_date, "%Y-%m-%dT%H:%M:%SZ")
            print(f"Last activity found on: {after_date}. Fetching only newer activities...")
        except Exception as e:
            print(f"Error parsing date {latest_activity.start_date}: {e}. Defaulting to full sync.")

    raw_activities = strava_manager.get_activities(before=None,after=after_date, limit=200)

    synced_count = 0
    for act in raw_activities:
        act_dict = json.loads(act.json())
        
        polyline = ""
        if act_dict.get("map") and act_dict["map"].get("summary_polyline"):
            polyline = act_dict["map"]["summary_polyline"]

        workout_type = WorkoutType.from_strava_int(act_dict.get("workout_type", 0))

        db_act = DBActivity(
            id=act_dict["id"],
            name=act_dict.get("name", "Unknown Activity"),
            type=act_dict.get("type", "Workout"),
            start_date=act_dict.get("start_date", ""),
            distance=act_dict.get("distance", 0.0),
            moving_time=act_dict.get("moving_time", 0),
            average_speed=act_dict.get("average_speed", 0.0),
            summary_polyline=polyline,
            workout_type=workout_type,
            workout_type_num=act_dict.get("workout_type", 0)
        )
        
        db.merge(db_act)
        synced_count += 1
        try:
            db.commit()
        except:
            db.rollback()
            print(f"Database error during sync: {e}")
            raise e

    print(f"Sync complete! Inserted/Updated {synced_count} activities.")
        
    return synced_count


def get_seconds(time_val):
    """Safely extracts seconds from Stravalib's various custom time/duration objects."""
    if time_val is None:
        return 0.0
    if hasattr(time_val, "total_seconds"):
        return time_val.total_seconds()
    if hasattr(time_val, "magnitude"):
        return float(time_val.magnitude)
    try:
        return float(time_val)
    except (ValueError, TypeError):
        pass
    if hasattr(time_val, "seconds"):
        return float(getattr(time_val, "days", 0) * 86400 + time_val.seconds)
    return 0.0

class WorkoutType(str, Enum):
    # Strava's integer mappings for Runs (adjust if you also track cycling!)
    RUN_STD = "Run - Standard"  # 0
    RUN_RACE = "Run - Race"                   # 1
    LONG_RUN = "Run - Long Run"           # 2
    RUN_WORKOUT = "Run - Workout"       # 3

    RIDE_STD = "Ride - Standard"
    RIDE_RACE = "Ride - Race"
    RIDE_WORKOUT = "Ride - Workout"

    UNKNOWN = "Unknown"             # Fallback

    @classmethod
    def from_strava_int(cls, strava_int: int):
        """Safely maps the Strava integer to our readable string."""
        mapping = {
            0: cls.RUN_STD,
            1: cls.RUN_RACE,
            2: cls.LONG_RUN,
            3: cls.RUN_WORKOUT,
            10: cls.RIDE_STD,
            11: cls.RIDE_RACE,
            12: cls.RIDE_WORKOUT
        }
        # Return the matched enum, or UNKNOWN if it's a weird number
        return mapping.get(strava_int, cls.UNKNOWN)