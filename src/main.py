from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import speech_recognition as sr
import tempfile
from llm import LLM
import gtts
import os
from pydub import AudioSegment

app = FastAPI()

#uvicorn main:app --reload

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static & templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "template"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/translate")
async def translate(audio: UploadFile = File(...)):
    temp_path, wav_path = None, None
    try:
        # Save uploaded audio (.webm from browser)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            temp_file.write(await audio.read())
            temp_path = temp_file.name

        # Convert WebM to WAV
        wav_path = temp_path.replace(".webm", ".wav")
        try:
            AudioSegment.from_file(temp_path).export(wav_path, format="wav")
        except Exception as e:
            raise ValueError(f"Audio conversion failed: {e}")

        # Speech to text
        try:
            r = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = r.record(source)
                original_text = r.recognize_google(audio_data)
        except Exception as e:
            raise ValueError(f"Speech recognition failed: {e}")

        # Translate
        try:
            llm = LLM(prompt=original_text)
            translated_text = llm.translate(original_text)
        except Exception as e:
            raise ValueError(f"Translation failed: {e}")

        # TTS output paths
        static_dir = os.path.join(BASE_DIR, "static")
        original_audio_path = os.path.join(static_dir, "original.mp3")
        translated_audio_path = os.path.join(static_dir, "translated.mp3")

        # Generate speech
        try:
            gtts.gTTS(original_text, lang="en").save(original_audio_path)
            gtts.gTTS(translated_text, lang="en").save(translated_audio_path)
        except Exception as e:
            raise ValueError(f"TTS failed: {e}")

        return JSONResponse({
            "original_text": original_text,
            "translated_text": translated_text,
            "original_audio": "/static/original.mp3",
            "translated_audio": "/static/translated.mp3"
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    finally:
        # Clean up temp files
        for f in [temp_path, wav_path]:
            if f and os.path.exists(f):
                os.remove(f)
