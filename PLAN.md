# AI Universal Receptionist — Hotel POC Implementation Plan

**Source of truth:** `BRD_AI_Universal_Receptionist_POC_V4.md` (BRD v2.0, 2026-07-03).
**Phase 1 scope:** Hotel domain only. Multi-tenant schema in place from day one (one seeded tenant + one hotel domain profile).

---

## 1. Stack

| Layer     | Tech                                                    |
|-----------|---------------------------------------------------------|
| Voice     | **Vapi** (telephony + STT + LLM + TTS + recording)      |
| Backend   | **Python 3.12 + FastAPI**, SQLAlchemy 2, Alembic, Pydantic v2 |
| DB        | PostgreSQL 16                                            |
| Jobs      | APScheduler (Phase 1); swap to Celery+Redis if load demands |
| Frontend  | **React 18 + Vite + TypeScript**, TanStack Query, React Router |
| Notif.    | Twilio (SMS + WhatsApp sandbox)                          |
| Calendar  | Google Calendar API (per BRD §6.2 — availability source of truth) |
| Tunnel    | ngrok / cloudflared (expose FastAPI to Vapi in dev)      |

---

## 2. Architecture

```
   PSTN caller ──► Vapi (assistant, STT, LLM, TTS, recording)
                      │
                      │ webhooks + tool calls (HTTPS, HMAC-signed)
                      ▼
              FastAPI backend ──► PostgreSQL (tenant_id on every row)
                      │              Google Calendar (per-room-type calendar)
                      │              Twilio (SMS/WhatsApp)
                      ▼
              React admin dashboard (JWT auth, role-gated)
```

Multi-tenant: dialed number → tenant_id + profile_id lookup on inbound; JWT carries tenant_id on dashboard requests.

---

## 3. Data Model (Phase 1)

| Table              | Notes                                                                                   |
|--------------------|-----------------------------------------------------------------------------------------|
| `tenant`           | id, name, plan_id, status                                                                |
| `plan`             | id, name, minute_allowance, booking_allowance, max_profiles                              |
| `user`             | id, tenant_id, email, hash, role ∈ {super_admin, owner, admin, operator}                 |
| `domain_profile`   | id, tenant_id, identity_json, kb_json, intent_map_json, booking_workflow_json, escalation_json, notification_templates_json, active, voice_style, languages[] |
| `room_type`        | id, tenant_id, profile_id, name, calendar_id, capacity                                   |
| `booking`          | id, tenant_id, profile_id, room_type_id, caller_phone_masked, guest_name, start_ts, end_ts, status, calendar_event_id, source, recurring_parent_id |
| `waitlist_entry`   | id, tenant_id, room_type_id, window_start, window_end, caller_phone, status              |
| `caller`           | id, tenant_id, phone, name, vip, notes, last_booking_id                                  |
| `call_log`         | id, tenant_id, profile_id, started_at, ended_at, duration_s, caller_phone_masked, language, detected_intents[], outcome, sentiment, urgency_flag, recording_url, transcript_url, escalation_target |
| `feedback`         | id, call_log_id, rating, comment                                                          |
| `usage_meter`      | id, tenant_id, period, minutes_used, bookings_used                                        |
| `audit_log`        | id, actor_user_id, tenant_id_scope, action, target, timestamp                             |

---

## 4. Vapi Assistant & Tools

**Assistant (per hotel profile):** greeting from profile Identity, voice style from profile, transcriber with 2-language detect, recording on with disclosure, tool server URL → FastAPI.

**Tools → FastAPI endpoints:**

| Tool | Endpoint | FR |
|------|----------|----|
| `identify_caller` | POST /vapi/tools/identify_caller | FR-14 |
| `get_faq_answer` | POST /vapi/tools/faq | FR-03 |
| `check_room_availability` | POST /vapi/tools/availability | FR-04 |
| `create_booking` | POST /vapi/tools/booking/create | FR-04 |
| `reschedule_booking` | POST /vapi/tools/booking/reschedule | FR-05 |
| `cancel_booking` | POST /vapi/tools/booking/cancel | FR-05 |
| `get_booking_status` | POST /vapi/tools/booking/status | FR-04 |
| `add_to_waitlist` | POST /vapi/tools/waitlist | FR-15 |
| `request_transfer` | POST /vapi/tools/transfer | FR-06 |
| `place_internal_call` | POST /vapi/tools/internal_call | FR-12 |
| `submit_feedback` | POST /vapi/tools/feedback | FR-19 |
| `log_sentiment_flag` | POST /vapi/tools/sentiment | FR-16 |

**Webhooks:** `POST /vapi/webhook/call-started`, `POST /vapi/webhook/call-ended`.

---

## 5. Frontend Screens

Login • Dashboard (usage tiles) • Domain Profile Editor (6 tabs mirroring BRD §8.1) • Bookings + Waitlist • Call Logs (list + detail with transcript & recording) • Post-call feedback • Tenant Settings (users, roles, plan/usage).

Super-Admin console (FR-26) — schema ready; UI deferred.

---

## 6. Voice Flow (Hotel)

Matches BRD §10, hotel-restricted: inbound → tenant lookup → greeting/lang → intent → { FAQ | book (availability→create→notify) | reschedule/cancel | transfer | waitlist | after-hours callback } → hang up → log/transcript/recording written → feedback stored. Outbound jobs: reminders, no-show follow-up, waitlist auto-outbound, missed-call callback.

---

## 7. Development Phases

1. **Foundations** ← *starting here* — repo scaffold, FastAPI+Postgres+Alembic, React+Vite+auth stub, .env templates, docker-compose.
2. Tenant/profile schema + seed one hotel tenant from JSON fixture.
3. Vapi wiring (thin): assistant, call-started/ended webhooks, call_log rows.
4. FAQ + KB editor.
5. Availability + create_booking + Google Calendar adapter + notification.
6. Reschedule / cancel / status.
7. Caller identification + VIP.
8. Escalation + transfer + failure fallback.
9. Waitlist + background jobs (reminders, no-show, waitlist auto-outbound).
10. Sentiment/urgency, hold queue, after-hours, feedback.
11. Second language.
12. Usage metering + role gating + plan gating.
13. (Deferred) Super-Admin console.

---

## 8. Environment / Config

Required env (see `backend/.env.example`):

```
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/receptionist
JWT_SECRET=change-me
VAPI_API_KEY=
VAPI_WEBHOOK_SIGNING_SECRET=
VAPI_PHONE_NUMBER_ID=
GOOGLE_SERVICE_ACCOUNT_JSON=./secrets/gsa.json
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_SMS_FROM=
TWILIO_WHATSAPP_FROM=
PUBLIC_BASE_URL=https://<tunnel>.ngrok-free.app
```

---

## 9. Testing Strategy

- Unit: booking guard, template rendering, calendar adapter (mocked), tenant scoping.
- Contract tests per Vapi tool endpoint (envelope in/out).
- Webhook signature verification.
- Integration: create → reschedule → cancel with notification adapter assertions.
- End-to-end voice via Vapi test call: FAQ, book-success, no-avail→waitlist, reschedule, cancel, transfer, after-hours, emergency escalation.
- Multi-tenant isolation test (FR-24 acceptance).
- Frontend: component tests + Playwright happy-path.

---

## 10. Open Questions

1. Google Calendar mapping — one calendar per room type? (default: yes)
2. Which two POC languages? (default: English + Spanish)
3. Reminder lead time, no-show window, hold-queue callback threshold? (defaults: 24h, 30m, 60s)
4. Plan enforcement depth in POC — soft (warn) or hard (cap)? (default: soft)
