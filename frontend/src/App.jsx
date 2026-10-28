import React, { useEffect, useState } from "react";
import SensorComparison from "./SensorComparison";
import CalendarHeatmap from "./CalendarHeatmap";
import ClimatologyChart from "./ClimatologyChart";
import PeakSeasonChart from "./PeakSeasonChart";
import AnomalyList from "./AnomalyList";
import ErrorBoundary from "./ErrorBoundary";
import { Info } from "./Explainer";
import MapAoiPicker from "./components/MapAoiPicker";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "/api";

const AOI_META = {
  california: { label: "California", sub: "USA · Mediterranean fire regime" },
  "north-india": { label: "North India", sub: "Punjab/Haryana · crop-residue burning" },
  amazon: { label: "Amazon Basin", sub: "Brazil · equatorial, year-round" },
  "australia-nsw": { label: "Australia NSW", sub: "Southeast Australia · temperate" },
  "east-siberia": { label: "East Siberia", sub: "Russia · boreal, short intense summer" },
};

const TABS = [
  { id: "compare", label: "Why harmonize", ep: "summary" },
  { id: "calendar", label: "Calendar", ep: "calendar" },
  { id: "climatology", label: "Typical season", ep: "climatology" },
  { id: "season", label: "Season timing", ep: "peak-season" },
  { id: "anomalies", label: "Unusual weeks", ep: "anomalies" },
];

function useFetch(path) {
  const [state, setState] = useState({ path: null, data: null, error: null });
  useEffect(() => {
    if (!path) return;
    let live = true;
    setState({ path, data: null, error: null });
    fetch(`${API}${path}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${r.status}`))))
      .then((d) => live && setState({ path, data: d, error: null }))
      .catch((e) => live && setState({ path, data: null, error: e.message }));
    return () => {
      live = false;
    };
  }, [path]);
  // Only expose data that belongs to the CURRENT path. Without this, switching
  // tabs renders the new chart with the previous tab's payload for one frame,
  // which crashes any chart that expects a different shape.
  const current = state.path === path;
  return { data: current ? state.data : null, error: current ? state.error : null };
}

// Deep links: /?aoi=amazon&tab=calendar. Lets a link (or a screenshot run) open
// a specific region/tab straight away, and keeps the URL shareable as the user
// navigates.
const params = new URLSearchParams(window.location.search);
const initialAoi = AOI_META[params.get("aoi")] ? params.get("aoi") : "california";
const initialTab = TABS.some((t) => t.id === params.get("tab"))
  ? params.get("tab")
  : "compare";

export default function App() {
  const [aoi, setAoi] = useState(initialAoi);
  const [tab, setTab] = useState(initialTab);
  const { data: aois } = useFetch("/aois");
  const list = aois?.aois || Object.keys(AOI_META);
  const ep = TABS.find((t) => t.id === tab)?.ep;
  const view = useFetch(`/aoi/${aoi}/${ep}`);
  const comparisonTs = useFetch(tab === "compare" ? `/aoi/${aoi}/comparison` : null);

  useEffect(() => {
    window.history.replaceState(null, "", `?aoi=${aoi}&tab=${tab}`);
  }, [aoi, tab]);

  const meta = AOI_META[aoi] || { label: aoi, sub: "" };

  return (
    <div className="app">
      <header className="head">
        <div className="head-main">
          <h1>
            Fire<span>Lens</span>
          </h1>
          <p className="tagline">
            One continuous fire record from two different satellites — a burning-activity
            calendar you can actually trust across the 2012 sensor change.
          </p>
        </div>
        <Info title="How to read this app">
          <p>
            Pick a region, then work through the tabs. Each chart has a{" "}
            <b>“What am I looking at?”</b> button explaining exactly what it shows and how
            to interpret it — hover or click any of them.
          </p>
          <p>
            Start with <b>Why harmonize</b>: it demonstrates the sensor problem and how
            FireLens removes it. Everything after that is the cleaned-up result.
          </p>
          <p>
            Source data: NASA FIRMS active-fire hotspots (MODIS C6.1 1&nbsp;km and VIIRS
            375&nbsp;m), 2001 to present.
          </p>
        </Info>
      </header>

      <section className="picker">
        <div className="picker-label">Region</div>
        <div className="chips">
          {list.map((a) => (
            <button
              key={a}
              className={`chip ${a === aoi ? "active" : ""}`}
              onClick={() => setAoi(a)}
            >
              <b>{(AOI_META[a] || {}).label || a}</b>
              <span>{(AOI_META[a] || {}).sub || ""}</span>
            </button>
          ))}
        </div>
        <MapAoiPicker selectedAoi={aoi} onAoiSelect={setAoi} />
      </section>

      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={tab === t.id ? "active" : ""}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="panel">
        {view.error && <div className="load err">Could not load this view ({view.error}).</div>}

        {!view.data && !view.error && <div className="load">Loading…</div>}

        {view.data && tab === "compare" && !comparisonTs.data && (
          <div className="load">Loading comparison…</div>
        )}

        {view.data && tab === "compare" && comparisonTs.data && (
          <ErrorBoundary resetKey={`${aoi}-${tab}`}>
            <SensorComparison comparison={comparisonTs.data} summary={view.data} aoi={aoi} />
          </ErrorBoundary>
        )}
        {view.data && tab === "calendar" && (
          <ErrorBoundary resetKey={`${aoi}-${tab}`}>
            <CalendarHeatmap data={view.data} />
          </ErrorBoundary>
        )}
        {view.data && tab === "climatology" && (
          <ErrorBoundary resetKey={`${aoi}-${tab}`}>
            <ClimatologyChart data={view.data} aoi={aoi} />
          </ErrorBoundary>
        )}
        {view.data && tab === "season" && (
          <ErrorBoundary resetKey={`${aoi}-${tab}`}>
            <PeakSeasonChart data={view.data} aoi={aoi} />
          </ErrorBoundary>
        )}
        {view.data && tab === "anomalies" && (
          <ErrorBoundary resetKey={`${aoi}-${tab}`}>
            <AnomalyList data={view.data} aoi={aoi} />
          </ErrorBoundary>
        )}
      </main>

      <footer>
        <span>
          <b>{meta.label}</b> · {meta.sub}
        </span>
        <span>
          NASA FIRMS (MODIS C6.1 + VIIRS 375&nbsp;m) · harmonized on a ~1&nbsp;km² H3 grid ·
          2001 → present
        </span>
      </footer>
    </div>
  );
}
