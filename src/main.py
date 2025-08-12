from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from src.llm import LLM
import gtts
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "template"))


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/translate")
async def translate(text: str = Form(...)):
    try:
        llm = LLM(prompt=text)
        translated_text = llm.translate(text)

        static_dir = os.path.join(BASE_DIR, "static")
        original_audio_path = os.path.join(static_dir, "original.mp3")
        translated_audio_path = os.path.join(static_dir, "translated.mp3")

        gtts.gTTS(text, lang="en").save(original_audio_path)
        gtts.gTTS(translated_text, lang="en").save(translated_audio_path)

        return JSONResponse({
            "original_text": text,
            "translated_text": translated_text,
            "original_audio": "/static/original.mp3",
            "translated_audio": "/static/translated.mp3"
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
