from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, sys, subprocess
import librosa, soundfile as sf
import numpy as np

# === Path setup ===
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from src.predict import FinalEmotiVoice

app = FastAPI(title="EmotiVoice API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load model once
predictor = FinalEmotiVoice()

@app.post("/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".wav", ".webm")):
        raise HTTPException(400, detail="Only .wav or .webm files are allowed")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    wav_path = file_path.rsplit(".", 1)[0] + "_clean.wav"
    final_wav = file_path.rsplit(".", 1)[0] + "_final.wav"

    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Convert to clean WAV using ffmpeg (works for both .wav and .webm)
        subprocess.run([
            "ffmpeg", "-y", "-i", file_path,
            "-ar", "16000", "-ac", "1", wav_path
        ], check=True, capture_output=True)

        # Load audio
        audio, sr = librosa.load(wav_path, sr=16000, mono=True)
        print(f"[DEBUG] Audio length: {len(audio)}, SR: {sr}")

        # Validate
        if audio is None or len(audio) < 1000:
            raise HTTPException(400, detail="Audio too short or invalid")
        if np.isnan(audio).any():
            raise HTTPException(400, detail="Invalid audio (NaN detected)")

        # Pad if too short (min 2 seconds)
        min_length = 16000 * 2
        if len(audio) < min_length:
            audio = np.pad(audio, (0, min_length - len(audio)))

        # Write final clean WAV for model
        sf.write(final_wav, audio, sr, subtype='PCM_16')

        # Run prediction
        try:
            result = predictor.predict(final_wav)
        except Exception as model_error:
            print("[MODEL ERROR]:", model_error)
            raise HTTPException(500, detail="Model prediction failed")

        return result

    except HTTPException:
        raise
    except Exception as e:
        print("[SERVER ERROR]:", e)
        raise HTTPException(500, detail=f"Error: {str(e)}")

    finally:
        # Cleanup all temp files
        for path in [file_path, wav_path, final_wav]:
            if path and os.path.exists(path):
                os.remove(path)

@app.get("/")
def home():
    return {"message": "EmotiVoice API is running 🚀"}