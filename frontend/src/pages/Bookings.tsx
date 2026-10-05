import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

type Booking = {
  id: number;
  profile_id: number;
  room_type_id: number;
  guest_name: string;
  caller_phone_masked: string;
  start_ts: string;
  end_ts: string;
  status: string;
};

export default function Bookings() {
  const q = useQuery({ queryKey: ["bookings"], queryFn: () => api<Booking[]>("/bookings") });
  return (
    <>
      <h2>Bookings</h2>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Guest</th><th>Caller</th><th>Start</th><th>End</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            {(q.data ?? []).map((b) => (
              <tr key={b.id}>
                <td>{b.id}</td>
                <td>{b.guest_name}</td>
                <td>{b.caller_phone_masked}</td>
                <td>{new Date(b.start_ts).toLocaleString()}</td>
                <td>{new Date(b.end_ts).toLocaleString()}</td>
                <td>
                  <span className={`badge ${b.status === "cancelled" ? "err" : ""}`}>{b.status}</span>
                </td>
              </tr>
            ))}
            {q.data && q.data.length === 0 && (
              <tr><td colSpan={6} style={{ color: "#4a5568" }}>No bookings yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
