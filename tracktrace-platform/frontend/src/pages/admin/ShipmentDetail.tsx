import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, ApiError } from "../../lib/api";

interface Detail {
  id: string; tracking_number: string; customer: { name: string; email: string | null; phone: string | null };
  origin: string; destination: string; current_location: string | null;
  status_ref: { code: string; label: Record<string, string>; is_problem: boolean };
  estimated_delivery: string | null; actual_delivery: string | null;
  reference_number: string | null; weight_kg: number | null; pieces: number;
  cargo_description: string | null; special_instructions: string | null;
  events: { status: string; status_ref: { label: Record<string, string> }; location: string | null; description: string | null; event_timestamp: string }[];
}
interface StatusOpt { code: string; label: Record<string, string>; }
interface DocumentOut { id: string; filename: string; doc_type: string; size_bytes: number; visible_to_customer: boolean; created_at: string; }

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function ShipmentDetailPage() {
  const { id } = useParams();
  const [data, setData] = useState<Detail | null>(null);
  const [statuses, setStatuses] = useState<StatusOpt[]>([]);
  const [docs, setDocs] = useState<DocumentOut[]>([]);
  const [eventForm, setEventForm] = useState({ status: "", location: "", description: "" });
  const [editForm, setEditForm] = useState({ reference_number: "", weight_kg: "", pieces: 1, cargo_description: "", special_instructions: "" });
  const [error, setError] = useState<string | null>(null);
  const [editMsg, setEditMsg] = useState<string | null>(null);
  const [docMsg, setDocMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [uploadType, setUploadType] = useState("SHIPPING");
  const [visibleToCustomer, setVisibleToCustomer] = useState(false);

  async function load() {
    const d = await api.get<Detail>(`/api/shipments/${id}`);
    setData(d);
    setEventForm((f) => ({ ...f, status: d.status_ref.code }));
    setEditForm({
      reference_number: d.reference_number || "", weight_kg: d.weight_kg?.toString() || "", pieces: d.pieces,
      cargo_description: d.cargo_description || "", special_instructions: d.special_instructions || "",
    });
  }
  async function loadDocs() {
    setDocs(await api.get<DocumentOut[]>(`/api/shipments/${id}/documents`));
  }

  useEffect(() => {
    load();
    loadDocs();
    api.get<StatusOpt[]>("/api/statuses").then(setStatuses);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function submitEvent(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.post(`/api/shipments/${id}/events`, {
        status: eventForm.status || undefined,
        location: eventForm.location || undefined,
        description: eventForm.description || undefined,
      });
      setEventForm((f) => ({ ...f, location: "", description: "" }));
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  async function submitEdit(e: React.FormEvent) {
    e.preventDefault();
    setEditMsg(null);
    try {
      await api.patch(`/api/shipments/${id}`, {
        reference_number: editForm.reference_number || null,
        weight_kg: editForm.weight_kg ? Number(editForm.weight_kg) : null,
        pieces: editForm.pieces,
        cargo_description: editForm.cargo_description || null,
        special_instructions: editForm.special_instructions || null,
      });
      setEditMsg("Saved.");
      await load();
    } catch (err) {
      setEditMsg(err instanceof ApiError ? err.message : "Something went wrong.");
    }
  }

  async function uploadDoc(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const input = e.currentTarget.elements.namedItem("file") as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    setDocMsg(null);
    const form = new FormData();
    form.append("file", file);
    form.append("doc_type", uploadType);
    form.append("visible_to_customer", String(visibleToCustomer));
    try {
      await api.upload(`/api/shipments/${id}/documents`, form);
      input.value = "";
      await loadDocs();
    } catch (err) {
      setDocMsg(err instanceof ApiError ? err.message : "Upload failed.");
    }
  }

  async function deleteDoc(docId: string) {
    await api.del(`/api/documents/${docId}`);
    await loadDocs();
  }

  if (!data) return null;

  return (
    <div style={{ maxWidth: 760 }}>
      <h1 className="mono" style={{ fontSize: "1.4rem" }}>{data.tracking_number}</h1>
      <p style={{ color: "var(--slate-500)" }}>{data.customer.name} · {data.origin} → {data.destination}</p>
      <span className={`status-pill ${data.status_ref.is_problem ? "problem" : ""}`}>{data.status_ref.label.en}</span>

      <h2 style={{ fontSize: "1.1rem", marginTop: 28 }}>Add tracking event</h2>
      {error && <div className="banner banner-error">{error}</div>}
      <form onSubmit={submitEvent} style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end" }}>
        <div className="field" style={{ marginBottom: 0 }}>
          <label>Status</label>
          <select value={eventForm.status} onChange={(e) => setEventForm({ ...eventForm, status: e.target.value })}>
            {statuses.map((s) => <option key={s.code} value={s.code}>{s.label.en}</option>)}
          </select>
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label>Location</label>
          <input value={eventForm.location} onChange={(e) => setEventForm({ ...eventForm, location: e.target.value })} />
        </div>
        <div className="field" style={{ marginBottom: 0, flex: 1 }}>
          <label>Note</label>
          <input value={eventForm.description} onChange={(e) => setEventForm({ ...eventForm, description: e.target.value })} />
        </div>
        <button className="btn btn-primary" type="submit" disabled={busy}>Add event</button>
      </form>

      <h2 style={{ fontSize: "1.1rem", marginTop: 28 }}>History</h2>
      <ol style={{ listStyle: "none", padding: 0, borderLeft: "2px solid var(--line-200)" }}>
        {[...data.events].reverse().map((e, i) => (
          <li key={i} style={{ paddingLeft: 18, paddingBottom: 18, position: "relative" }}>
            <span style={{ position: "absolute", left: -6, top: 4, width: 10, height: 10, borderRadius: "50%", background: "var(-- Track-700)" }} />
            <div style={{ fontWeight: 600 }}>{e.status_ref.label.en}</div>
            {e.location && <div style={{ fontSize: "0.9rem", color: "var(--slate-500)" }}>{e.location}</div>}
            {e.description && <div style={{ fontSize: "0.9rem" }}>{e.description}</div>}
            <div className="mono" style={{ fontSize: "0.8rem", color: "var(--slate-500)" }}>{new Date(e.event_timestamp).toLocaleString()}</div>
          </li>
        ))}
      </ol>

      <h2 style={{ fontSize: "1.1rem", marginTop: 28 }}>Edit shipment details</h2>
      <p style={{ color: "var(--slate-500)", fontSize: "0.85rem" }}>Status, location and ETA are changed above (via a tracking event) so history is preserved. This form edits everything else.</p>
      {editMsg && <div className={`banner ${editMsg === "Saved." ? "banner-success" : "banner-error"}`}>{editMsg}</div>}
      <form onSubmit={submitEdit} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, maxWidth: 480 }}>
        <div className="field"><label>Reference number</label><input value={editForm.reference_number} onChange={(e) => setEditForm({ ...editForm, reference_number: e.target.value })} /></div>
        <div className="field"><label>Weight (kg)</label><input type="number" min={0} step="0.01" value={editForm.weight_kg} onChange={(e) => setEditForm({ ...editForm, weight_kg: e.target.value })} /></div>
        <div className="field"><label>Pieces</label><input type="number" min={1} value={editForm.pieces} onChange={(e) => setEditForm({ ...editForm, pieces: Number(e.target.value) })} /></div>
        <div className="field" style={{ gridColumn: "1 / -1" }}><label>Cargo description</label><textarea rows={2} value={editForm.cargo_description} onChange={(e) => setEditForm({ ...editForm, cargo_description: e.target.value })} /></div>
        <div className="field" style={{ gridColumn: "1 / -1" }}><label>Special instructions</label><textarea rows={2} value={editForm.special_instructions} onChange={(e) => setEditForm({ ...editForm, special_instructions: e.target.value })} /></div>
        <button className="btn btn-secondary" type="submit" style={{ gridColumn: "1 / -1", justifySelf: "start" }}>Save details</button>
      </form>

      <h2 style={{ fontSize: "1.1rem", marginTop: 28 }}>Documents</h2>
      {docMsg && <div className="banner banner-error">{docMsg}</div>}
      <form onSubmit={uploadDoc} style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginBottom: 14 }}>
        <input type="file" name="file" required accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx,.csv,.txt" />
        <select value={uploadType} onChange={(e) => setUploadType(e.target.value)}>
          <option value="SHIPPING">Shipping</option>
          <option value="CUSTOMS">Customs</option>
          <option value="PROOF_OF_DELIVERY">Proof of delivery</option>
          <option value="OTHER">Other</option>
        </select>
        <label style={{ display: "flex", gap: 6, alignItems: "center", fontSize: "0.88rem" }}>
          <input type="checkbox" checked={visibleToCustomer} onChange={(e) => setVisibleToCustomer(e.target.checked)} /> Visible to customer
        </label>
        <button className="btn btn-secondary" type="submit">Upload</button>
      </form>
      {docs.length === 0 && <p style={{ color: "var(--slate-500)" }}>No documents uploaded yet.</p>}
      {docs.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0 }}>
          {docs.map((d) => (
            <li key={d.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: "1px solid var(--line-200)" }}>
              <span>{d.filename} <span style={{ color: "var(--slate-500)", fontSize: "0.82rem" }}>({d.doc_type}{d.visible_to_customer ? ", visible to customer" : ""})</span></span>
              <span style={{ display: "flex", gap: 12 }}>
                <a href={`${API_URL}/api/documents/${d.id}/download`} target="_blank" rel="noreferrer">Download</a>
                <button className="btn-secondary" style={{ border: "none", background: "none", color: "var(--danger-600)", cursor: "pointer" }} onClick={() => deleteDoc(d.id)}>Delete</button>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
