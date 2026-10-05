import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

type Call = { id: number; duration_s: number };
type Booking = { id: number; status: string };

export default function Dashboard() {
  const calls = useQuery({ queryKey: ["calls"], queryFn: () => api<Call[]>("/calls") });
  const bookings = useQuery({ queryKey: ["bookings"], queryFn: () => api<Booking[]>("/bookings") });

  const minutes = Math.round(((calls.data ?? []).reduce((s, c) => s + c.duration_s, 0) / 60) * 10) / 10;
  const bookingsCount = (bookings.data ?? []).filter((b) => b.status !== "cancelled").length;

  return (
    <>
      <h2>Dashboard</h2>
      <div className="tiles">
        <div className="tile"><div className="n">{calls.data?.length ?? "—"}</div><div className="l">Calls (last 200)</div></div>
        <div className="tile"><div className="n">{minutes}</div><div className="l">Minutes used</div></div>
        <div className="tile"><div className="n">{bookingsCount}</div><div className="l">Active bookings</div></div>
        <div className="tile"><div className="n">1</div><div className="l">Active domain profiles</div></div>
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <p style={{ margin: 0, color: "#4a5568" }}>
          Usage tiles reflect the current tenant only. Plan gating is stubbed (soft cap) — see BRD FR-22 / FR-23.
        </p>
      </div>
    </>
  );
}
