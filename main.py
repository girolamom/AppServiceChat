import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="templates")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message")

    headers = {
        "Content-Type": "application/json"
    }

    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Sei un assistente utile."},
            {"role": "user", "content": user_message}
        ]
    }

    response = requests.post(
        "https://foundry-expertdays2026-itn.cognitiveservices.azure.com/",
        headers=headers,
        json=body
    )

    result = response.json()
    reply = result["choices"][0]["message"]["content"]

    return JSONResponse({"reply": reply})
