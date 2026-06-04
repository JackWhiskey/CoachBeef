import { useState, useEffect, JSX } from 'react'
// @ts-ignore: side-effect import of CSS module without type declarations
import './App.css'
import { SummaryActivity } from './utils/entities.tsx'
import ActivityCard from './components/ActivityCard.tsx'
import Sidebar from './components/Sidebar.tsx'
import SettingsPanel from './components/SettingsPanel.tsx'
import AnalyticsPanel from './components/AnalyticsPanel.tsx'
import ChatPanel from './components/ChatPanel.tsx'
import DashboardPanel from './components/DashboardPanel.tsx'
import ActivitiesPanel from './components/ActivitiesPanel.tsx'

function App() {
  const [activities, setActivities] = useState<SummaryActivity[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [isMaximized, setIsMaximized] = useState<boolean>(false);
  const [useImperialDistances, setUseImperialDistances] = useState(true)
  const [activeSidebarItem, setActiveSidebarItem] = useState<string>('coach');

  const rightPanels: Record<string, JSX.Element> = {
    dashboard: (
      <DashboardPanel
      selectedActivityId={selectedId}
      />
    ),
    activities: (
      <ActivitiesPanel/>
    ),
    analytics: (
      <AnalyticsPanel/>
    ),
    coach: (
      <ChatPanel
        selectedActivityId={selectedId}
      />
    ),
    settings: (
      <SettingsPanel 
        useImperialDistances={useImperialDistances}
        setUseImperialDistances={setUseImperialDistances}
      />
    )
  };

  const LIMIT = 10;

  const fetchActivities = async (beforeDate?: string) => {
    setLoading(true)

    try {
      let url = `http://localhost:8000/api/activities?limit=${LIMIT}`
      console.log("Fetching activities with URL:", url) // Debug log to check the URL being fetched
      if (beforeDate) {
        url += `&before=${encodeURIComponent(beforeDate)}`
      }

      const response = await fetch(url)
      const data = await response.json()
      console.log("Received data:", data) // Check your browser console! TODO Remove this log after confirming data is received correctly

      if (data && data.length > 0) {
        setActivities(prev => {
          
            const existingIds = new Set(prev.map(act => act.id))
            const newUniqueActivities = data.filter((act: SummaryActivity) => !existingIds.has(act.id))
          return [...prev, ...newUniqueActivities]
        });
      }
    } catch (error) {
      console.error("Error fetching activities:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
      fetchActivities()
  }, [])

  // Cursor-based pagination trigger
  const handleLoadMore = () => {
    if (activities.length > 0) {
      // Get the exact start time of the very last activity currently loaded
      const lastActivity: SummaryActivity = activities[activities.length - 1]

      if (!lastActivity.start_date) {
        console.warn("Last activity is missing start_date, cannot fetch more activities.")
        return
      }
      console.log("Loading more activities before:", lastActivity.start_date) // Debug log to check the date being used for pagination
      fetchActivities(String(lastActivity.start_date))
    }
  }

  const handleCardClick = (id: number | null, event: React.MouseEvent<HTMLDivElement>) => {
    event.stopPropagation();
    if (id === null) {return}
    if (id === selectedId) { 
      if (isMaximized) {
        setIsMaximized(false);
      }
      return 
    }

    const targetElement = event.currentTarget;
    setSelectedId(id);
    setIsMaximized(false);

    setTimeout(() => {
      targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 50);
  }

  const handleBackgroundClick = () => {
    setSelectedId(null);
    setIsMaximized(false);
  }

  return (
    <div className="app-container">
      
      {/* 1. LEFT SIDEBAR */}
      <Sidebar 
        activeItemId={activeSidebarItem} 
        onMenuItemClick={setActiveSidebarItem} 
      />

      {/* 2. MIDDLE FEED */}
      <main className="feed-container" onClick={handleBackgroundClick}>
        <div className="feed-content">
          {loading && activities.length === 0 ? (
            <p>Loading activities...</p>
          ) : null}

          {activities.length === 0 && !loading ? (
            <p>No activities found. Check your backend terminal for errors!</p>
          ) : (
            activities.map((activity) => (
              <ActivityCard
                key={activity.id}
                activity={activity}
                isSelected={selectedId === activity.id}
                isDimmed={selectedId !== null && selectedId !== activity.id}
                isMaximized={isMaximized}
                useImperialDistances={useImperialDistances}
                onCardClick={handleCardClick}
                onMapClick={() => {
                  setSelectedId(activity.id);
                  setIsMaximized(true);
                }}
              />
            )))
          }
          {/* Load More Button */}
          {activities.length > 0 && (
            <button 
              onClick={handleLoadMore} 
              disabled={loading}
              style={{
                width: "100%", padding: "12px", marginTop: "10px",
                backgroundColor: loading ? "#ccc" : "#fc4c02", 
                color: "#fff", border: "none", borderRadius: "8px", 
                cursor: loading ? "not-allowed" : "pointer",
                fontWeight: "bold", fontSize: "1rem"
              }}
            >
              {loading ? "Loading..." : "Load Older Activities"}
            </button>
          )}
        </div>
      </main>

      {/* 3. RIGHT CHAT PANEL */}
      {rightPanels[activeSidebarItem] || rightPanels['coach']}
    </div>
  )
}

export default App