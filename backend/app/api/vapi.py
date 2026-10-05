"""Vapi-facing endpoints: webhooks + tool calls.

Every tool endpoint accepts Vapi's tool-call envelope and returns { results: [...] }.
Tenant + profile are resolved from the dialed number in the call context.
"""
import json
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Booking, CallLog, Caller, DomainProfile, Feedback
from app.services.booking_service import (
    add_to_waitlist,
    create_booking,
    find_faq_answer,
    find_profile_by_number,
    get_room_type_by_name,
    has_conflict,
    mask_phone,
)

router = APIRouter(prefix="/vapi", tags=["vapi"])


# --- helpers ---------------------------------------------------------------


def _extract_call(payload: Dict[str, Any]) -> Dict[str, Any]:
    return payload.get("message", {}).get("call", {}) or payload.get("call", {}) or {}


def _dialed_number(payload: Dict[str, Any]) -> Optional[str]:
    call = _extract_call(payload)
    pn = call.get("phoneNumber") or {}
    return pn.get("number") or call.get("assistantPhoneNumber")


def _caller_number(payload: Dict[str, Any]) -> str:
    call = _extract_call(payload)
    customer = call.get("customer") or {}
    return customer.get("number") or "unknown"


def _resolve_profile(db: Session, payload: Dict[str, Any]) -> DomainProfile:
    number = _dialed_number(payload)
    if not number:
        raise HTTPException(400, "Cannot resolve dialed number")
    profile = find_profile_by_number(db, number)
    if not profile:
        raise HTTPException(404, "No profile bound to " + number)
    if not profile.active:
        raise HTTPException(403, "Profile inactive")
    return profile


def _tool_args(payload: Dict[str, Any]) -> Dict[str, Any]:
    msg = payload.get("message", {})
    tc = msg.get("toolCalls") or msg.get("toolCallList") or []
    if tc:
        fn = tc[0].get("function", {})
        args = fn.get("arguments")
        if isinstance(args, str):
            try:
                return json.loads(args)
            except json.JSONDecodeError:
                return {}
        return args or {}
    return payload.get("arguments", {})


def _tool_call_id(payload: Dict[str, Any]) -> Optional[str]:
    msg = payload.get("message", {})
    tc = msg.get("toolCalls") or msg.get("toolCallList") or []
    if tc:
        return tc[0].get("id")
    return None


def _result(tool_call_id: Optional[str], result: Any) -> Dict[str, Any]:
    return {"results": [{"toolCallId": tool_call_id, "result": result}]}


# --- webhooks --------------------------------------------------------------


