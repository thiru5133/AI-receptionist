# AI Universal Receptionist — Hotel POC

Full implementation plan: **[PLAN.md](./PLAN.md)**.

## What's here (Phase 1 foundations, complete)

- FastAPI backend with tenant-scoped models (Tenant, Plan, User, DomainProfile, RoomType, Booking, WaitlistEntry, Caller, CallLog, Feedback).
- Vapi webhook + tool endpoints (12 tools: identify_caller, faq, availability, booking create/reschedule/cancel/status, waitlist, transfer, feedback, sentiment).
- JWT auth, role-gated dashboard API.
- React + Vite + TS admin UI (Login, Dashboard, Profile editor, Bookings, Call Logs).
- Postgres via docker-compose.
- Seed script for one Hotel tenant + profile + 3 room types + admin user.

## Run

### 1. Postgres
```bash
cd ~/ai-receptionist
docker compose up -d
```

### 2. Backend
```bash
cd ~/ai-receptionist/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.seed          # one-time
uvicorn app.main:app --reload --port 8000
```

Login: `admin@grandplaza.local` / `changeme`.

### 3. Frontend
```bash
cd ~/ai-receptionist/frontend
npm install
npm run dev                 # http://localhost:5173
```

### 4. Vapi wiring (when ready)
1. Get a public HTTPS URL for the backend (`ngrok http 8000`).
2. In Vapi: create an Assistant using the profile's Identity/Greeting/Voice.
3. Register these Server URLs on the assistant:
   - `POST {PUBLIC}/vapi/webhook/call-started`
   - `POST {PUBLIC}/vapi/webhook/call-ended`
4. Add tools pointing at `POST {PUBLIC}/vapi/tools/<name>` per PLAN.md §4.
5. Update `domain_profile.phone_number` to the Vapi-provisioned number so inbound calls resolve to the correct tenant.

## Next phases

See PLAN.md §7. Immediate next steps:
- Google Calendar adapter (currently `create_booking` writes DB only).
- Twilio notification adapter (currently a TODO in `create_booking`).
- Background jobs (reminders, no-show follow-up, waitlist auto-outbound).
- Webhook signature verification.
- Alembic migrations (currently `Base.metadata.create_all` bootstrap).
