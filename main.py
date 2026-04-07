import requests
import moviepy.editor as mp
from gtts import gTTS
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
import random

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

def extract_reddit_text(url):
    try:
        if url.endswith("/"):
            url = url[:-1]

        json_url = url + ".json"
        data = requests.get(json_url, headers={"User-agent": "Mozilla/5.0"}).json()
        text = data[0]["data"]["children"][0]["data"]["selftext"]
        return text if text else "No story text found."
    except:
        return "Failed to extract Reddit text."

def generate_tts(text):
    tts = gTTS(text=text, lang="en")
    tts.save("voice.mp3")
    return "voice.mp3"

def generate_video(audio_path, text, clip_length=60):
    video_path = "static/minecraft_long.mp4"

    video = mp.VideoFileClip(video_path)
    audio = mp.AudioFileClip(audio_path)

    clip_duration = min(clip_length, video.duration)

    max_start = max(0, video.duration - clip_duration)
    start_time = random.uniform(0, max_start)

    subclip = video.subclip(start_time, start_time + clip_duration)
    subclip = subclip.set_audio(audio)

    caption = mp.TextClip(
        text, fontsize=40, color="yellow",
        stroke_color="black", stroke_width=2
    ).set_duration(clip_duration).set_position(("center", "bottom"))

    final = mp.CompositeVideoClip([subclip, caption])
    final.write_videofile("final.mp4", fps=30)

@app.post("/generate")
async def generate(
    request: Request,
    reddit_url: str = Form(...),
    voice: str = Form(...),
    background: str = Form(...),
    length: int = Form(...),
    captions: str = Form(...)
):
    text = extract_reddit_text(reddit_url)
    audio = generate_tts(text)
    generate_video(audio, text, clip_length=length)
    return FileResponse("final.mp4", media_type="video/mp4", filename="final.mp4")
