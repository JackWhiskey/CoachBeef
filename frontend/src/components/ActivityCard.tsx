import ActivityMap from "./ActivityMap.tsx";
import { DetailedActivity, SummaryActivity } from "../utils/entities.tsx";
import { formatMovingTime, formatPace } from "../utils/formatters.tsx";
import { useEffect, useState } from "react";

interface ActivityCardProps {
  activity: SummaryActivity;
  isSelected: boolean;
  isDimmed: boolean;
  isMaximized: boolean;
  useImperialDistances: boolean;
  onCardClick: (id: number | null, e: React.MouseEvent<HTMLDivElement>) => void;
  onMapClick: () => void;
}

const showDescription: boolean = true;

export default function ActivityCard({ 
  activity, 
  isSelected, 
  isMaximized, 
  isDimmed,
  useImperialDistances, 
  onCardClick, 
  onMapClick,
}: ActivityCardProps) {
  console.log(`Rendering activity card for: ${activity.name} (ID: ${activity.id})`)

  const [detailedData, setDetailedData] = useState<DetailedActivity | null>(null);
  const [isLoadingDetails, setIsLoadingDetails] = useState<boolean>(false);

  const isMaximizedCard = isSelected && isMaximized;
  const hasDistance = (activity.distance ?? 0) > 0;
  const distanceKm = activity.distance ? (activity.distance / 1000).toFixed(2) : "N/A";
  const distanceMiles = activity.distance ? (activity.distance / 1609.34).toFixed(2) : "N/A";

  const movingTimeString = formatMovingTime(activity.moving_time);
  const formattedPace = formatPace(activity.average_speed, useImperialDistances);

  // 2. Trigger the fetch automatically when the card is selected
    useEffect(() => {
      // Only fetch if it's selected, we don't already have the data, and we aren't currently loading it
      if (isSelected && !detailedData && !isLoadingDetails) {
        const fetchDetails = async () => {
          setIsLoadingDetails(true);
          try {
            const response = await fetch(`http://localhost:8000/api/activities/${activity.id}`);
            if (response.ok) {
              const data: DetailedActivity = await response.json();
              setDetailedData(data);
            } else {
              console.error("Failed to fetch details:", response.statusText);
            }
          } catch (error) {
            console.error("Error fetching detailed activity:", error);
          } finally {
            setIsLoadingDetails(false);
          }
        };

        fetchDetails();
      }
    }, [isSelected, activity.id, detailedData, isLoadingDetails]);

  return (
    <div
      key={activity.id} 
      id={`activity-${activity.id}`}
      className={`activity-card ${isSelected ? 'selected' : ''} ${isDimmed ? 'dimmed' : ''} ${isMaximizedCard ? 'maximized' : ''}`}        
      onClick={(e) => onCardClick(activity.id, e)}
    >
      <h3>{activity.name}</h3>
      <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '10px' }}>
        {activity.type} • {activity.start_date ? new Date(activity.start_date).toLocaleString() : 'Unknown Date'}
      </p>

      {/* Basic Stats (Always Visible) */}
      {/* The Actual Map Component */}
      {activity.map?.summary_polyline ? (
        <div onClick={(e) => e.stopPropagation()}>
        <ActivityMap 
          encodedPolyline={activity.map.summary_polyline} 
          isMaximized={isMaximizedCard} 
          
          onMapClick={() => {
            if (!isMaximizedCard) {
              onMapClick();
              
              setTimeout(() => {
                const cardElement = document.getElementById(`activity-${activity.id}`);
                // Grab the specific scrolling container we just made in CSS
                const scrollContainer = document.querySelector('.feed-container'); 
                
                if (cardElement && scrollContainer) {
                  // Calculate exactly where the center of the card is relative to the container
                  const containerHeight = scrollContainer.clientHeight;
                  const cardTop = cardElement.offsetTop;
                  const cardHeight = cardElement.offsetHeight;
                  
                  // Math to put the card directly in the middle of the screen
                  const scrollToPosition = cardTop - (containerHeight / 2) + (cardHeight / 2);

                  scrollContainer.scrollTo({
                    top: scrollToPosition,
                    behavior: 'smooth'
                  });
                }
              }, 300);
            }
          }}
        />
        </div>
      ) : (
        <p style={{ fontSize: '0.9rem', color: '#888', fontStyle: 'italic', marginTop: '15px' }}>
          No GPS route for this activity.
        </p>
      )}
      <div className="stats-row">
        {hasDistance ? (
          <span>{useImperialDistances ? distanceMiles + ' mi' : distanceKm + ' km'}</span>
        ) : null}
        <span> {movingTimeString} </span>
      </div>
      {/* Expanded Details (Only visible when clicked) */}
      {isSelected && (
        <div style={{ 
          marginTop: '20px', 
          paddingTop: '20px', 
          borderTop: '1px solid #eee',
          animation: 'fadeIn 0.3s ease-in'
        }}>
          {isLoadingDetails && showDescription ? (
            <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '15px' }}>
              Loading description...
            </p>
          ) : (
            <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '15px' }}>
              {detailedData?.description || 'No description available.'}
            </p>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
            <div>
              <p style={{ fontSize: '0.8rem', color: '#888' }}>Average Pace</p>
              <p style={{ fontWeight: 'bold' }}>{formattedPace}</p>
            </div>
            {/* 3. Render the dynamically fetched calories */}
            <div>
              <p style={{ fontSize: '0.8rem', color: '#888', textAlign: 'right' }}>Calories</p>
              <p style={{ fontWeight: 'bold', color: '#fc4c02', textAlign: 'right' }}>
                {isLoadingDetails ? (
                  "Loading..." 
                ) : detailedData?.calories ? (
                  `${Math.round(detailedData.calories)} kcal`
                ) : (
                  "N/A"
                )}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}