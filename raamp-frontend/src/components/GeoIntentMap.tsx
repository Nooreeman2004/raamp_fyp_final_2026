import { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react';
import { MapPin } from 'lucide-react';
import { loadGoogleMapsScript } from '@/lib/loadGoogleMapsScript';

// Custom Map Styles for Premium Dark Look
const DARK_MAP_STYLE = [
  { elementType: "geometry", stylers: [{ color: "#121212" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#121212" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#5e5e5e" }] },
  { featureType: "administrative.locality", elementType: "labels.text.fill", stylers: [{ color: "#9ca3af" }] },
  { featureType: "poi", elementType: "labels.text.fill", stylers: [{ color: "#9ca3af" }] },
  { featureType: "poi.park", elementType: "geometry", stylers: [{ color: "#1a2c2c" }] },
  { featureType: "poi.park", elementType: "labels.text.fill", stylers: [{ color: "#4d7c0f" }] },
  { featureType: "road", elementType: "geometry", stylers: [{ color: "#262626" }] },
  { featureType: "road", elementType: "geometry.stroke", stylers: [{ color: "#262626" }] },
  { featureType: "road", elementType: "labels.text.fill", stylers: [{ color: "#525252" }] },
  { featureType: "road.highway", elementType: "geometry", stylers: [{ color: "#333333" }] },
  { featureType: "road.highway", elementType: "geometry.stroke", stylers: [{ color: "#333333" }] },
  { featureType: "road.highway", elementType: "labels.text.fill", stylers: [{ color: "#a3a3a3" }] },
  { featureType: "transit", elementType: "geometry", stylers: [{ color: "#1e1e1e" }] },
  { featureType: "transit.station", elementType: "labels.text.fill", stylers: [{ color: "#9ca3af" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#0a1919" }] },
  { featureType: "water", elementType: "labels.text.fill", stylers: [{ color: "#14B8A6" }] },
  { featureType: "water", elementType: "labels.text.stroke", stylers: [{ color: "#0a1919" }] },
];

const LIGHT_MAP_STYLE = [
  { elementType: "geometry", stylers: [{ color: "#f5f5f5" }] },
  { elementType: "labels.icon", stylers: [{ visibility: "off" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#616161" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#f5f5f5" }] },
  { featureType: "administrative.land_parcel", elementType: "labels.text.fill", stylers: [{ color: "#bdbdbd" }] },
  { featureType: "poi", elementType: "geometry", stylers: [{ color: "#eeeeee" }] },
  { featureType: "poi", elementType: "labels.text.fill", stylers: [{ color: "#757575" }] },
  { featureType: "poi.park", elementType: "geometry", stylers: [{ color: "#e5e5e5" }] },
  { featureType: "poi.park", elementType: "labels.text.fill", stylers: [{ color: "#9e9e9e" }] },
  { featureType: "road", elementType: "geometry", stylers: [{ color: "#ffffff" }] },
  { featureType: "road.arterial", elementType: "labels.text.fill", stylers: [{ color: "#757575" }] },
  { featureType: "road.highway", elementType: "geometry", stylers: [{ color: "#dadada" }] },
  { featureType: "road.highway", elementType: "labels.text.fill", stylers: [{ color: "#616161" }] },
  { featureType: "road.local", elementType: "labels.text.fill", stylers: [{ color: "#9e9e9e" }] },
  { featureType: "transit.line", elementType: "geometry", stylers: [{ color: "#e5e5e5" }] },
  { featureType: "transit.station", elementType: "geometry", stylers: [{ color: "#eeeeee" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#c9c9c9" }] },
  { featureType: "water", elementType: "labels.text.fill", stylers: [{ color: "#9e9e9e" }] },
];

declare global {
  interface Window {
    google: any;
  }
}

interface GeoIntentMapProps {
  center: { lat: number; lng: number };
  radiusMeters: number;
  heatmapData: Array<{ lat: number; lng: number; weight: number }>;
  zonePins?: Array<{ lat: number; lng: number; label: string }>;
  height?: string;
}

export interface GeoIntentMapRef {
  panTo: (latLng: [number, number]) => void;
}

const GeoIntentMap = forwardRef<GeoIntentMapRef, GeoIntentMapProps>((props, ref) => {
  const { center, radiusMeters, heatmapData, zonePins, height = "100%" } = props;
  const mapRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<any>(null);
  const [heatmapLayer, setHeatmapLayer] = useState<any>(null);
  const [radiusCircle, setRadiusCircle] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const GOOGLE_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "";

  useImperativeHandle(ref, () => ({
    panTo: (latLng: [number, number]) => {
      if (map && window.google) {
        map.panTo({ lat: latLng[0], lng: latLng[1] });
      }
    },
  }));

  useEffect(() => {
    if (!GOOGLE_KEY) {
      setIsLoading(false);
      return;
    }
    if (!mapRef.current) return;

    let cancelled = false;

    (async () => {
      try {
        await loadGoogleMapsScript(GOOGLE_KEY);
        if (cancelled || !mapRef.current || !window.google?.maps) {
          setIsLoading(false);
          return;
        }

        const isDark = document.documentElement.classList.contains("dark");

        const mapInstance = new window.google.maps.Map(mapRef.current, {
          center,
          zoom: 14,
          styles: isDark ? DARK_MAP_STYLE : LIGHT_MAP_STYLE,
          disableDefaultUI: false,
          zoomControl: true,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: true,
          backgroundColor: isDark ? "#0a0a0a" : "#f5f5f5",
        });

        setMap(mapInstance);

        const circle = new window.google.maps.Circle({
          strokeColor: "#00e0d0",
          strokeOpacity: 0.8,
          strokeWeight: 1,
          fillColor: "#00e0d0",
          fillOpacity: 0.05,
          map: mapInstance,
          center,
          radius: radiusMeters,
        });
        setRadiusCircle(circle);

        new window.google.maps.Marker({
          position: center,
          map: mapInstance,
          title: "SCAN CENTER",
          icon: {
            path: "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z",
            fillColor: "#ef4444",
            fillOpacity: 1,
            strokeColor: "#ffffff",
            strokeWeight: 2,
            scale: 2,
            anchor: new window.google.maps.Point(12, 21),
          },
          zIndex: 100,
        });

        setIsLoading(false);
      } catch {
        setIsLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [GOOGLE_KEY]);

  useEffect(() => {
    if (map) {
      map.panTo(center);
      if (radiusCircle) {
        radiusCircle.setCenter(center);
      }
    }
  }, [center, map, radiusCircle]);

  useEffect(() => {
    if (radiusCircle) {
      radiusCircle.setRadius(radiusMeters);
    }
  }, [radiusMeters, radiusCircle]);

  const heatMarkersRef = useRef<any[]>([]);

  const clearHeatMarkers = () => {
    heatMarkersRef.current.forEach((m) => m.setMap(null));
    heatMarkersRef.current = [];
  };

  const zoneMarkersRef = useRef<any[]>([]);

  const clearZoneMarkers = () => {
    zoneMarkersRef.current.forEach((m) => m.setMap(null));
    zoneMarkersRef.current = [];
  };

  useEffect(() => {
    if (!map || !window.google?.maps) return;

    if (heatmapLayer) {
      heatmapLayer.setMap(null);
    }
    clearHeatMarkers();

    if (heatmapData && Array.isArray(heatmapData) && heatmapData.length > 0) {
      if (window.google.maps.visualization) {
        const data = heatmapData.map((point) => ({
          location: new window.google.maps.LatLng(point.lat, point.lng),
          weight: point.weight,
        }));

        const layer = new window.google.maps.visualization.HeatmapLayer({
          data,
          map,
          radius: 60,
          opacity: 0.8,
          gradient: [
            "rgba(0, 255, 255, 0)",
            "rgba(0, 255, 255, 0.2)",
            "rgba(0, 224, 208, 0.5)",
            "rgba(0, 255, 255, 0.8)",
            "rgba(255, 255, 255, 1)",
          ],
        });
        setHeatmapLayer(layer);
      }

      heatmapData.slice(0, 15).forEach((point) => {
        const marker = new window.google.maps.Marker({
          position: { lat: point.lat, lng: point.lng },
          map,
          icon: {
            path: window.google.maps.SymbolPath.CIRCLE,
            scale: 6,
            fillColor: "#00e0d0",
            fillOpacity: 1,
            strokeColor: "#ffffff",
            strokeWeight: 1,
          },
          title: "LIVE CUSTOMER ACTIVITY",
          zIndex: 50,
        });
        heatMarkersRef.current.push(marker);
      });
    }
  }, [heatmapData, map]);

  useEffect(() => {
    if (!map || !window.google?.maps) return;
    clearZoneMarkers();
    if (!zonePins || zonePins.length === 0) return;
    zonePins.forEach((z) => {
      const marker = new window.google.maps.Marker({
        position: { lat: z.lat, lng: z.lng },
        map,
        title: `Zone ${z.label}`,
        label: {
          text: z.label,
          color: "#0a0a0a",
          fontSize: "10px",
          fontWeight: "700",
        },
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 8,
          fillColor: "#f59e0b",
          fillOpacity: 1,
          strokeColor: "#ffffff",
          strokeWeight: 2,
        },
        zIndex: 80,
      });
      zoneMarkersRef.current.push(marker);
    });
  }, [map, zonePins]);

  return (
    <div className="relative w-full h-full group" style={{ height }}>
      {!GOOGLE_KEY ? (
        <div className="flex flex-col items-center justify-center min-h-[300px] rounded border border-dashed border-border bg-muted/20 p-6 text-center">
          <MapPin className="w-10 h-10 text-muted-foreground mb-3 opacity-70" aria-hidden />
          <p className="text-sm font-medium text-foreground">Map needs a Google Maps API key</p>
          <p className="text-xs text-muted-foreground mt-2 max-w-sm leading-relaxed">
            Add <code className="rounded bg-muted px-1 py-0.5 text-[11px]">VITE_GOOGLE_MAPS_API_KEY</code> to your
            <code className="rounded bg-muted px-1 py-0.5 text-[11px] ml-1">.env</code> in the frontend project and restart Vite
            (<code className="rounded bg-muted px-1 py-0.5 text-[11px]">npm run dev</code>).
          </p>
        </div>
      ) : (
        <>
          {isLoading && (
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-background/50 backdrop-blur-sm">
              <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mb-3"></div>
              <p className="text-[10px] font-mono text-primary animate-pulse tracking-widest text-center">
                INITIALIZING QUANTUM GEO-RADAR...
              </p>
            </div>
          )}
          <div
            ref={mapRef}
            className="w-full h-full rounded border border-border/50 overflow-hidden"
            style={{ minHeight: "300px" }}
          />
        </>
      )}
    </div>
  );
});

GeoIntentMap.displayName = "GeoIntentMap";

export default GeoIntentMap;
