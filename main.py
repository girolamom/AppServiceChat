import os
import logging
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from azure.identity import DefaultAzureCredential
import uvicorn

# --------------------------------------------------
# Configurazione base
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = FastAPI()

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "templates")
)

# Variabili ambiente richieste
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_DEPLOYMENT:
    logger.warning("Endpoint o Deployment non configurati!")

# Managed Identity credential
credential = DefaultAzureCredential()

# --------------------------------------------------
# Homepage
# --------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}

# --------------------------------------------------
# Chat endpoint
# --------------------------------------------------

@app.post("/api/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message")

        if not user_message:
            return JSONResponse(
                status_code=400,
                content={"error": "Message is required"}
            )

        # Ottieni token Azure AD per Cognitive Services
        token = credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        )

        headers = {
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json"
        }

        body = {
            "messages": [
                {"role": "system", "content": "Sei un assistente utile."},
                {"role": "user", "content": user_message}
            ]
        }

        url = (
            f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/"
            f"{AZURE_OPENAI_DEPLOYMENT}/chat/completions"
            "?api-version=2024-02-15-preview"
        )

        response = requests.post(
            url,
            headers=headers,
            json=body,
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        reply = result["choices"][0]["message"]["content"]

        return {"reply": reply}

    except Exception as e:
        logger.error(f"Errore: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Errore interno"}
        )

# --------------------------------------------------
# Avvio applicazione
# --------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port
    )
