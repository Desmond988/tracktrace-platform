import { useEffect, useState } from "react";
import { api } from "../../lib/api";

interface Quote { id: string; reference: string; name: string; email: string; origin: string; destination: string; status: string; created_at: string; }

export default function Quotes() {
  const [items, setItems] = useState<Quote[]>([]);
  useEffect(() => { api.get<{ items: Quote[] }>("/api/quotes?page_size=100").then((d) => setItems(d.items)); }, []);

  async function setStatus(id: string, status: string) {
    await api.patch(`/api/quotes/${id}`, { status });
    setItems((prev) => prev.map((q) => (q.id === id ? { ...q, status } : q)));
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem" }}>Quote requests</h1>
      <table>
        <thead><tr><th>Reference</th><th>Name</th><th>Route</th><th>Status</th><th></th></tr></thead>
        <tbody>
          {items.map((q) => (
            <tr key={q.id}>
              <td className="mono">{q.reference}</td>
              <td>{q.name} · {q.email}</td>
              <td>{q.origin} → {q.destination}</td>
              <td>{q.status}</td>
              <td>
                <select value={q.status} onChange={(e) => setStatus(q.id, e.target.value)} style={{ padding: 4 }}>
                  <option value="NEW">New</option>
                  <option value="IN_REVIEW">In review</option>
                  <option value="QUOTED">Quoted</option>
                  <option value="CLOSED">Closed</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
