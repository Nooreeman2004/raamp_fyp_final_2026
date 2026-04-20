import { useEffect, useRef, useState } from 'react';
import { loadGoogleMapsScript } from '@/lib/loadGoogleMapsScript';

interface HeatmapMapProps {
  userLocation?: {
    lat: number;
    lng: number;
    name?: string;
  };
  highIntentAreas?: Array<{
    lat: number;
    lng: number;
    name?: string;
    intensity?: number;
  }>;
  height?: string;
}

declare global {
  interface Window {
    google: any;
  }
}

export default function HeatmapMap({ 
  userLocation,
  highIntentAreas = [],
  height = '400px' 
}: HeatmapMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<any>(null);
  const [markers, setMarkers] = useState<any[]>([]);
  const [heatmap, setHeatmap] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const GOOGLE_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

  useEffect(() => {
    if (!GOOGLE_KEY || !mapRef.current) return;

    const markersRef: any[] = [];
    let heatmapLayer: any = null;
    let cancelled = false;

    function initializeMap() {
      if (!mapRef.current || !window.google?.maps) {
        setIsLoading(false);
        return;
      }
      
      setIsLoading(true);

      // Determine center - use user location or first high intent area
      const defaultCenter = userLocation 
        ? { lat: userLocation.lat, lng: userLocation.lng }
        : (highIntentAreas.length > 0
          ? { lat: highIntentAreas[0].lat, lng: highIntentAreas[0].lng }
          : { lat: 24.8607, lng: 67.0011 }); // Default to Karachi

      const mapInstance = new window.google.maps.Map(mapRef.current, {
        center: defaultCenter,
        zoom: userLocation ? 13 : 12,
        mapTypeControl: true,
        streetViewControl: false,
        fullscreenControl: true,
      });

      setMap(mapInstance);

      const newMarkers: any[] = [];

      // Add user location marker (yellow)
      if (userLocation) {
        const userMarker = new window.google.maps.Marker({
          position: { lat: userLocation.lat, lng: userLocation.lng },
          map: mapInstance,
          title: userLocation.name || 'Your Location',
          icon: {
            path: window.google.maps.SymbolPath.CIRCLE,
            scale: 10,
            fillColor: '#FFD700', // Yellow
            fillOpacity: 1,
            strokeColor: '#FFA500',
            strokeWeight: 3,
          },
        });

        const userInfoWindow = new window.google.maps.InfoWindow({
          content: `
            <div style="padding: 8px;">
              <h3 style="margin: 0 0 4px 0; font-weight: bold; color: #FFD700;">Your Location</h3>
              ${userLocation.name ? `<p style="margin: 0; color: #666; font-size: 14px;">${userLocation.name}</p>` : ''}
            </div>
          `,
        });

        userMarker.addListener('click', () => {
          userInfoWindow.open(mapInstance, userMarker);
        });

        newMarkers.push(userMarker);
      }

      // Add high intent area markers (red)
      highIntentAreas.forEach((area, index) => {
        const intensity = area.intensity || 0.8;
        const marker = new window.google.maps.Marker({
          position: { lat: area.lat, lng: area.lng },
          map: mapInstance,
          title: area.name || `High Intent Area ${index + 1}`,
          icon: {
            path: window.google.maps.SymbolPath.CIRCLE,
            scale: 12,
            fillColor: '#FF0000', // Red
            fillOpacity: intensity,
            strokeColor: '#CC0000',
            strokeWeight: 2,
          },
        });

        const infoWindow = new window.google.maps.InfoWindow({
          content: `
            <div style="padding: 8px;">
              <h3 style="margin: 0 0 4px 0; font-weight: bold; color: #FF0000;">High Intent Area</h3>
              ${area.name ? `<p style="margin: 0; color: #666; font-size: 14px;">${area.name}</p>` : ''}
              <p style="margin: 4px 0 0 0; color: #666; font-size: 12px;">Intensity: ${Math.round(intensity * 100)}%</p>
            </div>
          `,
        });

        marker.addListener('click', () => {
          infoWindow.open(mapInstance, marker);
        });

        newMarkers.push(marker);
      });

      newMarkers.forEach((m) => markersRef.push(m));
      setMarkers(newMarkers);

      // Create heatmap layer for high intent areas
      if (highIntentAreas.length > 0 && window.google.maps.visualization) {
        const heatmapData = highIntentAreas.map(area => ({
          location: new window.google.maps.LatLng(area.lat, area.lng),
          weight: (area.intensity || 0.8) * 10,
        }));

        const hm = new window.google.maps.visualization.HeatmapLayer({
          data: heatmapData,
          map: mapInstance,
          radius: 50,
          opacity: 0.6,
        });

        hm.set('gradient', [
          'rgba(255, 0, 0, 0)',
          'rgba(255, 0, 0, 0.4)',
          'rgba(255, 0, 0, 0.6)',
          'rgba(255, 0, 0, 0.8)',
          'rgba(255, 0, 0, 1)',
        ]);

        heatmapLayer = hm;
        setHeatmap(hm);
      }

      // Fit bounds if we have multiple locations
      if (userLocation && highIntentAreas.length > 0) {
        const bounds = new window.google.maps.LatLngBounds();
        bounds.extend({ lat: userLocation.lat, lng: userLocation.lng });
        highIntentAreas.forEach(area => {
          bounds.extend({ lat: area.lat, lng: area.lng });
        });
        mapInstance.fitBounds(bounds);
      }
      
      setIsLoading(false);
    }

    void (async () => {
      try {
        await loadGoogleMapsScript(GOOGLE_KEY);
        if (cancelled) return;
        initializeMap();
      } catch {
        setIsLoading(false);
      }
    })();

    return () => {
      cancelled = true;
      markersRef.forEach(marker => marker.setMap(null));
      if (heatmapLayer) {
        heatmapLayer.setMap(null);
      }
    };
  }, [userLocation, highIntentAreas, GOOGLE_KEY]);

  if (!GOOGLE_KEY) {
    return (
      <div 
        style={{ 
          height, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          backgroundColor: '#f0f0f0',
          borderRadius: '8px',
          border: '1px solid #ddd'
        }}
      >
        <p style={{ color: '#666' }}>Google Maps API key not configured</p>
      </div>
    );
  }

  return (
    <div 
      ref={mapRef} 
      style={{ 
        width: '100%', 
        height: height,
        borderRadius: '8px',
        overflow: 'hidden',
        border: '1px solid #e0e0e0'
      }} 
    />
  );
}

