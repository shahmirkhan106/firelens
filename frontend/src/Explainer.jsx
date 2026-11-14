import React, { useState } from "react";

export function Info({ title, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className={`info ${open ? "open" : ""}`}>
      <button
        className="info-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <span className="info-icon">i</span>
        <span className="info-label">{title}</span>
        <span className="info-caret">{open ? "−" : "+"}</span>
      </button>
      {open && <div className="info-body">{children}</div>}
    </div>
  );
}

export function Figure({ title, subtitle, explain, legend, children, note, download }) {
  return (
    <figure className="fig">
      <figcaption>
        <h3>{title}</h3>
        {subtitle && <p className="fig-sub">{subtitle}</p>}
        {download && (
          <a
            className="fig-download"
            href={download.url}
            download={download.filename}
            title={download.title || "Download CSV"}
          >
            ⬇ CSV
          </a>
        )}
      </figcaption>
      {explain && <Info title="What am I looking at?">{explain}</Info>}
      {legend}
      {children}
      {note && <p className="fig-note">{note}</p>}
    </figure>
  );
}

export function Stat({ label, value, sub, tone }) {
  return (
    <div className={`stat ${tone || ""}`}>
      <div className="stat-val">{value}</div>
      <div className="stat-label">{label}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

const WEEK_ABBR = ["", "Jan 1", "Jan 8", "Jan 15", "Jan 22", "Jan 29", "Feb 5", "Feb 12", "Feb 19", "Feb 26", "Mar 4", "Mar 11", "Mar 18", "Mar 25", "Apr 1", "Apr 8", "Apr 15", "Apr 22", "Apr 29", "May 6", "May 13", "May 20", "May 27", "Jun 3", "Jun 10", "Jun 17", "Jun 24", "Jul 1", "Jul 8", "Jul 15", "Jul 22", "Jul 29", "Aug 5", "Aug 12", "Aug 19", "Aug 26", "Sep 2", "Sep 9", "Sep 16", "Sep 23", "Sep 30", "Oct 7", "Oct 14", "Oct 21", "Oct 28", "Nov 4", "Nov 11", "Nov 18", "Nov 25", "Dec 2", "Dec 9", "Dec 16", "Dec 23", "Dec 30"];

export function weekLabel(w) {
  if (w == null) return "—";
  return WEEK_ABBR[w] || `Week ${w}`;
}

export function weekRangeLabel(w, span = 1) {
  if (w == null) return "—";
  const end = Math.min(53, w + span - 1);
  return end === w ? weekLabel(w) : `${weekLabel(w)} – ${weekLabel(end)}`;
}

/* Robust upper bound for a colour/axis scale.
   Scaling to the raw maximum looks correct and is useless in practice: fire
   counts are heavy-tailed, so one extreme day sets the ceiling and 99% of the
   record collapses into the palest colour. Cap at the 95th percentile of
   non-zero values instead and clamp anything above it, which keeps the bulk of
   the data legible and still shows the outliers as saturated. */
export function robustMax(values, percentile = 0.95) {
  const v = (Array.isArray(values) ? values.flat(Infinity) : [])
    .filter((n) => Number.isFinite(n) && n > 0)
    .sort((a, b) => a - b);
  if (!v.length) return 1;
  const i = Math.min(v.length - 1, Math.max(0, Math.floor(v.length * percentile)));
  return Math.max(1, v[i]);
}

export const fmt = (n) =>
  n == null || Number.isNaN(n)
    ? "—"
    : n >= 1e6
    ? `${(n / 1e6).toFixed(1)}M`
    : n >= 1e4
    ? `${Math.round(n / 1e3)}k`
    : Math.round(n).toLocaleString();
