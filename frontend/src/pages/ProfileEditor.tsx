import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api } from "../lib/api";

type Profile = {
  id: number;
  name: string;
  domain: string;
  active: boolean;
  voice_style: string;
  languages: string[];
  identity: Record<string, unknown>;
  knowledge_base: Record<string, unknown>;
  intent_map: Record<string, unknown>;
  booking_workflow: Record<string, unknown>;
  escalation: Record<string, unknown>;
  notification_templates: Record<string, unknown>;
  phone_number: string | null;
};

const TABS = [
  "identity",
  "knowledge_base",
  "intent_map",
  "booking_workflow",
  "escalation",
  "notification_templates",
] as const;
type Tab = (typeof TABS)[number];

export default function ProfileEditor() {
  const qc = useQueryClient();
  const list = useQuery({ queryKey: ["profiles"], queryFn: () => api<Profile[]>("/profiles") });
  const profile = list.data?.[0];

  const [tab, setTab] = useState<Tab>("identity");
  const [draft, setDraft] = useState("");

  useEffect(() => {
    if (profile) setDraft(JSON.stringify(profile[tab], null, 2));
  }, [profile, tab]);

  const save = useMutation({
    mutationFn: async (patch: Record<string, unknown>) =>
      api(`/profiles/${profile!.id}`, { method: "PATCH", body: JSON.stringify(patch) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["profiles"] }),
  });

  if (!profile) return <div>Loading profile…</div>;

  function onSave() {
    try {
      const parsed = JSON.parse(draft);
      save.mutate({ [tab]: parsed });
    } catch (e: any) {
      alert(`Invalid JSON: ${e.message}`);
    }
  }

  return (
    <>
      <h2>
        Domain Profile — {profile.name}{" "}
        <span className="badge">{profile.domain}</span>{" "}
        <span className="badge">{profile.active ? "active" : "inactive"}</span>
      </h2>
      <div className="card">
        <div><strong>Phone number:</strong> {profile.phone_number ?? "not provisioned"}</div>
        <div><strong>Voice style:</strong> {profile.voice_style}</div>
        <div><strong>Languages:</strong> {profile.languages.join(", ")}</div>
      </div>

      <div className="card">
        <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                background: tab === t ? "#2b6cb0" : "#e2e8f0",
                color: tab === t ? "white" : "#1a1a1a",
              }}
            >
              {t.replace("_", " ")}
            </button>
          ))}
        </div>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          style={{ width: "100%", height: 380, fontFamily: "monospace" }}
        />
        <div style={{ marginTop: 8 }}>
          <button onClick={onSave} disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </>
  );
}
