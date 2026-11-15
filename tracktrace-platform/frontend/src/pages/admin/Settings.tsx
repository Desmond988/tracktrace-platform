import { useEffect, useState } from "react";
import { api } from "../../lib/api";

export default function Settings() {
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [saved, setSaved] = useState(false);

  useEffect(() => { api.get<{ values: Record<string, unknown> }>("/api/admin/settings").then((d) => setValues(d.values)); }, []);

  const editable = ["company.name", "company.address", "company.phone", "company.email", "tracking.prefix"];

  async function save() {
    const payload: Record<string, unknown> = {};
    editable.forEach((k) => (payload[k] = values[k]));
    await api.put("/api/admin/settings", { values: payload });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div style={{ maxWidth: 480 }}>
      <h1 style={{ fontSize: "1.5rem" }}>Company settings</h1>
      {saved && <div className="banner banner-success">Saved.</div>}
      {editable.map((key) => (
        <div className="field" key={key}>
          <label>{key}</label>
          <input value={(values[key] as string) || ""} onChange={(e) => setValues({ ...values, [key]: e.target.value })} />
        </div>
      ))}
      <button className="btn btn-primary" onClick={save}>Save</button>
    </div>
  );
}
