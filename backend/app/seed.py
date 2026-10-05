"""Seed one hotel tenant + one domain profile + room types + admin user.

Run:  python -m app.seed
"""
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import DomainProfile, Plan, RoomType, Tenant, User

HOTEL_PROFILE = {
    "identity": {
        "organization_name": "Grand Plaza Hotel",
        "greeting_template": "Thank you for calling Grand Plaza Hotel, how may I assist?",
        "operating_hours": {"mon-sun": "00:00-23:59"},
        "timezone": "Asia/Kolkata",
    },
    "knowledge_base": {
        "faqs": [
            {"question": "check in time", "answer": "Check-in is at 3 PM and check-out is at 11 AM."},
            {"question": "amenities", "answer": "We offer a pool, spa, gym, and complimentary breakfast."},
            {"question": "dining", "answer": "Our restaurant is open 6 AM to 11 PM, room service is 24/7."},
            {"question": "parking", "answer": "Valet parking is complimentary for all guests."},
            {"question": "location directions", "answer": "We are located 15 minutes from the airport on Main Boulevard."},
            {"question": "cancellation policy", "answer": "Free cancellation up to 24 hours before check-in."},
        ],
        "location": "123 Main Boulevard",
        "contact": "+91-80-4000-0000",
    },
    "intent_map": {
        "intents": [
            "book_room",
            "check_availability",
            "reschedule_booking",
            "cancel_booking",
            "booking_status",
            "ask_faq",
            "transfer_to_front_desk",
            "transfer_to_housekeeping",
            "transfer_to_manager",
        ],
        "fallback": "transfer_to_front_desk",
    },
    "booking_workflow": {
        "resource_type": "room",
        "required_fields": ["guest_name", "check_in_date", "check_out_date", "room_type", "guests"],
        "confirmation_template": "Confirmed {room_type} for {guest_name} from {start} to {end}. Confirmation: {id}.",
    },
    "escalation": {
        "routes": {
            "front_desk": "+91-80-4000-0001",
            "housekeeping": "+91-80-4000-0002",
            "manager": "+91-80-4000-0003",
        },
        "fallback": "voicemail",
    },
    "notification_templates": {
        "confirmation_sms": "Grand Plaza: booking {id} confirmed for {guest_name}, {room_type}, {start}.",
        "reminder_sms": "Reminder: your {room_type} at Grand Plaza is on {start}. Confirmation {id}.",
        "cancellation_sms": "Grand Plaza: booking {id} cancelled.",
        "waitlist_sms": "Grand Plaza: a {room_type} is now available on {start}. Reply YES to book.",
        "reminder_lead_hours": 24,
    },
}


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Tenant).count() > 0:
            print("Already seeded — skipping.")
            return

        plan = Plan(name="Starter", minute_allowance=1000, booking_allowance=500, max_profiles=1)
        db.add(plan)
        db.flush()

        tenant = Tenant(name="Grand Plaza Hotel", plan_id=plan.id, status="active")
        db.add(tenant)
        db.flush()

        admin = User(
            tenant_id=tenant.id,
            email="admin@grandplaza.local",
            password_hash=hash_password("changeme"),
            role="owner",
        )
        db.add(admin)

        profile = DomainProfile(
            tenant_id=tenant.id,
            name="Grand Plaza Hotel — Main",
            domain="hotel",
            active=True,
            voice_style="conversational",
            languages=["en", "hi"],
            identity=HOTEL_PROFILE["identity"],
            knowledge_base=HOTEL_PROFILE["knowledge_base"],
            intent_map=HOTEL_PROFILE["intent_map"],
            booking_workflow=HOTEL_PROFILE["booking_workflow"],
            escalation=HOTEL_PROFILE["escalation"],
            notification_templates=HOTEL_PROFILE["notification_templates"],
            phone_number="+10000000000",  # replace with Vapi-provisioned number
        )
        db.add(profile)
        db.flush()

        for name, cap in [("Standard", 20), ("Deluxe", 10), ("Suite", 5)]:
            db.add(
                RoomType(
                    tenant_id=tenant.id,
                    profile_id=profile.id,
                    name=name,
                    capacity=cap,
                )
            )

        db.commit()
        print(f"Seeded tenant={tenant.id} profile={profile.id}")
        print("Login: admin@grandplaza.local / changeme")
    finally:
        db.close()


if __name__ == "__main__":
    run()
