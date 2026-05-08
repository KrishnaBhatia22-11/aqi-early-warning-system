import { useEffect, useState } from "react";
import { MapContainer, TileLayer, GeoJSON, Marker, Tooltip } from "react-leaflet";
import L from "leaflet";
import { aqiCategory } from "../utils/aqiCategory";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl: null, iconUrl: null, shadowUrl: null });

const CITY_COORDS = {
  "Delhi":              [28.6139, 77.2090],
  "Mumbai":             [19.0760, 72.8777],
  "Bengaluru":          [12.9716, 77.5946],
  "Chennai":            [13.0827, 80.2707],
  "Kolkata":            [22.5726, 88.3639],
  "Hyderabad":          [17.3850, 78.4867],
  "Ahmedabad":          [23.0225, 72.5714],
  "Jaipur":             [26.9124, 75.7873],
  "Lucknow":            [26.8467, 80.9462],
  "Kanpur":             [26.4499, 80.3319],
  "Patna":              [25.5941, 85.1376],
  "Bhopal":             [23.2599, 77.4126],
  "Pune":               [18.5204, 73.8567],
  "Nagpur":             [21.1458, 79.0882],
  "Surat":              [21.1702, 72.8311],
  "Visakhapatnam":      [17.6868, 83.2185],
  "Coimbatore":         [11.0168, 76.9558],
  "Kochi":              [ 9.9312, 76.2673],
  "Indore":             [22.7196, 75.8577],
  "Chandigarh":         [30.7333, 76.7794],
  "Amritsar":           [31.6340, 74.8723],
  "Guwahati":           [26.1445, 91.7362],
  "Bhubaneswar":        [20.2961, 85.8245],
  "Thiruvananthapuram": [ 8.5241, 76.9366],
  "Varanasi":           [25.3176, 82.9739],
  "Ranchi":             [23.3441, 85.3096],
};

const GEOJSON_URL =
  "https://raw.githubusercontent.com/geohacker/india/master/state/india_telengana.geojson";

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

export default function IndiaMap({ cities, selected, onSelect, onCityClick }) {
  const [geoData, setGeoData] = useState(null);

  useEffect(() => {
    fetch(GEOJSON_URL).then(r => r.json()).then(setGeoData).catch(() => {});
  }, []);

  return (
    <div className="india-map-wrap">
      <MapContainer
        center={[22.5, 82.0]}
        zoom={5}
        zoomSnap={0.5}
        scrollWheelZoom={false}
        style={{ width: "100%", height: "100%" }}
        className="leaflet-dark-map"
      >
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
