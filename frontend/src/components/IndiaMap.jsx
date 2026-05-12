import { useEffect, useState } from "react";
import { MapContainer, TileLayer, GeoJSON, Marker, Tooltip, useMap } from "react-leaflet";
import L from "leaflet";
import { aqiCategory } from "../utils/aqiCategory";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl: null, iconUrl: null, shadowUrl: null });

const CITY_COORDS = {
  // ── Metro Tier ──────────────────────────────────────────────
  "Delhi":              [28.6139, 77.2090],
  "Mumbai":             [19.0760, 72.8777],
  "Bengaluru":          [12.9716, 77.5946],
  "Chennai":            [13.0827, 80.2707],
  "Kolkata":            [22.5726, 88.3639],
  "Hyderabad":          [17.3850, 78.4867],
  "Ahmedabad":          [23.0225, 72.5714],
  "Pune":               [18.5204, 73.8567],
  // ── Major Cities ────────────────────────────────────────────
  "Jaipur":             [26.9124, 75.7873],
  "Lucknow":            [26.8467, 80.9462],
  "Kanpur":             [26.4499, 80.3319],
  "Patna":              [25.5941, 85.1376],
  "Bhopal":             [23.2599, 77.4126],
  "Nagpur":             [21.1458, 79.0882],
  "Surat":              [21.1702, 72.8311],
  "Indore":             [22.7196, 75.8577],
  "Visakhapatnam":      [17.6868, 83.2185],
  "Chandigarh":         [30.7333, 76.7794],
  "Coimbatore":         [11.0168, 76.9558],
  "Kochi":              [ 9.9312, 76.2673],
  // ── Heritage / Tourist ──────────────────────────────────────
  "Agra":               [27.1767, 78.0081],
  "Varanasi":           [25.3176, 82.9739],
  "Amritsar":           [31.6340, 74.8723],
  "Jodhpur":            [26.2389, 73.0243],
  "Udaipur":            [24.5854, 73.7125],
  "Mysuru":             [12.2958, 76.6394],
  "Pondicherry":        [11.9416, 79.8083],
  // ── Industrial Corridors ────────────────────────────────────
  "Ghaziabad":          [28.6692, 77.4538],
  "Noida":              [28.5355, 77.3910],
  "Faridabad":          [28.4089, 77.3178],
  "Gurugram":           [28.4595, 77.0266],
  "Meerut":             [28.9845, 77.7064],
  "Moradabad":          [28.8386, 78.7733],
  "Ludhiana":           [30.9010, 75.8573],
  "Jalandhar":          [31.3260, 75.5762],
  // ── Tier 2 Growing ──────────────────────────────────────────
  "Bhubaneswar":        [20.2961, 85.8245],
  "Guwahati":           [26.1445, 91.7362],
  "Ranchi":             [23.3441, 85.3096],
  "Raipur":             [21.2514, 81.6296],
  "Dehradun":           [30.3165, 78.0322],
  "Shimla":             [31.1048, 77.1734],
  "Jammu":              [32.7266, 74.8570],
  "Srinagar":           [34.0837, 74.7973],
  "Thiruvananthapuram": [ 8.5241, 76.9366],
  "Madurai":            [ 9.9252, 78.1198],
  "Vijayawada":         [16.5062, 80.6480],
  "Nashik":             [19.9975, 73.7898],
  "Aurangabad":         [19.8762, 75.3433],
  "Kolhapur":           [16.7050, 74.2433],
  "Solapur":            [17.6599, 75.9064],
  "Warangal":           [17.9784, 79.5941],
  "Guntur":             [16.3067, 80.4365],
  "Tiruchirappalli":    [10.7905, 78.7047],
};

const GEOJSON_URLS = [
  "https://raw.githubusercontent.com/datameet/maps/master/Country/india-composite.geojson",
  "https://raw.githubusercontent.com/Subhash9325/GeoJson-Data-of-Indian-States/master/Indian_States",
  "https://raw.githubusercontent.com/geohacker/india/master/state/india_telengana.geojson",
];

const MAX_BOUNDS = [[6.0, 66.0], [40.0, 100.0]];

function makeCityIcon(color) {
  return L.divIcon({
    className: "city-marker-icon",
    html: `<div class="city-marker-wrap">
      <div class="city-pulse-ring" style="border-color:${color}"></div>
      <div class="city-dot" style="background:${color};box-shadow:0 0 8px ${color}88"></div>
    </div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    tooltipAnchor: [0, -14],
  });
}

const GEO_STYLE = {
  fillColor: "#0a1628",
  fillOpacity: 1,
  color: "#22c55e",
  weight: 0.8,
  opacity: 0.25,
};

function onEachFeature(_, layer) {
  layer.on({
    mouseover: e => e.target.setStyle({ fillColor: "#0f2040", color: "#22c55e", opacity: 0.5, weight: 1.2 }),
    mouseout:  e => e.target.setStyle(GEO_STYLE),
  });
}

function MapController() {
  const map = useMap();
  useEffect(() => {
    map.setView([22.5, 80.0], 4.8);
    map.setMaxBounds(MAX_BOUNDS);
  }, [map]);
  return null;
}

export default function IndiaMap({ cities, selected, onSelect, onCityClick }) {
  const [geoData, setGeoData] = useState(null);

  useEffect(() => {
    const tryUrls = async () => {
      for (const url of GEOJSON_URLS) {
        try {
          const r = await fetch(url);
          if (!r.ok) continue;
          const data = await r.json();
          if (data?.type || data?.features?.length) { setGeoData(data); return; }
        } catch {}
      }
    };
    tryUrls();
  }, []);

  return (
    <div className="india-map-wrap">
      <MapContainer
        center={[22.5, 80.0]}
        zoom={4.8}
        zoomSnap={0.1}
        scrollWheelZoom={false}
        maxBounds={MAX_BOUNDS}
        maxBoundsViscosity={0.8}
        style={{ width: "100%", height: "100%" }}
        className="leaflet-dark-map"
      >
        <MapController />
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          maxZoom={19}
        />

        {geoData && (
          <GeoJSON
            key="india"
            data={geoData}
            style={GEO_STYLE}
            onEachFeature={onEachFeature}
          />
        )}

        {cities.map(city => {
          const coords = CITY_COORDS[city.name];
          if (!coords) return null;
          const cat = aqiCategory(city.aqi);
          const stationLabel = city.station_count > 1
            ? `avg of ${city.station_count} stations`
            : null;
          return (
            <Marker
              key={city.name}
              position={coords}
              icon={makeCityIcon(cat.color)}
              eventHandlers={{ click: () => (onCityClick ?? onSelect)?.(city) }}
            >
              <Tooltip
                direction="top"
                offset={[0, -14]}
                opacity={1}
                className="city-tooltip"
              >
                <div className="ct-name mono">{city.name.toUpperCase()}</div>
                <div className="ct-aqi" style={{ color: cat.color }}>{city.aqi}</div>
                <div className="ct-cat" style={{ color: cat.color }}>{cat.name.toUpperCase()}</div>
                {stationLabel && (
                  <div className="ct-stations mono" style={{ color: "rgba(255,255,255,0.5)", fontSize: 10 }}>
                    {stationLabel}
                  </div>
                )}
                <div className="ct-cta mono">Click to explore →</div>
              </Tooltip>
            </Marker>
          );
        })}
      </MapContainer>

      <div className="map-corners">
        <span className="c tl" /><span className="c tr" />
        <span className="c bl" /><span className="c br" />
      </div>
    </div>
  );
}
