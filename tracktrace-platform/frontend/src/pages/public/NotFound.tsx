import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="container" style={{ padding: "80px 0", textAlign: "center" }}>
      <h1 style={{ fontSize: "2rem" }}>Page not found</h1>
      <p style={{ color: "var(--slate-500)" }}>The page you're looking for doesn't exist.</p>
      <Link className="btn btn-primary" to="/">Go home</Link>
    </div>
  );
}
