import { useEffect, useState } from "react";

const API = "https://192.168.1.10";
const SEUIL = 35;
const TYPES = {
  personne: { label: "Personne détectée", level: "info" },
  anomalie: { label: "Anomalie caméra", level: "alerte" },
  temperature: { label: "Température élevée", level: "alerte" },
};
const heure = () => new Date().toLocaleTimeString("fr-FR");

export default function App() {
  const [events, setEvents] = useState([]);
  const [mesures, setMesures] = useState({ temperature: 22.5, humidite: 45 });
  const [courbe, setCourbe] = useState([22.5]);
  const [enLigne, setEnLigne] = useState(false);
  const [auto, setAuto] = useState(false);
  const [filtre, setFiltre] = useState("tous");

  const ajouter = (label, level) =>
    setEvents((e) =>
      [{ id: Date.now() + Math.random(), label, level, heure: heure(), lu: false }, ...e].slice(0, 50)
    );

  const majTemp = (t) => {
    setMesures((m) => ({ ...m, temperature: t }));
    setCourbe((c) => [...c, t].slice(-20));
  };

  // Lecture de l'API
  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch(`${API}/api/status`);
        const d = await r.json();
        setEnLigne(true);
        if (d.mesures) {
          setMesures(d.mesures);
          setCourbe((c) => [...c, d.mesures.temperature].slice(-20));
        }
        if (Array.isArray(d.events)) setEvents(d.events.map((e, i) => ({ id: e.id ?? i, lu: false, ...e })));
      } catch {
        setEnLigne(false);
      }
    };
    load();
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, []);

  // Simulation automatique (hors ligne uniquement)
  useEffect(() => {
    if (!auto || enLigne) return;
    const t = setInterval(() => {
      majTemp(+(18 + Math.random() * 22).toFixed(1));
      if (Math.random() < 0.3) ajouter(TYPES.personne.label, "info");
    }, 2000);
    return () => clearInterval(t);
  }, [auto, enLigne]);

  const simuler = (k) => {
    ajouter(TYPES[k].label, TYPES[k].level);
    if (k === "temperature") majTemp(41.2);
  };
  const acquitter = () => setEvents((e) => e.map((x) => ({ ...x, lu: true })));
  const reinit = () => { setEvents([]); setMesures({ temperature: 22.5, humidite: 45 }); setCourbe([22.5]); };

  const alerte = mesures.temperature >= SEUIL || events.some((e) => e.level === "alerte" && !e.lu);
  const nbPers = events.filter((e) => e.label === TYPES.personne.label).length;
  const liste = events.filter((e) => filtre === "tous" || e.level === filtre);

  // Courbe SVG (échelle 10 à 50 °C)
  const pts = courbe
    .map((v, i) => `${(i / Math.max(courbe.length - 1, 1)) * 300},${80 - ((v - 10) / 40) * 80}`)
    .join(" ");

  return (
    <div className="app">
      <style>{css}</style>

      <header>
        <h1>🛡️ Sentinel-X</h1>
        <span className={`pill ${enLigne ? "ok" : "off"}`}>
          {enLigne ? "● API en ligne" : "● Mode simulation"}
        </span>
      </header>

      <div className={`banner ${alerte ? "alerte" : "normal"}`}>
        {alerte ? "⚠ ALERTE" : "✔ Normal"}
        {alerte && <button onClick={acquitter}>Acquitter</button>}
      </div>

      <section className="grid">
        <Card titre="Température" valeur={`${mesures.temperature} °C`} rouge={mesures.temperature >= SEUIL} />
        <Card titre="Humidité" valeur={`${mesures.humidite} %`} />
        <Card titre="Personnes détectées" valeur={nbPers} />
        <Card titre="Alertes actives" valeur={events.filter((e) => e.level === "alerte" && !e.lu).length} rouge />
      </section>

      <section className="panel">
        <h2>Température (20 dernières mesures)</h2>
        <svg viewBox="0 0 300 80" preserveAspectRatio="none" width="100%" height="120">
          <line x1="0" x2="300" y1={80 - ((SEUIL - 10) / 40) * 80} y2={80 - ((SEUIL - 10) / 40) * 80} stroke="#ef4444" strokeDasharray="4" />
          <polyline points={pts} fill="none" stroke="#38bdf8" strokeWidth="2" vectorEffect="non-scaling-stroke" />
        </svg>
        <small>Ligne rouge : seuil {SEUIL} °C</small>
      </section>

      <section className="panel">
        <h2>Simulation</h2>
        <div className="row">
          {Object.entries(TYPES).map(([k, v]) => (
            <button key={k} onClick={() => simuler(k)}>{v.label}</button>
          ))}
          <button className={auto ? "on" : "gris"} onClick={() => setAuto(!auto)}>
            Auto : {auto ? "ON" : "OFF"}
          </button>
          <button className="gris" onClick={reinit}>Réinitialiser</button>
        </div>
      </section>

      <section className="panel">
        <div className="row between">
          <h2>Historique ({liste.length})</h2>
          <div className="row">
            {["tous", "alerte", "info"].map((f) => (
              <button key={f} className={filtre === f ? "on" : "gris"} onClick={() => setFiltre(f)}>{f}</button>
            ))}
          </div>
        </div>
        {liste.length === 0 && <p className="vide">Aucun événement.</p>}
        <ul>
          {liste.map((e) => (
            <li key={e.id} className={e.lu ? "lu" : ""}>
              <b className={e.level}>{e.level.toUpperCase()}</b> {e.label}
              <span>{e.heure}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function Card({ titre, valeur, rouge }) {
  return (
    <div className="card">
      <div className="t">{titre}</div>
      <div className="v" style={rouge ? { color: "#f87171" } : null}>{valeur}</div>
    </div>
  );
}

const css = `
body{margin:0;background:#0f172a;color:#e2e8f0;font-family:system-ui,sans-serif}
.app{max-width:900px;margin:0 auto;padding:24px}
header{display:flex;justify-content:space-between;align-items:center}
h1{margin:0;font-size:26px} h2{font-size:16px;margin:0 0 12px;color:#94a3b8}
.pill{padding:4px 12px;border-radius:99px;font-size:13px}
.pill.ok{background:#14532d;color:#86efac} .pill.off{background:#78350f;color:#fcd34d}
.banner{margin:16px 0;padding:16px;border-radius:10px;font-size:22px;font-weight:700;text-align:center;position:relative}
.banner.normal{background:#16a34a} .banner.alerte{background:#dc2626;animation:p 1s infinite}
.banner button{position:absolute;right:12px;top:12px;font-size:13px;background:#fff;color:#dc2626}
@keyframes p{50%{opacity:.7}}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.card,.panel{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:16px}
.panel{margin-top:16px} .t{color:#94a3b8;font-size:14px} .v{font-size:30px;font-weight:700}
.row{display:flex;gap:8px;flex-wrap:wrap} .between{justify-content:space-between;align-items:center}
button{padding:8px 14px;border:0;border-radius:6px;background:#2563eb;color:#fff;cursor:pointer;font-size:14px}
button:hover{filter:brightness(1.15)} button.gris{background:#475569} button.on{background:#0ea5e9}
ul{list-style:none;padding:0;margin:0}
li{padding:10px 0;border-bottom:1px solid #334155} li.lu{opacity:.5}
li span{float:right;color:#94a3b8} .alerte{color:#f87171} .info{color:#60a5fa}
.vide,small{color:#64748b}
`;
