import { useEffect, useRef, useState } from 'react';
import { apiClient } from '@/services/api';

interface GoogleMapProps {
  locations: Array<{
    lat: number;
    lng: number;
    name?: string;
    address?: string;
  }>;
  center?: { lat: number; lng: number };
  zoom?: number;
  height?: string;
}

declare global {
  interface Window {
    google: any;
    initMap: () => void;
  }
}

export default function GoogleMap({ 
  locations, 
  center, 
  zoom = 12, 
  height = '400px' 
}: GoogleMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<any>(null);
  const [markers, setMarkers] = useState<any[]>([]);
  const GOOGLE_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

  useEffect(() => {
    if (!GOOGLE_KEY || !mapRef.current) return;

    // Load Google Maps script if not already loaded
    if (!window.google) {
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_KEY}&libraries=places`;
      script.async = true;
      script.defer = true;
      script.onload = initializeMap;
      document.head.appendChild(script);
    } else {
      initializeMap();
    }

    function initializeMap() {
      if (!mapRef.current || !window.google) return;

      const defaultCenter = center || (locations.length > 0 
        ? { lat: locations[0].lat, lng: locations[0].lng }
        : { lat: 37.7749, lng: -122.4194 }); // Default to San Francisco

      const mapInstance = new window.google.maps.Map(mapRef.current, {
        center: defaultCenter,
        zoom: zoom,
        mapTypeControl: true,
        streetViewControl: true,
        fullscreenControl: true,
      });

      setMap(mapInstance);

      // Clear existing markers
      markers.forEach(marker => marker.setMap(null));

      // Add markers for each location
      const newMarkers = locations.map(location => {
        const marker = new window.google.maps.Marker({
          position: { lat: location.lat, lng: location.lng },
          map: mapInstance,
          title: location.name || 'Location',
        });

        // Add info window if name or address is provided
        if (location.name || location.address) {
          const infoWindow = new window.google.maps.InfoWindow({
            content: `
              <div style="padding: 8px;">
                ${location.name ? `<h3 style="margin: 0 0 4px 0; font-weight: bold;">${location.name}</h3>` : ''}
                ${location.address ? `<p style="margin: 0; color: #666; font-size: 14px;">${location.address}</p>` : ''}
              </div>
            `,
          });

          marker.addListener('click', () => {
            infoWindow.open(mapInstance, marker);
          });
        }

        return marker;
      });

      setMarkers(newMarkers);

      // Fit bounds if multiple locations
      if (locations.length > 1) {
        const bounds = new window.google.maps.LatLngBounds();
        locations.forEach(location => {
          bounds.extend({ lat: location.lat, lng: location.lng });
        });
        mapInstance.fitBounds(bounds);
      }
    }

    return () => {
      // Cleanup markers
      markers.forEach(marker => marker.setMap(null));
    };
  }, [locations, center, zoom, GOOGLE_KEY]);

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

