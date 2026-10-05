import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, setToken } from "../lib/api";

export default function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState("admin@grandplaza.local");
  const [password, setPassword] = useState("changeme");
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      const r = await api<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(r.access_token);
      nav("/");
    } catch (e: any) {
      setErr(e.message);
    }
  }

  return (
    <div className="container" style={{ maxWidth: 380 }}>
      <div className="card">
        <h2>Admin Login</h2>
        <form onSubmit={submit}>
          <div className="field">
            <label>Email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: "100%" }} />
          </div>
          <div className="field">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: "100%" }}
            />
          </div>
          {err && <div className="badge err">{err}</div>}
          <button type="submit">Sign in</button>
        </form>
      </div>
    </div>
  );
}
