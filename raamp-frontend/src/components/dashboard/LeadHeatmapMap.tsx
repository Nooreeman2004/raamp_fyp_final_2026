import React, { useState } from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";
import { Card } from "@/components/ui/card";

// Example mock data
const regions = [
  { name: "DHA", leadScore: 95, color: "#e3342f" }, // red
  { name: "Other Region", leadScore: 50, color: "#22c55e" }, // green
];

// Simple world map topojson (can be replaced with Pakistan or city map)
const geoUrl = "https://raw.githubusercontent.com/deldersveld/topojson/master/world-countries.json";

const regionColor = (name: string) => {
  if (name === "DHA") return "#e3342f";
  return "#22c55e";
};

export default function LeadHeatmapMap({ onRegionClick }: { onRegionClick: (region: any) => void }) {
  const [tooltip, setTooltip] = useState<string | null>(null);
  const [hoveredRegion, setHoveredRegion] = useState<string | null>(null);

  return (
    <div className="relative w-full h-[320px] md:h-[400px]">
      <ComposableMap
        projection="geoMercator"
        width={500}
        height={320}
        style={{ width: "100%", height: "100%" }}
      >
        <Geographies geography={geoUrl}>
          {({ geographies }) =>
            geographies.map((geo) => {
              // For demo, highlight "Pakistan" as DHA, rest as green
              const regionName = geo.properties.NAME === "Pakistan" ? "DHA" : "Other Region";
              const region = regions.find((r) => r.name === regionName) || regions[1];
              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill={region.color}
                  stroke="#fff"
                  style={{
                    default: { outline: "none" },
                    hover: { outline: "none", opacity: 0.8 },
                    pressed: { outline: "none" },
                  }}
                  onMouseEnter={() => {
                    setTooltip(`${region.name}: Lead Score ${region.leadScore}`);
                    setHoveredRegion(region.name);
                  }}
                  onMouseLeave={() => {
                    setTooltip(null);
                    setHoveredRegion(null);
                  }}
                  onClick={() => onRegionClick(region)}
                />
              );
            })
          }
        </Geographies>
      </ComposableMap>
      {/* Tooltip */}
      {tooltip && (
        <div className="absolute left-1/2 top-2 z-10 -translate-x-1/2 bg-card text-card-foreground px-3 py-1 rounded shadow-lg text-xs">
          {tooltip}
        </div>
      )}
      {/* Legend */}
      <div className="absolute bottom-2 left-2 flex items-center space-x-4 bg-background/80 px-3 py-1 rounded shadow text-xs">
        <div className="flex items-center space-x-1">
          <span className="inline-block w-3 h-3 rounded-full bg-[#22c55e] border border-muted" />
          <span>Normal</span>
        </div>
        <div className="flex items-center space-x-1">
          <span className="inline-block w-3 h-3 rounded-full bg-[#e3342f] border border-muted" />
          <span>High-Intent (DHA)</span>
        </div>
      </div>
    </div>
  );
}
