from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from db import getDB

router = APIRouter()
templates = Jinja2Templates(directory="templates")


async def getEvent(db, eid):
	cur = await db.execute("SELECT * FROM events WHERE id=%s;", (eid,))
	return await cur.fetchone()


@router.get("/events")
async def eventList(request: Request, db=Depends(getDB)):
	cur = await db.execute("SELECT * FROM events ORDER BY id;")
	data = await cur.fetchall()
	return templates.TemplateResponse(name="index.html", request=request, context={"events": data})


@router.get("/events/new")
async def eventNew(request: Request):
	return templates.TemplateResponse(name="event_new.html", request=request)

@router.post("/events")
async def eventInsert(title: str = Form(...), description: str = Form(""), db=Depends(getDB)):
	await db.execute(
		"INSERT INTO events (title, description) VALUES (%s, %s);",
		(title, description),
	)
	return RedirectResponse(url="/events", status_code=303)


@router.get("/events/{eid}")
async def eventDetail(eid: int, request: Request, db=Depends(getDB)):
	event = await getEvent(db, eid)
	if event is None:
		return HTMLResponse("找不到這個活動", status_code=404)
	return templates.TemplateResponse(name="event_detail.html", request=request, context={"event": event})

@router.post("/events/{eid}/register")
async def registerSubmit(eid: int, name: str = Form(...), phone: str = Form(...), db=Depends(getDB)):
	if await getEvent(db, eid) is None:
		return HTMLResponse("找不到這個活動", status_code=404)
	await db.execute(
		"INSERT INTO registrations (event_id, name, phone) VALUES (%s, %s, %s);",
		(eid, name, phone),
	)
	return RedirectResponse(url=f"/events/{eid}/participants", status_code=303)


@router.get("/events/{eid}/participants")
async def participantList(eid: int, request: Request, db=Depends(getDB)):
	event = await getEvent(db, eid)
	if event is None:
		return HTMLResponse("找不到這個活動", status_code=404)
	cur = await db.execute("SELECT * FROM registrations WHERE event_id=%s ORDER BY id;", (eid,))
	data = await cur.fetchall()
	return templates.TemplateResponse(
		name="participants.html", request=request,
		context={"event": event, "participants": data},
	)
