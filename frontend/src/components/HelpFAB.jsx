import { useState } from "react";

const CATS = [
  { c:"#34d27a", n:"Good",         r:"0–50",    d:"Air is clean. Safe for everyone."              },
  { c:"#f5d142", n:"Satisfactory", r:"51–100",  d:"Minor issues for sensitive groups."            },
  { c:"#FFB300", n:"Moderate",     r:"101–200", d:"Children and elderly take care."               },
  { c:"#FF6B00", n:"Poor",         r:"201–300", d:"Health effects for all. Limit outdoor."        },
  { c:"#ef3a4d", n:"Very Poor",    r:"301–400", d:"Serious effects. Stay indoors."                },
  { c:"#c2002a", n:"Severe",       r:"401–500", d:"Emergency conditions. Hazardous."              },
];
const POLS = [
  { n:"PM2.5", d:"Tiny particles that enter the bloodstream"         },
  { n:"PM10",  d:"Coarser dust, affects the respiratory tract"       },
  { n:"NO2",   d:"Traffic emissions, causes lung inflammation"       },
  { n:"CO",    d:"Colorless, odorless — blocks oxygen in blood"      },
  { n:"SO2",   d:"Industrial emissions, triggers asthma"             },
  { n:"O3",    d:"Ground ozone, irritates eyes and lungs"            },
];

function EducationModal({ onClose }) {
  return (
    <div className="edu-overlay" onClick={onClose}>
      <div className="edu-modal" onClick={e => e.stopPropagation()}>
        <button className="edu-close" onClick={onClose}>✕ CLOSE</button>
        <span className="mono" style={{ fontSize: 11, letterSpacing: "0.18em", color: "var(--orange)" }}>EXPLAINER</span>
        <h2 className="edu-title">Understanding AQI</h2>
        <p className="edu-sub">India's National Air Quality Index distills 9 pollutants into a single number from 0–500. The higher the number, the worse the air.</p>
        <div className="edu-section">CATEGORIES</div>
        <div className="edu-cats">
          {CATS.map(c => (
            <div className="edu-cat" key={c.n}>
              <span className="edu-cat-dot" style={{ background: c.c, boxShadow: `0 0 12px ${c.c}` }}></span>
              <span className="edu-cat-name" style={{ color: c.c }}>{c.n}</span>
              <span className="edu-cat-range">{c.r}</span>
              <span className="edu-cat-desc">{c.d}</span>
            </div>
          ))}
        </div>
        <div className="edu-section">POLLUTANTS</div>
        <div className="edu-pollutants">
          {POLS.map(p => (
            <div className="edu-pol" key={p.n}>
              <span className="edu-pol-name">{p.n}</span>
              <span className="edu-pol-desc">{p.d}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function HelpFAB() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button className="help-fab" onClick={() => setOpen(true)} title="What is AQI?">?</button>
      {open && <EducationModal onClose={() => setOpen(false)} />}
    </>
  );
}
