import os
import time

import json

import pandas as pd
from db_model import DBActivity
import stravalib

from stravalib.strava_model import ActivityZone, DetailedActivity, DetailedAthlete, Literal, SummaryActivity, Zones

from config import Config
from stravalib.client import BatchedResultsIterator, Client, Session, datetime


class StravaManager:
    def __init__(self):
        """Initializes the Strava API client using the access token from our settings."""

        print("Initializing StravaManager with Config settings.")

        if not Config.STRAVA_ACCESS_TOKEN:
            raise ValueError(
                "Strava access token is missing. Please set STRAVA_ACCESS_TOKEN in your Config."
            )

        self.client = Client()
        self.token_file = os.path.join(os.path.dirname(__file__), "tokens.json")

        self._authenticate()

    def _authenticate(self):
        """Handles the OAuth2 token refresh cycle seamlessly."""
        tokens = self._load_tokens()

        if not tokens or time.time() > tokens.get("expires_at", 0) - 300:
            print("Access token expired or missing. Refreshing...")

            current_refresh_token = (
                tokens.get("refresh_token") if tokens else Config.STRAVA_REFRESH_TOKEN
            )

            new_tokens = self.client.refresh_access_token(
                client_id=Config.STRAVA_CLIENT_ID,
                client_secret=Config.STRAVA_CLIENT_SECRET,
                refresh_token=current_refresh_token,
            )

            self._save_tokens(new_tokens)
            tokens = new_tokens
        else:
            print("Using existing valid access token.")

        self.client.access_token = tokens["access_token"]
        self.client.refresh_token = tokens['refresh_token']
        self.client.token_expires = tokens['expires_at']

    def _load_tokens(self):
        """Reads the cached tokens from a local file."""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(
                    "Error decoding tokens.json. It may be corrupted. Deleting the file."
                )
                os.remove(self.token_file)
                return None
        return None

    def _save_tokens(self, tokens):
        """Saves the refreshed tokens to a local file."""
        with open(self.token_file, "w") as f:
            json.dump(tokens, f)


    def get_athlete(self) -> DetailedAthlete | None:
        """Fetches the athlete's profile information from Strava."""
        try:
            return self.client.get_athlete()
        except Exception as e:
            print(f"Error fetching athlete profile: {e}")
            return None

    def get_athlete_zones(self):
        """Fetches the athlete's heart rate and power zones."""
        try:
            zones : Zones = self.client.get_athlete_zones()
            return {
                "heart_rate": zones.heart_rate if zones.heart_rate else [],
                "power": zones.power if zones.power else [],
            }
        except Exception as e:
            print(f"Error fetching athlete zones: {e}")
            return {"heart_rate": [], "power": []}

    def get_activities(self, before: datetime | str, after: datetime | str, limit):
        """Fetches activities within a custom timeframe."""
        try:
            activities: BatchedResultsIterator[SummaryActivity] = (
                self.client.get_activities(before=before, after=after, limit=limit)
            )
            return activities
        except Exception as e:
            print(f"Error fetching activities for custom timeframe: {e}")
            return None

    def get_activity(self, activity_id, include_all_efforts=False) -> DetailedActivity:
        """Fetches detailed information for a specific activity."""
        try:
            return self.client.get_activity(activity_id, include_all_efforts=include_all_efforts)
        except Exception as e:
            print(f"Error fetching activity {activity_id}: {e}")
            return None

    def get_activity_zones(self, activity_id) -> list[ActivityZone]:
        """Fetches the heart rate and power zones for a specific activity."""
        try:
            return self.client.get_activity_zones(activity_id)
        except Exception as e:
            print(f"Error fetching zones for activity {activity_id}: {e}")
            return None

    def get_activity_comments(
            self, 
            activity_id, 
            markdown: bool = False, 
            limit: int | None = None
        ) -> BatchedResultsIterator[stravalib.model.Comment]:
        """Fetches comments for a specific activity."""
        try:
            return self.client.get_activity_comments(activity_id, markdown=markdown, limit=limit)
        except Exception as e:
            print(f"Error fetching comments for activity {activity_id}: {e}")
            return None
        
    def get_activity_kudos(
        self, 
        activity_id: int, 
        limit: int | None = None
    ) -> BatchedResultsIterator[stravalib.model.SummaryAthlete]:
        """Fetches kudos for a specific activity."""
        try:
            return self.client.get_activity_kudos(activity_id, limit=limit)
        except Exception as e:
            print(f"Error fetching kudos for activity {activity_id}: {e}")
            return None
        
    def get_activity_streams(
        self, 
        activity_id: int, 
        types: list[str] | None = None,
        resolution: Literal["low", "medium", "high"] | None = None,
        series_type: Literal["distance", "time"] | None = None
    ) -> dict[str, stravalib.model.Stream]:
        """Fetches data streams (like GPS, heart rate, power) for a specific activity."""
        try:
            return self.client.get_activity_streams(
                activity_id, types=types, resolution=resolution, series_type=series_type
            )
        except Exception as e:
            print(f"Error fetching streams for activity {activity_id}: {e}")
            return None

    def get_activity_photos(
        self,
        activity_id: int,
        size: int | None = None,
        only_instagram: bool = False,
    ) -> BatchedResultsIterator[stravalib.model.ActivityPhoto]:
        """Fetches photos for a specific activity."""
        try:
            return self.client.get_activity_photos(
                activity_id, size=size, only_instagram=only_instagram
            )
        except Exception as e:
            print(f"Error fetching photos for activity {activity_id}: {e}")
            return None

    def get_recent_activities(self, limit=5):
        """Fetches the most recent activities for the athlete."""
        return self.get_activities(before=None, after=None, limit=limit)
    
    def get_most_recent_activity(self):
        """Fetches the most recent activity for the athlete."""
        activities = self.get_recent_activities(limit=1)
        return next(activities, None) if activities else None

    def convert_activities_to_dataframe(self, activities: list[SummaryActivity]):
        """Fetches activities and returns a cleaned Pandas DataFrame."""
        try:
            data = []
            for act in activities:
                data.append(
                    {
                        "id": act.id,
                        "name": act.name,
                        "type": act.type.root,
                        # Convert to datetime and extract just the date
                        "date": pd.to_datetime(act.start_date_local).date(),
                        # Convert meters to kilometers
                        "distance_km": round(act.distance / 1000, 2),
                        # Convert seconds to minutes
                        "moving_time_min": round(act.moving_time / 60, 2),
                        "elevation_gain_m": act.total_elevation_gain,
                    }
                )

            df = pd.DataFrame(data)

            # Ensure the date column is a proper datetime object for time-series graphing
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])

            return df

        except Exception as e:
            print(f"Error converting to dataframe: {e}")
            return pd.DataFrame()  # Return empty DataFrame on failure

    def get_athlete_profile_dict(self):
        """Fetches the athlete's profile information from Strava."""
        try:
            athlete: DetailedAthlete = self.client.get_athlete()
            return {
                "id": athlete.id,
                "name": f"{athlete.firstname} {athlete.lastname}",
                "username": athlete.username,
                "profile_png": athlete.profile,
                "city": athlete.city,
                "state": athlete.state,
                "country": athlete.country,
            }
        except Exception as e:
            print(f"Error fetching athlete profile: {e}")
            return None