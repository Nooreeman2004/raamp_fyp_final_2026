import { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react';

// Custom Map Styles for Premium Dark Look
const DARK_MAP_STYLE = [
  { "elementType": "geometry", "stylers": [{ "color": "#121212" }] },
  { "elementType": "labels.text.stroke", "stylers": [{ "color": "#121212" }] },
  { "elementType": "labels.text.fill", "stylers": [{ "color": "#5e5e5e" }] },
  { "featureType": "administrative.locality", "elementType": "labels.text.fill", "stylers": [{ "color": "#9ca3af" }] },
  { "featureType": "poi", "elementType": "labels.text.fill", "stylers": [{ "color": "#9ca3af" }] },
  { "featureType": "poi.park", "elementType": "geometry", "stylers": [{ "color": "#1a2c2c" }] },
  { "featureType": "poi.park", "elementType": "labels.text.fill", "stylers": [{ "color": "#4d7c0f" }] },
  { "featureType": "road", "elementType": "geometry", "stylers": [{ "color": "#262626" }] },
  { "featureType": "road", "elementType": "geometry.stroke", "stylers": [{ "color": "#262626" }] },
  { "featureType": "road", "elementType": "labels.text.fill", "stylers": [{ "color": "#525252" }] },
  { "featureType": "road.highway", "elementType": "geometry", "stylers": [{ "color": "#333333" }] },
  { "featureType": "road.highway", "elementType": "geometry.stroke", "stylers": [{ "color": "#333333" }] },
  { "featureType": "road.highway", "elementType": "labels.text.fill", "stylers": [{ "color": "#a3a3a3" }] },
  { "featureType": "transit", "elementType": "geometry", "stylers": [{ "color": "#1e1e1e" }] },
  { "featureType": "transit.station", "elementType": "labels.text.fill", "stylers": [{ "color": "#9ca3af" }] },
  { "featureType": "water", "elementType": "geometry", "stylers": [{ "color": "#0a1919" }] },
  { "featureType": "water", "elementType": "labels.text.fill", "stylers": [{ "color": "#14B8A6" }] },
  { "featureType": "water", "elementType": "labels.text.stroke", "stylers": [{ "color": "#0a1919" }] }
];

const LIGHT_MAP_STYLE = [
  { "elementType": "geometry", "stylers": [{ "color": "#f5f5f5" }] },
  { "elementType": "labels.icon", "stylers": [{ "visibility": "off" }] },
  { "elementType": "labels.text.fill", "stylers": [{ "color": "#616161" }] },
  { "elementType": "labels.text.stroke", "stylers": [{ "color": "#f5f5f5" }] },
  { "featureType": "administrative.land_parcel", "elementType": "labels.text.fill", "stylers": [{ "color": "#bdbdbd" }] },
  { "featureType": "poi", "elementType": "geometry", "stylers": [{ "color": "#eeeeee" }] },
  { "featureType": "poi", "elementType": "labels.text.fill", "stylers": [{ "color": "#757575" }] },
  { "featureType": "poi.park", "elementType": "geometry", "stylers": [{ "color": "#e5e5e5" }] },
  { "featureType": "poi.park", "elementType": "labels.text.fill", "stylers": [{ "color": "#9e9e9e" }] },
  { "featureType": "road", "elementType": "geometry", "stylers": [{ "color": "#ffffff" }] },
  { "featureType": "road.arterial", "elementType": "labels.text.fill", "stylers": [{ "color": "#757575" }] },
  { "featureType": "road.highway", "elementType": "geometry", "stylers": [{ "color": "#dadada" }] },
  { "featureType": "road.highway", "elementType": "labels.text.fill", "stylers": [{ "color": "#616161" }] },
  { "featureType": "road.local", "elementType": "labels.text.fill", "stylers": [{ "color": "#9e9e9e" }] },
  { "featureType": "transit.line", "elementType": "geometry", "stylers": [{ "color": "#e5e5e5" }] },
  { "featureType": "transit.station", "elementType": "geometry", "stylers": [{ "color": "#eeeeee" }] },
  { "featureType": "water", "elementType": "geometry", "stylers": [{ "color": "#c9c9c9" }] },
  { "featureType": "water", "elementType": "labels.text.fill", "stylers": [{ "color": "#9e9e9e" }] }
];

// Safety declaration for Google Maps API
declare global {
  interface Window {
    google: any;
  }
}

interface GeoIntentMapProps {
  center: { lat: number; lng: number };
  radiusMeters: number;
  heatmapData: Array<{ lat: number; lng: number; weight: number }>;
  isDrawingActive?: boolean;
  onDrawingComplete?: (polygonPath: { lat: number; lng: number }[]) => void;
  height?: string;
}

export interface GeoIntentMapRef {
    clearDrawing: () => void;
    startDrawing: () => void;
    panTo: (latLng: [number, number]) => void;
}

const GeoIntentMap = forwardRef<GeoIntentMapRef, GeoIntentMapProps>((props, ref) => {
  const { center, radiusMeters, heatmapData, isDrawingActive, onDrawingComplete, height = '100%' } = props;
  const mapRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<any>(null);
  const [drawingManager, setDrawingManager] = useState<any>(null);
  const [heatmapLayer, setHeatmapLayer] = useState<any>(null);
  const [radiusCircle, setRadiusCircle] = useState<any>(null);
  const currentPolygonRef = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const GOOGLE_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

  // Expose methods to parent
  useImperativeHandle(ref, () => ({
      clearDrawing: () => {
          if (currentPolygonRef.current) {
              currentPolygonRef.current.setMap(null);
              currentPolygonRef.current = null;
          }
      },
      startDrawing: () => {
          if (drawingManager && window.google) {
              if (currentPolygonRef.current) {
                  currentPolygonRef.current.setMap(null);
                  currentPolygonRef.current = null;
              }
              drawingManager.setDrawingMode(window.google.maps.drawing.OverlayType.POLYGON);
          }
      },
      panTo: (latLng: [number, number]) => {
          if (map && window.google) {
              map.panTo({ lat: latLng[0], lng: latLng[1] });
          }
      }
  }));

  useEffect(() => {
    if (!GOOGLE_KEY || !mapRef.current) return;

    if (!window.google) {
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_KEY}&libraries=drawing,visualization`;
      script.async = true;
      script.defer = true;
      script.onload = initializeMap;
      document.head.appendChild(script);
    } else {
      initializeMap();
    }

    function initializeMap() {
      if (!mapRef.current || !window.google || !window.google.maps) {
        setIsLoading(false);
        return;
      }
      
      const isDark = document.documentElement.classList.contains('dark');
      
      const mapInstance = new window.google.maps.Map(mapRef.current, {
        center: center,
        zoom: 14,
        styles: isDark ? DARK_MAP_STYLE : LIGHT_MAP_STYLE,
        disableDefaultUI: false,
        zoomControl: true,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: true,
        backgroundColor: isDark ? '#0a0a0a' : '#f5f5f5',
      });

      setMap(mapInstance);

      // Initialize Drawing Manager (guard against missing library)
      if (window.google.maps.drawing) {
        const drawingMgr = new window.google.maps.drawing.DrawingManager({
        drawingControl: false, // We will trigger it via button
        polygonOptions: {
          fillColor: '#00e0d0',
          fillOpacity: 0.2,
          strokeWeight: 2,
          strokeColor: '#00e0d0',
          clickable: true,
          editable: true,
          zIndex: 1,
        },
      });

      drawingMgr.setMap(mapInstance);
        setDrawingManager(drawingMgr);

        window.google.maps.event.addListener(drawingMgr, 'overlaycomplete', function(event: any) {
          if (window.google.maps.drawing && event.type === window.google.maps.drawing.OverlayType.POLYGON) {
              if (currentPolygonRef.current) currentPolygonRef.current.setMap(null);
              
              const newPolygon = event.overlay as any; // Cast as any for flexibility
              currentPolygonRef.current = newPolygon;
              drawingMgr.setDrawingMode(null); // Stop drawing after one polygon

              if (onDrawingComplete) {
                  const path = newPolygon.getPath();
                  const coords: { lat: number; lng: number }[] = [];
                  for (let i = 0; i < path.getLength(); i++) {
                      const point = path.getAt(i);
                      coords.push({ lat: point.lat(), lng: point.lng() });
                  }
                  onDrawingComplete(coords);
              }
          }
        });
      }

      // Initialize Circle (Radius)
      const circle = new window.google.maps.Circle({
        strokeColor: "#00e0d0",
        strokeOpacity: 0.8,
        strokeWeight: 1,
        fillColor: "#00e0d0",
        fillOpacity: 0.05,
        map: mapInstance,
        center: center,
        radius: radiusMeters,
      });
      setRadiusCircle(circle);
      
      // Add Central Business Location Pin (Red Pin)
      new window.google.maps.Marker({
        position: center,
        map: mapInstance,
        title: "SCAN CENTER",
        // Using standard Google Maps pin but making it red and slightly larger
        icon: {
          path: "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z",
          fillColor: "#ef4444", // Tailwind red-500
          fillOpacity: 1,
          strokeColor: "#ffffff",
          strokeWeight: 2,
          scale: 2,
          anchor: new window.google.maps.Point(12, 21),
        },
        zIndex: 100,
      });

      setIsLoading(false);
    }
  }, [GOOGLE_KEY]);

  // Update center when it changes
  useEffect(() => {
    if (map) {
      map.panTo(center);
      if (radiusCircle) {
        radiusCircle.setCenter(center);
      }
    }
  }, [center, map]);

  // Update radius when it changes
  useEffect(() => {
    if (radiusCircle) {
      radiusCircle.setRadius(radiusMeters);
    }
  }, [radiusMeters]);

  const markersRef = useRef<any[]>([]);

  // Cleanup old markers
  const clearMarkers = () => {
    markersRef.current.forEach(m => m.setMap(null));
    markersRef.current = [];
  };

  // Handle Heatmap AND Custom Markers
  useEffect(() => {
    if (!map || !window.google || !window.google.maps) return;

    if (heatmapLayer) {
      heatmapLayer.setMap(null);
    }
    clearMarkers();

    if (heatmapData && Array.isArray(heatmapData) && heatmapData.length > 0) {
      // 1. Setup Heatmap
      if (window.google.maps.visualization) {
        const data = heatmapData.map(point => ({
          location: new window.google.maps.LatLng(point.lat, point.lng),
          weight: point.weight
        }));

        const layer = new window.google.maps.visualization.HeatmapLayer({
          data: data,
          map: map,
          radius: 60, // Increased radius for better visibility
          opacity: 0.8,
          gradient: [
            'rgba(0, 255, 255, 0)',
            'rgba(0, 255, 255, 0.2)',
            'rgba(0, 224, 208, 0.5)',
            'rgba(0, 255, 255, 0.8)',
            'rgba(255, 255, 255, 1)', // White core for intense areas
          ]
        });
        setHeatmapLayer(layer);
      }

      // 2. Setup "Live Pings" (Individual markers for specific points of interest)
      // Only show for top 10 points or specific weight
      heatmapData.slice(0, 15).forEach((point) => {
        const marker = new window.google.maps.Marker({
            position: { lat: point.lat, lng: point.lng },
            map: map,
            icon: {
                path: window.google.maps.SymbolPath.CIRCLE,
                scale: 6,
                fillColor: "#00e0d0",
                fillOpacity: 1,
                strokeColor: "#ffffff",
                strokeWeight: 1,
            },
            title: "LIVE CUSTOMER ACTIVITY",
            zIndex: 50
        });
        markersRef.current.push(marker);
      });
    }
  }, [heatmapData, map]);

  // Handle manual drawing mode trigger via prop (only if explicitly provided)
  useEffect(() => {
    if (isDrawingActive !== undefined && drawingManager && window.google) {
        if (isDrawingActive) {
            drawingManager.setDrawingMode(window.google.maps.drawing.OverlayType.POLYGON);
        } else {
            drawingManager.setDrawingMode(null);
        }
    }
  }, [isDrawingActive, drawingManager]);

  return (
    <div className="relative w-full h-full group" style={{ height }}>
      {isLoading && (
        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-background/50 backdrop-blur-sm">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mb-3"></div>
          <p className="text-[10px] font-mono text-primary animate-pulse tracking-widest text-center">INITIALIZING QUANTUM GEO-RADAR...</p>
        </div>
      )}
      <div 
        ref={mapRef} 
        className="w-full h-full rounded border border-border/50 overflow-hidden" 
        style={{ minHeight: '300px' }}
      />
    </div>
  );
});

GeoIntentMap.displayName = "GeoIntentMap";

export default GeoIntentMap;
