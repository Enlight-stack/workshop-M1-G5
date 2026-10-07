import { useEffect, useState } from "react";

const API = "https://192.168.1.10"; // adresse du serveur (.10)

const TYPES = {
  personne: { label: "Personne détectée", level: "info" },
  anomalie: { label: "Anomalie caméra", level: "alerte" },
  temperature: { label: "Température élevée", level: "alerte" },
};

const COLORS = { Normal: "#16a34a", Alerte: "#dc2626" };

export default function App() {
  const [events, setEvents] = useState([]);
  const [mesures, setMesures] = useState({ temperature: 22.5, humidite: 45 });
  const [alerte, setAlerte] = useState(false);

  // Récupère les données de l'API ; si elle est absente, on garde la simulation
  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch(`${API}/api/status`);
        const d = await r.json();
        if (d.mesures) setMesures(d.mesures);
        if (Array.isArray(d.events)) setEvents(d.events);
        setAlerte((d.events ?? []).some((e) => e.level === "alerte" && e.actif));
      } catch {
        /* API indisponible : mode simulation */
      }
    };
    load();
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, []);

  const simuler = (type) => {
    const { label, level } = TYPES[type];
    setEvents((e) => [
      { id: Date.now(), label, level, heure: new Date().toLocaleTimeString("fr-FR") },
      ...e,
    ]);
    if (level === "alerte") setAlerte(true);
    if (type === "temperature") setMesures((m) => ({ ...m, temperature: 41.2 }));
  };

  const reinitialiser = () => {
    setAlerte(false);
    setEvents([]);
    setMesures({ temperature: 22.5, humidite: 45 });
  };

  const statut = alerte ? "Alerte" : "Normal";

  return (
    <div style={s.page}>
      <h1 style={{ margin: 0 }}>Sentinel-X</h1>

      <div style={{ ...s.banner, background: COLORS[statut] }}>{statut}</div>

      <div style={s.row}>
        <Card titre="Température" valeur={`${mesures.temperature} °C`} />
        <Card titre="Humidité" valeur={`${mesures.humidite} %`} />
        <Card
          titre="Personnes détectées"
          valeur={events.filter((e) => e.label === TYPES.personne.label).length}
        />
      </div>

      <h2>Simuler un événement</h2>
      <div style={s.row}>
        {Object.entries(TYPES).map(([k, v]) => (
          <button key={k} style={s.btn} onClick={() => simuler(k)}>
            {v.label}
          </button>
        ))}
        <button style={{ ...s.btn, background: "#475569" }} onClick={reinitialiser}>
          Réinitialiser
        </button>
      </div>

      <h2>Historique</h2>
      {events.length === 0 && <p style={{ color: "#64748b" }}>Aucun événement.</p>}
      <ul style={{ padding: 0, listStyle: "none" }}>
        {events.map((e) => (
          <li key={e.id} style={s.item}>
            <span style={{ color: e.level === "alerte" ? "#dc2626" : "#2563eb", fontWeight: 600 }}>
              {e.level.toUpperCase()}
            </span>{" "}
            {e.label} <span style={{ float: "right", color: "#64748b" }}>{e.heure}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Card({ titre, valeur }) {
  return (
    <div style={s.card}>
      <div style={{ color: "#64748b", fontSize: 14 }}>{titre}</div>
      <div style={{ fontSize: 28, fontWeight: 700 }}>{valeur}</div>
    </div>
  );
}

const s = {
  page: { maxWidth: 800, margin: "0 auto", padding: 24, fontFamily: "system-ui, sans-serif" },
  banner: { color: "#fff", padding: 16, borderRadius: 8, margin: "16px 0", fontSize: 22, fontWeight: 700, textAlign: "center" },
  row: { display: "flex", gap: 12, flexWrap: "wrap" },
  card: { flex: 1, minWidth: 160, padding: 16, border: "1px solid #e2e8f0", borderRadius: 8 },
  btn: { padding: "10px 16px", border: 0, borderRadius: 6, background: "#2563eb", color: "#fff", cursor: "pointer" },
  item: { padding: 10, borderBottom: "1px solid #e2e8f0" },
};