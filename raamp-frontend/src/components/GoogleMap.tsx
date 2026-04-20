import { useEffect, useRef, useState } from 'react';
import { loadGoogleMapsScript } from '@/lib/loadGoogleMapsScript';

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
  const [isLoading, setIsLoading] = useState(true);
  const GOOGLE_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

  useEffect(() => {
    if (!GOOGLE_KEY || !mapRef.current) return;

    const markersRef: any[] = [];
    let cancelled = false;

    const initializeMap = () => {
      if (!mapRef.current || !window.google?.maps) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);

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

      // Add markers for each location
      const newMarkers = locations.map((location) => {
        const marker = new window.google.maps.Marker({
          position: { lat: location.lat, lng: location.lng },
          map: mapInstance,
          title: location.name || 'Location',
          animation: window.google.maps.Animation.DROP
        });

        // Add info window if name or address is provided
        if (location.name || location.address) {
          const infoWindow = new window.google.maps.InfoWindow({
            content: `
              <div style="padding: 8px; color: #333;">
                ${location.name ? `<h3 style="margin: 0 0 4px 0; font-weight: bold; color: #000;">${location.name}</h3>` : ''}
                ${location.address ? `<p style="margin: 0; color: #666; font-size: 14px;">${location.address}</p>` : ''}
              </div>
            `,
          });

          marker.addListener('click', () => {
            infoWindow.open(mapInstance, marker);
          });

          // Open info window by default if it's the only location
          if (locations.length === 1) {
            infoWindow.open(mapInstance, marker);
          }
        }

        return marker;
      });

      markersRef.push(...newMarkers);
      setMarkers(newMarkers);

      // Fit bounds if multiple locations
      if (locations.length > 1) {
        const bounds = new window.google.maps.LatLngBounds();
        locations.forEach(location => {
          bounds.extend({ lat: location.lat, lng: location.lng });
        });
        mapInstance.fitBounds(bounds);
      }

      setIsLoading(false);
    };

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
      markersRef.forEach((marker) => marker.setMap(null));
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
          backgroundColor: 'rgba(0,0,0,0.2)',
          borderRadius: '4px',
          border: '1px solid rgba(255,255,255,0.05)'
        }}
      >
        <p style={{ color: '#666', fontSize: '12px', fontFamily: 'monospace' }}>MAP ENGINE NOT CONFIGURED</p>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full group" style={{ height }}>
      {isLoading && (
        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-slate-950/50 backdrop-blur-sm">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mb-3"></div>
          <p className="text-[10px] font-mono text-primary animate-pulse tracking-widest">INITIALIZING MAP ENGINE...</p>
        </div>
      )}
      <div
        ref={mapRef}
        className="w-full h-full"
        style={{
          height: '100%',
          width: '100%',
        }}
      />
    </div>
  );
}

