export interface DetailedActivity extends SummaryActivity {
    best_efforts: DetailedSegmentEffort[] | null
    // The number of kilocalories consumed during this activity
    calories: number | null
    // The description of the activity
    description: string | null
    // The name of the device used to record the activity
    device_name: string | null
    // The token used to embed a Strava activity
    embed_token: string | null
    gear: SummaryGear | null
    laps: Lap[] | null
    photos: PhotosSummary | null
    segment_efforts: DetailedSegmentEffort[] | null
    // The splits of this activity in metric units (for runs)
    splits_metric: Split[] | null
    // The splits of this activity in imperial units (for runs)
    splits_standard: Split[] | null
}

export interface Split {
    // The average speed of this split, in meters per second
    average_speed: number | null
    // The distance of this split, in meters
    distance: number | null
    // The elapsed time of this split, in seconds
    elapsed_time: number | null
    // The elevation difference of this split, in meters
    elevation_difference: number | null
    // The moving time of this split, in seconds
    moving_time: number | null
    // The pacing zone of this split
    pace_zone: number | null
    // N/A
    split: number | null
}

export interface PhotosSummary {
    // The number of photos for this activity
    count: number | null
    // Whether the activity has any photos
    primary: boolean | null
}

export interface Lap {
    activity: MetaActivity | null
    athlete: MetaAthlete | null
    average_cadence: number | null
    // The lap's average cadence
    average_speed: number | null
    // The lap's average speed
    distance: number | null
    // The lap's distance, in meters
    elapsed_time: number | null
    // The lap's elapsed time, in seconds
    end_index: number | null
    // The end index of this effort in its activity's stream
    id: number | null
    // The unique identifier of this lap
    lap_index: number | null
    // The index of this lap in the activity it belongs to
    max_speed: number | null
    //  The maximum speed of this lat, in meters per second
    moving_time: number | null
    // The lap's moving time, in seconds
    name: string | null
    // The name of the lap
    pace_zone: number | null
    // The athlete's pace zone during this lap
    split: number | null
    start_date: Date | null
    // The time at which the lap was started.
    start_date_local: Date | null
    // The time at which the lap was started in the local timezone.
    start_index: number | null
    // The start index of this effort in its activity's stream
    total_elevation_gain: number | null
    // The elevation gain of this lap, in meters
    }

export interface SummaryGear {
    // The distance logged with this gear.
    distance: number | null
    // The gear's unique identifier.
    id: string | null
    // The gear's name.
    name: string | null
    //Whether this gear's is the owner's default one.
    primary: boolean | null
    //Resource state, indicates level of detail. Possible values: 2 -> "summary", 3 -> "detail"
    resource_state: number | null
}

export interface DetailedSegmentEffort {
    activity: MetaActivity | null
    athlete: MetaAthlete | null
    // The effort's average cadence
    average_cadence: number | null
    // The heart heart rate of the athlete during this effort
    average_heartrate: number | null
    // The average wattage of this effort
    average_watts: number | null
    // For riding efforts, whether the wattage was reported by a dedicated recording device
    device_watts: boolean | null
    // The end index of this effort in its activity's stream
    end_index: number | null
    // Whether this effort should be hidden when viewed within an activity
    hidden: boolean | null
    // The rank of the effort on the global leaderboard if it belongs in the top 10 at the time of upload
    kom_rank: number | null
    // The maximum heart rate of the athlete during this effort
    max_heartrate: number | null
    // The effort's moving time
    moving_time: number | null
    // The name of the segment on which this effort was performed
    name: string | null
    // The rank of the effort on the athlete's leaderboard if it belongs in the top 3 at the time of upload
    pr_rank: number | null
    segment: SummarySegment | null
    // The start index of this effort in its activity's stream
    start_index: number | null
}

export interface MetaActivity {
    id: number | null,
}

export interface SummarySegment {
    
}

