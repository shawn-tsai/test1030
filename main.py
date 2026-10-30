from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from db import lifespan

app = FastAPI(lifespan=lifespan)

from routes.event import router as eventRoute
app.include_router(eventRoute)

@app.get("/")
async def home():
	return RedirectResponse(url="/events", status_code=303)
