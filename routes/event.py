# routes/event.py —— 廢墟版活動報名平台的所有網址 (URL) 都在這裡
#
# 流程: 使用者在 UI 點按鈕 → 瀏覽器送出 URL → 這裡的函式去資料庫拿/存資料 → 回傳下一個 UI
#
# 網址一覽:
#   GET  /events                      列出可報名的活動清單
#   GET  /event/add                   顯示「新增活動」表單
#   POST /event/insert                收到新增表單，存進資料庫
#   GET  /event/{eid}/register        顯示某活動的報名表
#   POST /event/{eid}/register        收到報名表，存進資料庫
#   GET  /event/{eid}/registrations   查看某活動的報名清單
from datetime import date
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from db import getDB

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ---------- 1. 列出可報名的活動清單 ----------
@router.get("/events")
async def eventList(request: Request, db=Depends(getDB)):
	# 「可報名」= 活動日期還沒過，而且報名人數還沒滿
	# 因為人數要從 registrations 表數出來，所以用 LEFT JOIN + COUNT
	# 用 LEFT JOIN 而不是 JOIN，是因為還沒人報名的活動也要出現 (JOIN 會把 0 人的活動漏掉)
	cur = await db.execute("""
		SELECT e.*, COUNT(r.id) AS signed
		FROM events e
		LEFT JOIN registrations r ON r.event_id = e.id
		WHERE e.event_date >= CURRENT_DATE
		GROUP BY e.id
		HAVING COUNT(r.id) < e.quota
		ORDER BY e.event_date;
	""")
	data = await cur.fetchall()
	return templates.TemplateResponse(name="eventList.html", request=request, context={"events": data})


# ---------- 2. 新增新的活動 ----------
@router.get("/event/add")
async def eventAdd(request: Request):
	# 只是把空白表單給使用者看，不用碰資料庫
	return templates.TemplateResponse(name="eventAdd.html", request=request)

@router.post("/event/insert")
async def eventInsert(
	title: str = Form(...),
	event_date: date = Form(...),
	location: str = Form(...),
	quota: int = Form(...),
	db=Depends(getDB),
):
	# 用 %s 佔位、資料另外傳，而不是自己把字串拼進 SQL
	# 因為如果有人在標題打 '); DROP TABLE events; -- 這種東西，拼字串就會被當成指令執行 (SQL injection)
	await db.execute(
		"INSERT INTO events (title, event_date, location, quota) VALUES (%s, %s, %s, %s);",
		(title, event_date, location, quota),
	)
	# 303 會讓瀏覽器改用 GET 去開清單頁
	# 如果用預設的 307，瀏覽器會繼續用 POST，使用者按重新整理就會重複新增
	return RedirectResponse(url="/events", status_code=303)


# ---------- 3. 點擊報名 → 出現報名表 → 送出 ----------
@router.get("/event/{eid}/register")
async def registerForm(eid: int, request: Request, db=Depends(getDB)):
	# 報名表上要顯示「你正在報名哪個活動」，所以先把活動資料查出來
	cur = await db.execute("SELECT * FROM events WHERE id=%s;", (eid,))
	event = await cur.fetchone()
	if event is None:
		return HTMLResponse("找不到這個活動", status_code=404)
	return templates.TemplateResponse(name="registerForm.html", request=request, context={"event": event})

@router.post("/event/{eid}/register")
async def registerSubmit(eid: int, name: str = Form(...), phone: str = Form(...), db=Depends(getDB)):
	# 送出前再檢查一次名額
	# 因為使用者可能開著報名表很久，這段時間別人已經把名額報滿了，清單頁的檢查已經過期
	cur = await db.execute("""
		SELECT e.quota, COUNT(r.id) AS signed
		FROM events e
		LEFT JOIN registrations r ON r.event_id = e.id
		WHERE e.id=%s
		GROUP BY e.id;
	""", (eid,))
	row = await cur.fetchone()
	if row is None:
		return HTMLResponse("找不到這個活動", status_code=404)
	if row["signed"] >= row["quota"]:
		return HTMLResponse("報名已額滿 <a href='/events'>回活動清單</a>")

	await db.execute(
		"INSERT INTO registrations (event_id, name, phone) VALUES (%s, %s, %s);",
		(eid, name, phone),
	)
	# 報完名直接帶去看報名清單，使用者能馬上確認自己有在名單上
	return RedirectResponse(url=f"/event/{eid}/registrations", status_code=303)


# ---------- 4. 查看活動的報名清單 ----------
@router.get("/event/{eid}/registrations")
async def registrationList(eid: int, request: Request, db=Depends(getDB)):
	cur = await db.execute("SELECT * FROM events WHERE id=%s;", (eid,))
	event = await cur.fetchone()
	if event is None:
		return HTMLResponse("找不到這個活動", status_code=404)
	cur = await db.execute("SELECT * FROM registrations WHERE event_id=%s ORDER BY id;", (eid,))
	data = await cur.fetchall()
	return templates.TemplateResponse(
		name="registrationList.html", request=request,
		context={"event": event, "registrations": data},
	)
