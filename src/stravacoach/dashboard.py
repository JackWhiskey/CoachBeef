import streamlit as st
from strava_client import StravaManager
from datetime import datetime, time
import plotly.express as px

# Set up the page layout (This must be the very first Streamlit command)
st.set_page_config(page_title="StravaCoach", page_icon="🏃", layout="wide")


# Initialize your backend client and cache it
@st.cache_resource
def get_strava_manager():
    return StravaManager()


manager = get_strava_manager()

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("🏃‍♂️ StravaCoach")
st.sidebar.write("Your Personal Training Hub")
st.sidebar.divider()

# Create the radio button menu in the sidebar
page = st.sidebar.radio(
    "Navigation", ["Activities", "Feed", "Map", "Profile", "Settings"]
)

# ==========================================
# MAIN PAGE ROUTING
# ==========================================

if page == "Activities":
    st.title("Activity Analytics")

    start_date = st.date_input("Start Date", value=None)
    end_date = st.date_input("End Date", value=None)
    limit = st.slider(
        "Max Activities to Fetch", min_value=10, max_value=500, value=100, step=10
    )

    start_dt = datetime.combine(start_date, time.min) if start_date else None
    end_dt = datetime.combine(end_date, time.max) if end_date else None

    with st.spinner("Pulling and crunching data..."):
        if start_dt or end_dt or limit:
            activities = manager.get_activities(end_dt, start_dt, limit)
        else:
            activities = manager.get_recent_activities(limit)

        df = manager.convert_activities_to_dataframe(activities)

    if not df.empty:
        # --- AGGREGATION ---
        st.subheader("High-Level Stats")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Activities", len(df))
        col2.metric("Total Distance (km)", round(df["distance_km"].sum(), 1))
        col3.metric("Total Elevation (m)", round(df["elevation_gain_m"].sum(), 1))

        st.divider()

        # --- GRAPH 1: Distance Over Time ---
        st.subheader("Training Volume Over Time")
        # Group by date in case there are multiple activities in one day
        daily_volume = df.groupby("date")["distance_km"].sum().reset_index()

        fig_time = px.bar(
            daily_volume,
            x="date",
            y="distance_km",
            labels={"distance_km": "Distance (km)", "date": "Date"},
            color_discrete_sequence=["#fc4c02"],  # Strava Orange!
        )
        st.plotly_chart(fig_time, use_container_width=True)

        # --- GRAPH 2: Activity Type Breakdown ---
        st.subheader("Activity Distribution")
        type_counts = df["type"].value_counts().reset_index()
        type_counts.columns = ["type", "count"]

        fig_pie = px.pie(type_counts, names="type", values="count", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

        # --- RAW DATA ---
        with st.expander("View Raw Data Table"):
            st.dataframe(df)

    else:
        st.info("No activity data found to analyze.")

elif page == "Feed":
    st.title("Strava Feed")
    st.write("Scroll through your workouts.")

    start_date = st.date_input("Start Date", value=None)
    end_date = st.date_input("End Date", value=None)
    limit = st.slider(
        "Max Activities to Fetch", min_value=10, max_value=500, value=100, step=10
    )

    start_dt = datetime.combine(start_date, time.min) if start_date else None
    end_dt = datetime.combine(end_date, time.max) if end_date else None

    # Define common sports for the filter (expand this based on what you track)
    common_sports = ["Run", "Ride", "Swim", "Walk", "Hike", "Workout", "WeightTraining"]
    
    # The multiselect returns a list of the strings the user has clicked
    selected_types = st.multiselect(
        "Filter by Activity Type", 
        options=common_sports, 
        default=common_sports, # Defaults to showing everything
        key="feed_type_filter"
    )
            
    with st.spinner("Loading feed..."):
        raw_activities = manager.get_activities(before=end_dt, after=start_dt, limit=limit)
            
        # 2. Pass the list into your refactored processing method
        df = manager.convert_activities_to_dataframe(raw_activities)            
        if not df.empty:

            # Step C: Apply the Streamlit multiselect filter to the DataFrame
            # This only keeps rows where the 'type' column matches one of the selected options
            if selected_types:
                df = df[df['type'].isin(selected_types)]
            else:
                # If the user clears the multiselect entirely, empty the DataFrame
                df = df.iloc[0:0]

            st.success(f"Loaded {len(df)} activities!")
            st.divider()
            
            # Iterate through the DataFrame to build the UI "cards"
            for index, row in df.iterrows():
                
                # Create a container for the activity to keep elements grouped together
                with st.container():
                    # The Title and Subtitle
                    st.subheader(row['name'])
                    
                    # Add an emoji based on the activity type
                    emoji = "🏃" if row['type'] == "Run" else "🚴" if row['type'] == "Ride" else "🏊" if row['type'] == "Swim" else "⏱️"
                    st.caption(f"{emoji} {row['type']} • {row['date']}")
                    
                    # Display core metrics side-by-side
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Distance", f"{row['distance_km']} km")
                    col2.metric("Moving Time", f"{row['moving_time_min']} min")
                    col3.metric("Elevation", f"{row['elevation_gain_m']} m")
                    
                    # Add a visual separator between feed posts
                    st.divider()
        else:
            st.warning("No activities found for this time period.")


elif page == "Map":
    st.title("Activity Map")
    st.write("Visualizations of your recent routes will appear here.")
    st.info("Feature coming soon! (We will need to decode Strava polylines for this).")

elif page == "Profile":
    st.title("Your Profile")
    profile = manager.get_athlete_profile()

    if profile:
        col1, col2 = st.columns(2)
        col1.metric("Athlete Name", profile["name"])
        col2.metric("Location", f"{profile['city']}, {profile['country']}")
    else:
        st.error("Could not load profile data.")

elif page == "Settings":
    st.title("Settings")
    st.write("Manage your application preferences and API connection here.")

    # Example of a setting toggle
    st.toggle("Use Metric System (km)", value=True)