@router.post("/webhook/call-started")
async def call_started(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    profile = _resolve_profile(db, payload)
    call = _extract_call(payload)
    log = CallLog(
        tenant_id=profile.tenant_id,
        profile_id=profile.id,
        vapi_call_id=call.get("id"),
        started_at=datetime.utcnow(),
        caller_phone_masked=mask_phone(_caller_number(payload)),
    )
    db.add(log)
    db.commit()
    return {"status": "ok"}


@router.post("/webhook/call-ended")
async def call_ended(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    call = _extract_call(payload)
    vapi_call_id = call.get("id")
    log = db.query(CallLog).filter(CallLog.vapi_call_id == vapi_call_id).first()
    msg = payload.get("message", {})
    if log:
        log.ended_at = datetime.utcnow()
        log.duration_s = int(msg.get("durationSeconds") or 0)
        log.recording_url = msg.get("recordingUrl") or call.get("recordingUrl")
        log.transcript = msg.get("transcript")
        log.outcome = msg.get("endedReason")
        db.commit()
    return {"status": "ok"}


# --- tools -----------------------------------------------------------------


@router.post("/tools/identify_caller")
async def tool_identify_caller(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    profile = _resolve_profile(db, payload)
    caller_phone = _caller_number(payload)
    caller = (
        db.query(Caller)
        .filter(Caller.tenant_id == profile.tenant_id, Caller.phone == caller_phone)
        .first()
    )
    result = {
        "known": bool(caller),
        "name": caller.name if caller else None,
        "vip": bool(caller.vip) if caller else False,
        "last_booking_id": caller.last_booking_id if caller else None,
    }
    return _result(_tool_call_id(payload), result)


@router.post("/tools/faq")
async def tool_faq(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    profile = _resolve_profile(db, payload)
    args = _tool_args(payload)
    question = str(args.get("question", "")).strip()
    if not question:
        return _result(_tool_call_id(payload), {"answer": None, "reason": "empty_question"})
    answer = find_faq_answer(profile, question)
    return _result(
        _tool_call_id(payload),
        {"answer": answer, "reason": None if answer else "not_in_kb"},
    )


@router.post("/tools/availability")
async def tool_availability(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    profile = _resolve_profile(db, payload)
    args = _tool_args(payload)
    room_type_name = str(args.get("room_type", ""))
    start = datetime.fromisoformat(args["start_ts"])
    end = datetime.fromisoformat(args["end_ts"])
    rt = get_room_type_by_name(db, profile.tenant_id, profile.id, room_type_name)
    if not rt:
        return _result(_tool_call_id(payload), {"available": False, "reason": "unknown_room_type"})
    conflict = has_conflict(db, rt.id, start, end)
    return _result(
        _tool_call_id(payload),
        {"available": not conflict, "room_type": rt.name, "capacity": rt.capacity},
    )


@router.post("/tools/booking/create")
async def tool_create_booking(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    profile = _resolve_profile(db, payload)
    args = _tool_args(payload)
    caller_phone = _caller_number(payload)
    rt = get_room_type_by_name(db, profile.tenant_id, profile.id, str(args.get("room_type", "")))
    if not rt:
        return _result(_tool_call_id(payload), {"success": False, "reason": "unknown_room_type"})
    start = datetime.fromisoformat(args["start_ts"])
    end = datetime.fromisoformat(args["end_ts"])
    if has_conflict(db, rt.id, start, end):
        return _result(_tool_call_id(payload), {"success": False, "reason": "unavailable"})
    b = create_booking(
        db,
        tenant_id=profile.tenant_id,
        profile_id=profile.id,
        room_type_id=rt.id,
        caller_phone=caller_phone,
        guest_name=str(args.get("guest_name", "Guest")),
        start_ts=start,
        end_ts=end,
    )
    # TODO: trigger notification (FR-07) via services/notifications.py
    return _result(
        _tool_call_id(payload),
        {"success": True, "confirmation_id": b.id, "room_type": rt.name},
    )


@router.post("/tools/booking/reschedule")
async def tool_reschedule_booking(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    profile = _resolve_profile(db, payload)
    args = _tool_args(payload)
    b = (
        db.query(Booking)
        .filter(Booking.id == int(args["confirmation_id"]), Booking.tenant_id == profile.tenant_id)
        .first()
    )
    if not b:
        return _result(_tool_call_id(payload), {"success": False, "reason": "not_found"})
    new_start = datetime.fromisoformat(args["start_ts"])
    new_end = datetime.fromisoformat(args["end_ts"])
    conflict = (
        db.query(Booking)
        .filter(
            Booking.id != b.id,
            Booking.room_type_id == b.room_type_id,
            Booking.status != "cancelled",
            Booking.start_ts < new_end,
            Booking.end_ts > new_start,
        )
        .first()
    )
    if conflict:
        return _result(_tool_call_id(payload), {"success": False, "reason": "unavailable"})
    b.start_ts = new_start
    b.end_ts = new_end
    db.commit()
    return _result(_tool_call_id(payload), {"success": True, "confirmation_id": b.id})


@router.post("/tools/booking/cancel")
async def tool_cancel_booking(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    profile = _resolve_profile(db, payload)
    args = _tool_args(payload)
    b = (
        db.query(Booking)
        .filter(Booking.id == int(args["confirmation_id"]), Booking.tenant_id == profile.tenant_id)
        .first()
    )
    if not b:
        return _result(_tool_call_id(payload), {"success": False, "reason": "not_found"})
    b.status = "cancelled"
    db.commit()
    return _result(_tool_call_id(payload), {"success": True})


@router.post("/tools/booking/status")
async def tool_booking_status(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    profile = _resolve_profile(db, payload)
    args = _tool_args(payload)
    b = (
        db.query(Booking)
        .filter(Booking.id == int(args["confirmation_id"]), Booking.tenant_id == profile.tenant_id)
        .first()
    )
    if not b:
        return _result(_tool_call_id(payload), {"found": False})
    return _result(
        _tool_call_id(payload),
        {
            "found": True,
            "guest_name": b.guest_name,
            "start_ts": b.start_ts.isoformat(),
            "end_ts": b.end_ts.isoformat(),
            "status": b.status,
        },
    )


@router.post("/tools/waitlist")
async def tool_waitlist(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    profile = _resolve_profile(db, payload)
    args = _tool_args(payload)
    caller_phone = _caller_number(payload)
    rt = get_room_type_by_name(db, profile.tenant_id, profile.id, str(args.get("room_type", "")))
    if not rt:
        return _result(_tool_call_id(payload), {"success": False, "reason": "unknown_room_type"})
    w = add_to_waitlist(
        db,
        tenant_id=profile.tenant_id,
        profile_id=profile.id,
        room_type_id=rt.id,
        caller_phone=caller_phone,
        guest_name=str(args.get("guest_name", "Guest")),
        window_start=datetime.fromisoformat(args["window_start"]),
        window_end=datetime.fromisoformat(args["window_end"]),
    )
    return _result(_tool_call_id(payload), {"success": True, "waitlist_id": w.id})


@router.post("/tools/transfer")
async def tool_transfer(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    profile = _resolve_profile(db, payload)
    args = _tool_args(payload)
    target = str(args.get("target", ""))
    routes = (profile.escalation or {}).get("routes", {})
    dest = routes.get(target)
    if not dest:
        return _result(_tool_call_id(payload), {"success": False, "reason": "no_route"})
    return _result(
        _tool_call_id(payload),
        {"success": True, "destination": dest, "mode": args.get("mode", "warm")},
    )


@router.post("/tools/feedback")
async def tool_feedback(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    args = _tool_args(payload)
    call = _extract_call(payload)
    log = db.query(CallLog).filter(CallLog.vapi_call_id == call.get("id")).first()
    if not log:
        return _result(_tool_call_id(payload), {"success": False, "reason": "no_call_log"})
    fb = Feedback(call_log_id=log.id, rating=int(args.get("rating", 0)), comment=args.get("comment"))
    db.add(fb)
    db.commit()
    return _result(_tool_call_id(payload), {"success": True})


@router.post("/tools/sentiment")
async def tool_sentiment(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    args = _tool_args(payload)
    call = _extract_call(payload)
    log = db.query(CallLog).filter(CallLog.vapi_call_id == call.get("id")).first()
    if log:
        log.sentiment = str(args.get("sentiment", ""))[:16]
        log.urgency_flag = bool(args.get("urgency", False))
        db.commit()
    return _result(_tool_call_id(payload), {"success": True})
