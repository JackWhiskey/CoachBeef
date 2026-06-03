import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Polyline, useMap, useMapEvents } from 'react-leaflet';
import polyline from '@mapbox/polyline';
// @ts-ignore: side-effect import of Leaflet CSS without type declarations
import 'leaflet/dist/leaflet.css';

interface ActivityMapProps {
  encodedPolyline: string;
  isMaximized: boolean;
  onMapClick: () => void;
}

// 1. Utility: Forces Leaflet to fetch new tiles when the container changes size
const MapResizer = ({ isMaximized }: { isMaximized: boolean }) => {
  const map = useMap();
  useEffect(() => {
    const timeout = setTimeout(() => {
      map.invalidateSize();
    }, 300);
    return () => clearTimeout(timeout);
  }, [isMaximized, map]);
  return null;
};

// 2. Utility: Catches map clicks and stops them from bubbling up to the card
const MapInteraction = ({ onClick }: { onClick: () => void }) => {
  useMapEvents({
    click: (e) => {
      e.originalEvent.stopPropagation();
      onClick();
    }
  });
  return null;
};

const MapInteractivity = ({ isMaximized }: { isMaximized: boolean }) => {
  const map = useMap();
  
  useEffect(() => {
    if (isMaximized) {
      // Turn everything on when expanded
      map.dragging.enable();
      map.scrollWheelZoom.enable();
      map.touchZoom.enable();
      map.doubleClickZoom.enable();
    } else {
      // Lock it completely down when it's a thumbnail
      map.dragging.disable();
      map.scrollWheelZoom.disable();
      map.touchZoom.disable();
      map.doubleClickZoom.disable();
    }
  }, [isMaximized, map]);

  return null;
};

// A helper component to automatically zoom the map to fit the route
const MapBounds = ({ positions }: { positions: [number, number][] }) => {
  const map = useMap();
  useEffect(() => {
    if (positions.length > 0) {
      map.fitBounds(positions, { padding: [20, 20] });
    }
  }, [map, positions]);
  return null;
};

export default function ActivityMap({ encodedPolyline, isMaximized, onMapClick }: ActivityMapProps) {
  const [positions, setPositions] = useState<[number, number][]>([]);

  useEffect(() => {
    if (encodedPolyline) {
      const decoded = polyline.decode(encodedPolyline);
      setPositions(decoded as [number, number][]);
    }
  }, [encodedPolyline]);

  if (positions.length === 0) return null;

  const mapHeight = isMaximized ? '50vh' : '150px';

  return (
    <div style={{ 
      height: mapHeight, 
      width: '100%', 
      borderRadius: '8px', 
      overflow: 'hidden', 
      marginTop: '15px',
      transition: 'height 0.3s ease-in-out' 
    }}>
      <MapContainer 
        bounds={positions} 
        zoomControl={false}
        scrollWheelZoom={false} 
        dragging={false}
        style={{ height: '100%', width: '100%' }}
      >
        <MapInteraction onClick={onMapClick} />
        <MapResizer isMaximized={isMaximized} />
        
        <MapInteractivity isMaximized={isMaximized} />

        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polyline positions={positions} pathOptions={{ color: '#fc4c02', weight: 4, opacity: 0.8 }} />
        <MapBounds positions={positions} />
      </MapContainer>
    </div>
  );
}