import { useEffect, useRef, useState } from 'react';
import { Search, MapPin, Loader2, Navigation } from 'lucide-react';
import { Input } from './ui/input';
import { loadGoogleMapsScript } from '@/lib/loadGoogleMapsScript';

interface GoogleLocationPickerProps {
    onLocationSelect: (lat: number, lng: number, address?: string) => void;
    initialLat?: number;
    initialLng?: number;
    initialAddress?: string;
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
    initialAddress = '',
    zoom = 15,
    height = '400px'
}: GoogleLocationPickerProps) {
    const mapRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const [map, setMap] = useState<any>(null);
    const [marker, setMarker] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [address, setAddress] = useState(initialAddress);
    
    const GOOGLE_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

    useEffect(() => {
        if (!GOOGLE_KEY || !mapRef.current) return;

        let cancelled = false;

        void (async () => {
            try {
                await loadGoogleMapsScript(GOOGLE_KEY);
                if (cancelled) return;
                initializeMap();
            } catch {
                setIsLoading(false);
            }
        })();

        function initializeMap() {
            if (!mapRef.current || !window.google || !window.google.maps) {
                setIsLoading(false);
                return;
            }

            const defaultCenter = (initialLat && initialLng && initialLat !== 0)
                ? { lat: initialLat, lng: initialLng }
                : { lat: 31.5204, lng: 74.3587 }; // Default center

            const isDark = document.documentElement.classList.contains('dark');
            
            const mapInstance = new window.google.maps.Map(mapRef.current, {
                center: defaultCenter,
                zoom: zoom,
                disableDefaultUI: false,
                zoomControl: true,
                mapTypeControl: false,
                streetViewControl: false,
                fullscreenControl: true,
                styles: isDark ? [
                    { "elementType": "geometry", "stylers": [{ "color": "#1e293b" }] },
                    { "elementType": "labels.text.stroke", "stylers": [{ "color": "#1e293b" }] },
                    { "elementType": "labels.text.fill", "stylers": [{ "color": "#94a3b8" }] },
                    { "featureType": "road", "elementType": "geometry", "stylers": [{ "color": "#334155" }] },
                    { "featureType": "water", "elementType": "geometry", "stylers": [{ "color": "#0f172a" }] }
                ] : []
            });

            const markerInstance = new window.google.maps.Marker({
                position: defaultCenter,
                map: mapInstance,
                draggable: true,
                animation: window.google.maps.Animation.DROP,
                icon: {
                    path: "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z",
                    fillColor: "#00e0d0", 
                    fillOpacity: 1,
                    strokeColor: "#ffffff",
                    strokeWeight: 2,
                    scale: 2,
                    anchor: new window.google.maps.Point(12, 21),
                }
            });

            setMap(mapInstance);
            setMarker(markerInstance);

            // Initialize Autocomplete
            if (inputRef.current) {
                const autocomplete = new window.google.maps.places.Autocomplete(inputRef.current, {
                    types: ['geocode', 'establishment'],
                });
                autocomplete.bindTo('bounds', mapInstance);

                autocomplete.addListener('place_changed', () => {
                    const place = autocomplete.getPlace();
                    if (!place.geometry || !place.geometry.location) {
                        return; // Handle case where user hits enter on invalid text
                    }

                    const location = place.geometry.location;
                    mapInstance.setCenter(location);
                    mapInstance.setZoom(17);
                    markerInstance.setPosition(location);
                    
                    setAddress(place.formatted_address || '');
                    onLocationSelect(location.lat(), location.lng(), place.formatted_address);
                });
            }

            // Map click listener
            mapInstance.addListener('click', (e: any) => {
                const clickedLocation = e.latLng;
                markerInstance.setPosition(clickedLocation);
                updateAddressFromCoords(clickedLocation.lat(), clickedLocation.lng());
            });

            // Marker drag listener
            markerInstance.addListener('dragend', () => {
                const finalPosition = markerInstance.getPosition();
                updateAddressFromCoords(finalPosition.lat(), finalPosition.lng());
            });

            setIsLoading(false);
        }

        async function updateAddressFromCoords(lat: number, lng: number) {
            if (!window.google || !window.google.maps) return;
            const geocoder = new window.google.maps.Geocoder();
            try {
                const response = await geocoder.geocode({ location: { lat, lng } });
                if (response.results && response.results[0]) {
                    const formattedAddress = response.results[0].formatted_address;
                    setAddress(formattedAddress);
                    onLocationSelect(lat, lng, formattedAddress);
                } else {
                    onLocationSelect(lat, lng);
                }
            } catch (err) {
                onLocationSelect(lat, lng);
            }
        }

        return () => {
            cancelled = true;
        };
    }, [GOOGLE_KEY]);

    const handleCurrentLocation = () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition((position) => {
                const pos = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                map.setCenter(pos);
                map.setZoom(17);
                marker.setPosition(pos);
                // Trigger geocode
                const geocoder = new window.google.maps.Geocoder();
                geocoder.geocode({ location: pos }, (results: any, status: any) => {
                    if (status === 'OK' && results[0]) {
                        setAddress(results[0].formatted_address);
                        onLocationSelect(pos.lat, pos.lng, results[0].formatted_address);
                    }
                });
            });
        }
    };

    return (
        <div className="flex flex-col gap-4 w-full">
            {/* Search Input Container */}
            <div className="relative group">
                <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none text-muted-foreground group-focus-within:text-primary transition-colors">
                    <Search className="w-4 h-4" />
                </div>
                <Input
                    ref={inputRef}
                    type="text"
                    placeholder="Search for a location..."
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    className="pl-10 pr-12 h-12 bg-background border-primary/20 focus:border-primary/50 transition-all rounded-xl shadow-sm"
                />
                <button
                    onClick={handleCurrentLocation}
                    className="absolute inset-y-2 right-2 flex items-center px-2 hover:bg-primary/10 rounded-lg text-primary transition-colors"
                    title="Use current location"
                >
                    <Navigation className="w-4 h-4" />
                </button>
            </div>

            {/* Map Container */}
            <div 
                className="relative w-full rounded-2xl overflow-hidden border border-primary/20 shadow-2xl group" 
                style={{ height }}
            >
                {isLoading && (
                    <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-background/80 backdrop-blur-md">
                        <Loader2 className="w-8 h-8 text-primary animate-spin mb-4" />
                        <p className="text-xs font-mono text-primary tracking-[0.2em] animate-pulse">SYNCHRONIZING GEO-COORDINATES</p>
                    </div>
                )}
                
                {/* Visual Accent Overlay */}
                <div className="absolute top-4 left-4 z-10 flex gap-2">
                    <div className="bg-background/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-border/50 flex items-center gap-2 shadow-xl">
                        <MapPin className="w-3.5 h-3.5 text-primary" />
                        <span className="text-[10px] font-mono font-bold tracking-tight uppercase">Live Precision Mode</span>
                    </div>
                </div>

                <div ref={mapRef} className="w-full h-full grayscale-[0.2] contrast-[1.1]" />
                
                {/* Bottom Status Bar */}
                <div className="absolute bottom-4 inset-x-4 z-10">
                    <div className="bg-background/90 backdrop-blur-md px-4 py-2.5 rounded-xl border border-border/50 flex items-center justify-between shadow-2xl">
                        <div className="flex flex-col">
                            <span className="text-[9px] text-muted-foreground uppercase font-bold tracking-widest">Active Search Target</span>
                            <span className="text-xs font-medium truncate max-w-[250px]">{address || 'Awaiting selection...'}</span>
                        </div>
                        <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                    </div>
                </div>
            </div>
        </div>
    );
}
