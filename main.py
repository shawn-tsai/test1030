# main.py —— 程式進入點：建立 app、接上資料庫、把 routes 掛進來
# 啟動方式: fastapi dev main.py   (或 uv run fastapi dev main.py)
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from db import lifespan

app = FastAPI(lifespan=lifespan)  #lifespan 負責開機時連上資料庫、關機時斷線

# 把活動相關的網址全部掛進來
# 因為功能都寫在 routes/event.py，main.py 只負責「接線」，這樣分工時大家不會改到同一個檔案而衝突
from routes.event import router as eventRoute  #取個別名避免同名變數衝突
app.include_router(eventRoute)

@app.get("/")
async def home():
	# 首頁沒有自己的畫面，直接導到活動清單
	return RedirectResponse(url="/events", status_code=303)
