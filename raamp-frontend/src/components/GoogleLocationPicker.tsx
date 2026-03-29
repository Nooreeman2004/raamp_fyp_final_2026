import { useEffect, useRef, useState } from 'react';

interface GoogleLocationPickerProps {
    onLocationSelect: (lat: number, lng: number) => void;
    initialLat?: number;
    initialLng?: number;
    zoom?: number;
    height?: string;
}

declare global {
    interface Window {
        google: any;
    }
}

export default function GoogleLocationPicker({
    onLocationSelect,
    initialLat,
    initialLng,
    zoom = 15,
    height = '300px'
}: GoogleLocationPickerProps) {
    const mapRef = useRef<HTMLDivElement>(null);
    const [map, setMap] = useState<any>(null);
    const [marker, setMarker] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);
    const GOOGLE_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

    useEffect(() => {
        if (!GOOGLE_KEY || !mapRef.current) return;

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
            if (!mapRef.current || !window.google) {
                setIsLoading(false);
                return;
            }

            setIsLoading(true);

            const defaultCenter = (initialLat && initialLng && initialLat !== 0)
                ? { lat: initialLat, lng: initialLng }
                : { lat: 31.5204, lng: 74.3587 }; // Default to Lahore, Pakistan or similar if none provided

            const mapInstance = new window.google.maps.Map(mapRef.current, {
                center: defaultCenter,
                zoom: zoom,
                mapTypeControl: false,
                streetViewControl: false,
                fullscreenControl: true,
            });

            const markerInstance = new window.google.maps.Marker({
                position: defaultCenter,
                map: mapInstance,
                draggable: true,
                animation: window.google.maps.Animation.DROP,
                title: 'Drag me to your precise location'
            });

            setMap(mapInstance);
            setMarker(markerInstance);

            // Listener for map click to move marker
            mapInstance.addListener('click', (e: any) => {
                const clickedLocation = e.latLng;
                markerInstance.setPosition(clickedLocation);
                onLocationSelect(clickedLocation.lat(), clickedLocation.lng());
            });

            // Listener for marker drag end
            markerInstance.addListener('dragend', () => {
                const finalPosition = markerInstance.getPosition();
                onLocationSelect(finalPosition.lat(), finalPosition.lng());
            });

            setIsLoading(false);
        }
    }, [GOOGLE_KEY]);

    // Update marker position if initial coordinates change from parent (e.g. from search)
    useEffect(() => {
        if (map && marker && initialLat && initialLng && initialLat !== 0) {
            const newPos = { lat: initialLat, lng: initialLng };
            marker.setPosition(newPos);
            map.panTo(newPos);
        }
    }, [initialLat, initialLng, map, marker]);

    if (!GOOGLE_KEY) {
        return (
            <div className="flex items-center justify-center bg-slate-900 border border-white/10 rounded-lg" style={{ height }}>
                <p className="text-xs font-mono text-muted-foreground">GOOGLE MAPS KEY MISSING</p>
            </div>
        );
    }

    return (
        <div className="relative w-full rounded-lg overflow-hidden border border-primary/20" style={{ height }}>
            {isLoading && (
                <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-slate-950/70 backdrop-blur-sm">
                    <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mb-2"></div>
                    <p className="text-[10px] font-mono text-primary tracking-widest">LOADING MAP...</p>
                </div>
            )}
            <div ref={mapRef} className="w-full h-full" />
            <div className="absolute bottom-4 left-4 z-10 bg-slate-950/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-primary/30 shadow-lg">
                <p className="text-[10px] text-primary font-mono uppercase tracking-tighter">Click or drag pin to adjust</p>
            </div>
        </div>
    );
}
