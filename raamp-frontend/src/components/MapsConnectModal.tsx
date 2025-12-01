import React, { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/services/api';

type Place = {
  place_id: string;
  name: string;
  formatted_address?: string;
  lat?: number;
  lng?: number;
};

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onConnected: (payload: { place_id: string; name: string; formatted_address?: string; lat?: number; lng?: number }) => void;
};

export default function MapsConnectModal({ isOpen, onClose, onConnected }: Props) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Place[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<Place | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      setQuery('');
      setResults([]);
      setSelected(null);
    }
  }, [isOpen]);

  const doSearch = async (q: string) => {
    if (!q || q.trim().length < 2) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      // Use onboarding maps search endpoint
      const res: any = await apiClient.post('/profile/onboarding/maps/search', { query: q.trim() });
      // expect res.data.results or res.results depending on client adapter
      setResults((res && (res.data?.results || res.results)) || []);
    } catch (err: any) {
      console.error('Search error', err);
      alert('Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchDetails = async (place_id: string) => {
    setDetailsLoading(true);
    try {
      // Use onboarding maps confirm endpoint to get canonical details
      const res: any = await apiClient.post('/profile/onboarding/maps/confirm', { place_id });
      const data = res && (res.data || res);
      setSelected({
        place_id: data.place_id,
        name: data.name,
        formatted_address: data.formatted_address || data.address,
        lat: data.lat,
        lng: data.lng,
      });
    } catch (err: any) {
      console.error('Details error', err);
      alert('Failed to load place details');
    } finally {
      setDetailsLoading(false);
    }
  };

  const confirm = async () => {
    if (!selected) return;
    try {
      const payload = {
        place_id: selected.place_id,
        name: selected.name,
        address: selected.formatted_address,
        lat: selected.lat,
        lng: selected.lng,
      };
      // Save via maps save endpoint in onboarding router
      await apiClient.post('/profile/onboarding/maps/save', payload);
      onConnected({ ...payload, formatted_address: selected.formatted_address, lat: selected.lat, lng: selected.lng });
      onClose();
    } catch (err: any) {
      console.error('Connect error', err);
      alert('Failed to connect place. Please try again.');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card p-6 rounded-lg w-full max-w-2xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold">Connect Google Maps</h3>
          <Button variant="ghost" onClick={onClose}>Close</Button>
        </div>
        {!selected && (
          <div>
            <div className="flex gap-2 mb-4">
              <input
                className="flex-1 px-3 py-2 border border-input bg-background rounded-md text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Search for your business (e.g. 'Corner Cafe, New York')"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  if (e.target.value.length >= 2) {
                    doSearch(e.target.value);
                  } else {
                    setResults([]);
                  }
                }}
              />
              <Button onClick={() => doSearch(query)} disabled={loading}>Search</Button>
            </div>

            <div className="space-y-2 max-h-96 overflow-auto">
              {loading && <div className="text-center py-4 text-muted-foreground">Searching…</div>}
              {!loading && query.length >= 2 && results.length === 0 && (
                <div className="text-sm text-muted-foreground text-center py-4">
                  No results found. Try a different search term.
                </div>
              )}
              {!loading && query.length < 2 && results.length === 0 && (
                <div className="text-sm text-muted-foreground text-center py-4">
                  Enter at least 2 characters to search
                </div>
              )}
              {results.map((r) => (
                <div key={r.place_id} className="p-3 bg-muted/50 rounded flex justify-between items-center hover:bg-muted transition-colors">
                  <div className="flex-1">
                    <div className="font-semibold">{r.name}</div>
                    <div className="text-sm text-muted-foreground">{r.formatted_address}</div>
                  </div>
                  <div>
                    <Button size="sm" onClick={() => fetchDetails(r.place_id)}>Select</Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {selected && (
          <div>
            <h4 className="font-semibold mb-2">Confirm Location</h4>
            <div className="mb-3">
              <div className="font-bold">{selected.name}</div>
              <div className="text-sm text-muted-foreground">{selected.formatted_address}</div>
            </div>

            {/* Map preview: use OpenStreetMap iframe as a lightweight Leaflet-free fallback */}
            {selected.lat && selected.lng ? (
              <div className="mb-3 w-full h-56">
                <iframe
                  title="map-preview"
                  width="100%"
                  height="100%"
                  frameBorder={0}
                  src={`https://www.openstreetmap.org/export/embed.html?bbox=${selected.lng - 0.002}%2C${selected.lat - 0.002}%2C${selected.lng + 0.002}%2C${selected.lat + 0.002}&layer=mapnik&marker=${selected.lat}%2C${selected.lng}`}
                />
                <div className="text-xs text-muted-foreground mt-1">Map preview (OpenStreetMap)</div>
              </div>
            ) : (
              <div className="mb-3 text-sm text-muted-foreground">No coordinates available for preview.</div>
            )}

            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setSelected(null)}>Back</Button>
              <Button onClick={confirm} disabled={detailsLoading}>This is my business</Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}