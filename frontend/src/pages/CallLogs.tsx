import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";

type Call = {
  id: number;
  started_at: string;
  duration_s: number;
  caller_phone_masked: string | null;
  language: string | null;
  detected_intents: string[];
  outcome: string | null;
  sentiment: string | null;
  urgency_flag: boolean;
  recording_url: string | null;
};

type CallDetail = Call & { transcript: string | null };

export default function CallLogs() {
  const list = useQuery({ queryKey: ["calls"], queryFn: () => api<Call[]>("/calls") });
  const [openId, setOpenId] = useState<number | null>(null);
  const detail = useQuery({
    queryKey: ["call", openId],
    queryFn: () => api<CallDetail>(`/calls/${openId}`),
    enabled: openId != null,
  });

  return (
    <>
      <h2>Call Logs</h2>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>When</th><th>Caller</th><th>Dur (s)</th><th>Lang</th>
              <th>Intents</th><th>Outcome</th><th>Sentiment</th><th></th>
            </tr>
          </thead>
          <tbody>
            {(list.data ?? []).map((c) => (
              <tr key={c.id}>
                <td>{c.id}</td>
                <td>{new Date(c.started_at).toLocaleString()}</td>
                <td>{c.caller_phone_masked}</td>
                <td>{c.duration_s}</td>
                <td>{c.language}</td>
                <td>{c.detected_intents?.join(", ")}</td>
                <td>{c.outcome}</td>
                <td>
                  {c.sentiment}{" "}
                  {c.urgency_flag && <span className="badge err">urgent</span>}
                </td>
                <td>
                  <button onClick={() => setOpenId(c.id)}>View</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {openId && detail.data && (
        <div className="card">
          <h3>Call #{detail.data.id}</h3>
          {detail.data.recording_url && (
            <audio controls src={detail.data.recording_url} style={{ width: "100%" }} />
          )}
          <h4>Transcript</h4>
          <pre style={{ whiteSpace: "pre-wrap" }}>
            {detail.data.transcript ?? "(no transcript)"}
          </pre>
          <button onClick={() => setOpenId(null)}>Close</button>
        </div>
      )}
    </>
  );
}
