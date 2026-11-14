import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet-draw';
import '../styles/MapAoiPicker.css';

const DEFAULT_BOUNDS = [[-90, -180], [90, 180]];
const PRESET_AOIS = {
  california: { label: 'California', bounds: [[32.5, -125], [42, -114]] },
  'north-india': { label: 'North India', bounds: [[22, 70], [32, 85]] },
  amazon: { label: 'Amazon Basin', bounds: [[-15, -80], [5, -50]] },
  'australia-nsw': { label: 'Australia NSW', bounds: [[-38, 140], [-28, 155]] },
  'east-siberia': { label: 'East Siberia', bounds: [[50, 110], [70, 140]] }
};

export default function MapAoiPicker({ onAoiSelect, selectedAoi }) {
  const mapRef = useRef(null);
  const mapContainer = useRef(null);
  const drawnItemsRef = useRef(null);

  // Initialize map once
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = L.map(mapContainer.current, {
      center: [0, 0],
      zoom: 2,
      maxBounds: DEFAULT_BOUNDS,
      maxBoundsViscosity: 1.0
    });
    mapRef.current = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    drawnItemsRef.current = drawnItems;

    const dc = new L.Control.Draw({
      position: 'topleft',
      draw: {
        polygon: { allowIntersection: false, showArea: true },
        rectangle: true,
        circle: false,
        marker: false,
        circlemarker: false,
        polyline: false
      },
      edit: { featureGroup: drawnItems, remove: true }
    });
    map.addControl(dc);

    // Every processed artifact belongs to one of the five preset regions. For
    // an arbitrary drawn area, use the nearest preset's data instead of
    // requesting a non-existent /aoi/custom endpoint.
    const nearestAoiId = (bounds) => {
      const center = bounds.getCenter();
      let best = null;
      let bestDistance = Infinity;
      for (const [id, meta] of Object.entries(PRESET_AOIS)) {
        const distance = map.distance(center, L.latLngBounds(meta.bounds).getCenter());
        if (distance < bestDistance) {
          best = id;
          bestDistance = distance;
        }
      }
      return best;
    };

    map.on(L.Draw.Event.CREATED, (e) => {
      const layer = e.layer;
      drawnItems.clearLayers();
      drawnItems.addLayer(layer);
      onAoiSelect(nearestAoiId(layer.getBounds()));
    });

    map.on(L.Draw.Event.EDITED, (e) => {
      e.layers.eachLayer((layer) => {
        onAoiSelect(nearestAoiId(layer.getBounds()));
      });
    });

    map.on(L.Draw.Event.DELETED, () => {
      // keep selection unchanged
    });

    return () => map.remove();
  }, [onAoiSelect]);

  // Update drawn preset rectangle when selectedAoi changes
  useEffect(() => {
    const map = mapRef.current;
    const drawnItems = drawnItemsRef.current;
    if (!map || !drawnItems) return;

    drawnItems.clearLayers();
    if (selectedAoi && PRESET_AOIS[selectedAoi]) {
      const b = PRESET_AOIS[selectedAoi].bounds;
      const rect = L.rectangle(b, { color: '#f0883e', weight: 2, dashArray: '5,5' });
      drawnItems.addLayer(rect);
      map.fitBounds(rect.getBounds());
      // ensure map renders correctly after container size changes
      setTimeout(() => map.invalidateSize(), 0);
    }
  }, [selectedAoi]);

  return (
    <div className="map-aoi-picker">
      <div ref={mapContainer} className="map-container" />
      <div className="map-hint">
        Draw a rectangle/polygon on the map. Drawn areas use the nearest processed preset region; five preset regions are available above.
      </div>
    </div>
  );
}