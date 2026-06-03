from datetime import datetime
import time

from stravalib.strava_model import DetailedActivity, DetailedAthlete, SummaryActivity, Zones, Zones

from strava_client import StravaManager


def main():
    print("Initializing Strava Client")
    m : StravaManager = StravaManager()

    athlete : DetailedAthlete | None = m.get_athlete()
    print(f"Athlete Profile: {athlete.firstname} {athlete.lastname} - {athlete.city}, {athlete.state}, {athlete.country}") if athlete else print("No athlete profile found.")

    zones : Zones = m.get_athlete_zones()
    print(f"Athlete Zones: {zones}")

    most_recent : SummaryActivity | None = m.get_most_recent_activity()
    print(f"Most recent activity (Simple): {most_recent.name} on {most_recent.start_date_local} - {most_recent.moving_time} seconds") if most_recent else print("No recent activities found.")

    # most_rcent_detailed : DetailedActivity | None = m.get_activity(most_recent.id) if most_recent else None
    # print(f"Most recent activity (Detailed): {most_rcent_detailed}")

    total_seconds_of_moving_time = 0

    last_30_days = m.get_activities(before=datetime.fromtimestamp(time.time()), after=datetime.fromtimestamp(time.time() - 30 * 24 * 60 * 60), limit=100)
    print("Fetching activities from the last 30 days:")
    if not last_30_days:
        print("No activities found in the last 30 days.")
        return
    for activity in last_30_days:
        total_seconds_of_moving_time += activity.moving_time

        print(f" - {activity.name} - Time: {activity.moving_time // 3600}:{(activity.moving_time % 3600) // 60}:{activity.moving_time % 60}")

    hours = total_seconds_of_moving_time // 3600
    minutes = (total_seconds_of_moving_time % 3600) // 60
    seconds = total_seconds_of_moving_time % 60

    print(f"Total moving time (last 30 days): {hours} hours {minutes} minutes {seconds} seconds")


if __name__ == "__main__":
    main()