export interface SummaryActivity extends MetaActivity {
    // The number of achievements gained during this activity
    achievement_count: number | null,
    // Athlete entity who performed the activity
    athlete: MetaAthlete | null,
    // The number of athletes for taking part in a group activity
    athlete_count: number | null,
    // The activity's average speed, in meters per second
    average_speed: number | null,
    // Average power output in watts during this activity. Rides only
    average_watts: number | null,
    // The number of comments for this activity
    comment_count: number | null,
    // Whether this activity is a commute
    commute: boolean | null,
    // Whether the watts are from a power meter, false if estimated
    device_watts: boolean | null,
    // The activity's distance, in meters
    distance: number | null,
    // The activity's elapsed time, in seconds
    elapsed_time: number | null,
    // The activity's highest elevation, in meters
    elev_high: number | null,
    // The activity's lowest elevation, in meters
    elev_low: number | null,    
    end_latlng: LatLng | null,
    // The identifier provided at upload time
    external_id: string | null,
    // Whether this activity is flagged
    flagged: boolean | null,
    // The id of the gear for the activity
    gear_id: string | null,
    // Whether the logged-in athlete has kudoed this activity
    has_kudoed: boolean | null,
    // Whether the activity is muted
    hide_from_home: boolean | null,
    // The total work done in kilojoules during this activity. Rides only
    kilojoules: number | null,
    // The number of kudos given for this activity
    kudos_count: number | null,
    // Whether this activity was created manually
    manual: boolean | null,
    map: PolylineMap | null,
    // The activity's max speed, in meters per second
    max_speed: number | null,
    // Rides with power meter data only
    max_watts: number | null,
    // The activity's moving time, in seconds
    moving_time: number | null,
    // The name of the activity
    name: string | null,
    // The number of Instagram photos for this activity
    photo_count: number | null,
    // Whether this activity is private
    private: boolean | null,
    sport_type: SportType | null,
    // The time at which the activity was started.
    start_date: Date | null,
    // The time at which the activity was started in the local timezone.
    start_date_local: Date | null,
    start_latlng: LatLng | null,
    // The timezone of the activity
    timezone: string | null,
    // The activity's total elevation gain.
    total_elevation_gain: number | null,
    // The number of Instagram and Strava photos for this activity
    total_photo_count: number | null,
    // Whether this activity was recorded on a training machine
    trainer: boolean | null,
    // Deprecated. Prefer to use sport_type
    type: ActivityType | null,
    // The identifier of the upload that resulted in this activity
    upload_id: number | null,
    // The unique identifier of the upload in string format
    upload_id_str: string | null,
    // Similar to Normalized Power. Rides with power meter data only
    weighted_average_watts: number | null,
    // The activity's workout type
    workout_type: string | null
}

export interface MetaAthlete {
    id: number | null,
}

export interface PolylineMap {
    // The identifier of the map
    id: string | null,
    // The polyline of the map, only returned on detailed representation of an object
    polyline: string | null,
    // The summary polyline of the map
    summary_polyline: string | null
}

export interface LatLng {
    // A pair of latitude/longitude coordinates, represented as an array of 2 floating point numbers.
    root: number[] | null,
}

enum ActivityType {
    "AlpineSki",
    "BackcountrySki",
    "Canoeing",
    "Crossfit",
    "EBikeRide",
    "Elliptical",
    "Golf",
    "Handcycle",
    "Hike",
    "IceSkate",
    "InlineSkate",
    "Kayaking",
    "Kitesurf",
    "NordicSki",
    "Ride",
    "RockClimbing",
    "RollerSki",
    "Rowing",
    "Run",
    "Sail",
    "Skateboard",
    "Snowboard",
    "Snowshoe",
    "Soccer",
    "StairStepper",
    "StandUpPaddling",
    "Surfing",
    "Swim",
    "Velomobile",
    "VirtualRide",
    "VirtualRun",
    "Walk",
    "WeightTraining",
    "Wheelchair",
    "Windsurf",
    "Workout",
    "Yoga"
}

enum SportType {
    "AlpineSki",
    "BackcountrySki",
    "Badminton",
    "Canoeing",
    "Crossfit",
    "EBikeRide",
    "Elliptical",
    "EMountainBikeRide",
    "Golf",
    "GravelRide",
    "Handcycle",
    "HighIntensityIntervalTraining",
    "Hike",
    "IceSkate",
    "InlineSkate",
    "Kayaking",
    "Kitesurf",
    "MountainBikeRide",
    "NordicSki",
    "Pickleball",
    "Pilates",
    "Racquetball",
    "Ride",
    "RockClimbing",
    "RollerSki",
    "Rowing",
    "Run",
    "Sail",
    "Skateboard",
    "Snowboard",
    "Snowshoe",
    "Soccer",
    "Squash",
    "StairStepper",
    "StandUpPaddling",
    "Surfing",
    "Swim",
    "TableTennis",
    "Tennis",
    "TrailRun",
    "Velomobile",
    "VirtualRide",
    "VirtualRow",
    "VirtualRun",
    "Walk",
    "WeightTraining",
    "Wheelchair",
    "Windsurf",
    "Workout",
    "Yoga"
}

export interface ChartTitle {
    text: string;
}

export interface ChartAxis {
    type: string;
    data: string[];
}

export interface ChartSeries {
    name: string;
    type: string;
    data: number[];
}

export interface EChartOption {
    title: ChartTitle;
    xAxis: ChartAxis;
    yAxis: ChartAxis;
    series: ChartSeries[];
}

export interface DashboardData {
    summary_text: string;
    charts: EChartOption[];
}

export interface DashboardPanelProps {
    selectedActivityId: number | null;
}