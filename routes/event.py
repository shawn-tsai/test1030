# routes/event.py —— 廢墟版活動報名平台的所有網址 (URL) 都在這裡
#
# 流程: 使用者在 UI 點按鈕 → 瀏覽器送出 URL → 這裡的函式去資料庫拿/存資料 → 回傳下一個 UI
#
# 網址是照 C 寫好的 template 裡的連結來定的 (template 的 href / form action 指向哪，這裡就要接哪):
#   GET  /events                       列出活動清單              → index.html
#   GET  /events/new                   顯示「新增活動」表單       → event_new.html (C 還沒做)
#   POST /events                       收到新增表單，存進資料庫
#   GET  /events/{eid}                 顯示某活動的介紹 + 報名表  → event_detail.html
#   POST /events/{eid}/register        收到報名表，存進資料庫
#   GET  /events/{eid}/participants    查看某活動的報名清單       → participants.html
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from db import getDB

router = APIRouter()
templates = Jinja2Templates(directory="template")  #C 的資料夾叫 template (沒有 s)


# 好幾個網址都要「用 id 查一個活動」，所以抽成一個小函式，避免同一段 SQL 寫三次
async def getEvent(db, eid):
	cur = await db.execute("SELECT * FROM events WHERE id=%s;", (eid,))
	return await cur.fetchone()  #查不到會回傳 None


# ---------- 1. 列出可報名的活動清單 ----------
@router.get("/events")
async def eventList(request: Request, db=Depends(getDB)):
	cur = await db.execute("SELECT * FROM events ORDER BY id;")
	data = await cur.fetchall()
	return templates.TemplateResponse(name="index.html", request=request, context={"events": data})


# ---------- 2. 新增新的活動 ----------
# 注意: /events/new 要寫在 /events/{eid} 前面
# 因為 FastAPI 由上往下比對網址，寫在後面的話 "new" 會先被 {eid} 那條規則拿去比對
@router.get("/events/new")
async def eventNew(request: Request):
	# 只是把空白表單給使用者看，不用碰資料庫
	return templates.TemplateResponse(name="event_new.html", request=request)

@router.post("/events")
async def eventInsert(title: str = Form(...), description: str = Form(""), db=Depends(getDB)):
	# 用 %s 佔位、資料另外傳，而不是自己把字串拼進 SQL
	# 因為如果有人在標題打 '); DROP TABLE events; -- 這種東西，拼字串就會被當成指令執行 (SQL injection)
	await db.execute(
		"INSERT INTO events (title, description) VALUES (%s, %s);",
		(title, description),
	)
	# 303 會讓瀏覽器改用 GET 去開清單頁
	# 如果用預設的 307，瀏覽器會繼續用 POST，使用者按重新整理就會重複新增
	return RedirectResponse(url="/events", status_code=303)


# ---------- 3. 點擊報名 → 出現報名表 → 送出 ----------
@router.get("/events/{eid}")
async def eventDetail(eid: int, request: Request, db=Depends(getDB)):
	# 報名表上要顯示「你正在報名哪個活動」，所以先把活動資料查出來
	event = await getEvent(db, eid)
	if event is None:
		return HTMLResponse("找不到這個活動", status_code=404)
	return templates.TemplateResponse(name="event_detail.html", request=request, context={"event": event})

@router.post("/events/{eid}/register")
async def registerSubmit(eid: int, name: str = Form(...), phone: str = Form(...), db=Depends(getDB)):
	# 先確認活動存在，因為有人可能直接亂打網址送一個不存在的 eid 進來
	if await getEvent(db, eid) is None:
		return HTMLResponse("找不到這個活動", status_code=404)
	await db.execute(
		"INSERT INTO registrations (event_id, name, phone) VALUES (%s, %s, %s);",
		(eid, name, phone),
	)
	# 報完名直接帶去看報名清單，使用者能馬上確認自己有在名單上
	return RedirectResponse(url=f"/events/{eid}/participants", status_code=303)


# ---------- 4. 查看活動的報名清單 ----------
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
