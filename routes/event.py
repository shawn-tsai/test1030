import re
import unicodedata
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from db import getDB

router = APIRouter()
templates = Jinja2Templates(directory="templates")

EVENT_COLUMNS = """
	a.event_id AS id, a.title, a.date,
	COALESCE(a.deadline, a.date) AS deadline,
	CURRENT_DATE > COALESCE(a.deadline, a.date) AS closed,
	(SELECT COUNT(*) FROM registrations r WHERE r.event_id = a.event_id) AS signed
"""


def normalizePhone(raw):
	phone = unicodedata.normalize("NFKC", raw).strip()
	if not re.fullmatch(r"\+?[0-9 ()\-]+", phone):
		return None
	digits = re.sub(r"[^0-9]", "", phone)
	if digits.startswith("886"):
		digits = "0" + digits[3:]
	if re.fullmatch(r"09[0-9]{8}", digits) or re.fullmatch(r"0[2-8][0-9]{7,8}", digits):
		return digits
	return None


async def getEvent(db, eid):
	cur = await db.execute(f"SELECT {EVENT_COLUMNS} FROM activities a WHERE a.event_id=%s;", (eid,))
	return await cur.fetchone()


@router.get("/events")
async def eventList(request: Request, db=Depends(getDB)):
	cur = await db.execute(f"SELECT {EVENT_COLUMNS} FROM activities a ORDER BY a.date, a.event_id;")
	data = await cur.fetchall()
	return templates.TemplateResponse(name="index.html", request=request, context={"events": data})


@router.get("/events/new")
async def eventNew(request: Request):
	return templates.TemplateResponse(name="event_new.html", request=request)

@router.post("/events")
async def eventInsert(
	title: str = Form(...),
	eventDate: date = Form(..., alias="date"),
	deadline: Optional[str] = Form(None),
	db=Depends(getDB),
):
	await db.execute(
		"INSERT INTO activities (title, date, deadline) VALUES (%s, %s, %s);",
		(title, eventDate, deadline or None),
	)
	return RedirectResponse(url="/events", status_code=303)


@router.get("/events/{eid}")
async def eventDetail(eid: int, request: Request, db=Depends(getDB)):
	event = await getEvent(db, eid)
	if event is None:
		return HTMLResponse("找不到這個活動", status_code=404)
	return templates.TemplateResponse(name="event_detail.html", request=request, context={"event": event})

@router.post("/events/{eid}/register")
async def registerSubmit(eid: int, request: Request, name: str = Form(...), phone: str = Form(...), db=Depends(getDB)):
	event = await getEvent(db, eid)
	if event is None:
		return HTMLResponse("找不到這個活動", status_code=404)

	name, phone = name.strip(), phone.strip()
	normalized = normalizePhone(phone)
	error = None
	if event["closed"]:
		error = "此活動已截止報名"
	elif normalized is None:
		error = "電話格式錯誤，請輸入台灣手機（例如 0912-345-678）或市話（例如 02-1234-5678），不可包含英文或其他符號"
	else:
		phone = normalized
		cur = await db.execute(
			"SELECT 1 FROM registrations WHERE event_id=%s AND name=%s AND phone_number=%s;",
			(eid, name, phone),
		)
		if await cur.fetchone():
			error = f"{name}（{phone}）已經報名過此活動"

	if error:
		return templates.TemplateResponse(
			name="event_detail.html", request=request, status_code=400,
			context={"event": event, "error": error, "name": name, "phone": phone},
		)

	await db.execute(
		"INSERT INTO registrations (event_id, name, phone_number) VALUES (%s, %s, %s);",
		(eid, name, phone),
	)
	return RedirectResponse(url=f"/events/{eid}/participants", status_code=303)


@router.get("/events/{eid}/participants")
async def participantList(eid: int, request: Request, db=Depends(getDB)):
	event = await getEvent(db, eid)
	if event is None:
		return HTMLResponse("找不到這個活動", status_code=404)
	cur = await db.execute(
		"SELECT sign_id, event_id, name, phone_number AS phone FROM registrations WHERE event_id=%s ORDER BY sign_id;",
		(eid,),
	)
	data = await cur.fetchall()
	return templates.TemplateResponse(
		name="participants.html", request=request,
		context={"event": event, "participants": data},
	)
