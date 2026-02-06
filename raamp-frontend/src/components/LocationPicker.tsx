import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icon in React Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface LocationPickerProps {
    initialLat?: number;
    initialLng?: number;
    onLocationSelect: (lat: number, lng: number) => void;
}

// Custom red marker icon
const redIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const LocationMarker = ({ onLocationSelect, position }: { onLocationSelect: (lat: number, lng: number) => void, position: L.LatLng | null }) => {
    const map = useMapEvents({
        click(e) {
            onLocationSelect(e.latlng.lat, e.latlng.lng);
            map.flyTo(e.latlng, map.getZoom());
        },
    });

    // Side effect: fly to position if it changes externally
    useEffect(() => {
        if (position) {
            map.flyTo(position, map.getZoom());
        }
    }, [position, map]);

    return position === null ? null : (
        <Marker position={position} icon={redIcon} />
    );
};

const LocationPicker = ({ initialLat = 51.505, initialLng = -0.09, onLocationSelect }: LocationPickerProps) => {
    const [position, setPosition] = useState<L.LatLng | null>(
        initialLat !== 0 && initialLng !== 0 ? new L.LatLng(initialLat, initialLng) : null
    );

    const handleLocationSelect = (lat: number, lng: number) => {
        setPosition(new L.LatLng(lat, lng));
        onLocationSelect(lat, lng);
    };

    // If initial props change (e.g. loaded from DB), update local state
    useEffect(() => {
        if (initialLat !== 0 && initialLng !== 0) {
            setPosition(new L.LatLng(initialLat, initialLng));
        }
    }, [initialLat, initialLng]);

    return (
        <div className="h-[300px] w-full rounded-md overflow-hidden relative z-0 ring-2 ring-primary/30 shadow-[0_0_15px_rgba(0,224,208,0.15)]">
            {/* Neon glass border effect with glow */}
            <MapContainer
                center={[initialLat || 51.505, initialLng || -0.09]}
                zoom={13}
                style={{ height: '100%', width: '100%' }}
                className="z-0"
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <LocationMarker onLocationSelect={handleLocationSelect} position={position} />
            </MapContainer>
            {position && (
                <div className="absolute bottom-2 left-2 bg-black/70 backdrop-blur-md px-3 py-1 rounded text-xs text-white font-mono z-[1000] border border-white/10">
                    LAT: {position.lat.toFixed(6)} | LNG: {position.lng.toFixed(6)}
                </div>
            )}
        </div>
    );
};

export default LocationPicker;
