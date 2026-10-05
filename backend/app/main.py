from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, bookings, calls, profiles, vapi
from app.core.database import Base, engine

# For Phase 1 dev bootstrap only. Move to Alembic migrations before production.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Universal Receptionist — Hotel POC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(bookings.router)
app.include_router(calls.router)
app.include_router(vapi.router)
