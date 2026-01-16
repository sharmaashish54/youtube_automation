import os
import requests

from moviepy import (
    AudioFileClip,
    ImageClip,
    TextClip,
    CompositeVideoClip
)

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# =========================
# CONFIG
# =========================
ELEVEN_API_KEY = "sk_109d154cc7ee93b814a98cd032003be19829ad5dd0c4dc18"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Rachel voice ID

SCRIPT_FILE = "script.txt"
BACKGROUND_IMAGE = "background.jpg"
OUTPUT_DIR = "output"
AUDIO_FILE = f"{OUTPUT_DIR}/voice.mp3"
VIDEO_FILE = f"{OUTPUT_DIR}/short.mp4"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================
# ELEVENLABS VOICE
# =========================
def generate_voice(text: str):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    with open(AUDIO_FILE, "wb") as f:
        f.write(response.content)

    print("✅ Voiceover generated")


# =========================
# VIDEO CREATION
# =========================
def create_video(script: str):
    audio = AudioFileClip(AUDIO_FILE)

    bg = (
        ImageClip(BACKGROUND_IMAGE)
        .resized((1080, 1920))
        .with_duration(audio.duration)
    )

    lines = [line.strip() for line in script.split("\n") if line.strip()]
    clips = []

    start = 0
    dur = audio.duration / len(lines)

    for line in lines:
        txt = (
            TextClip(
                text=line,
                font_size=70,
                color="white",
                method="caption",
                size=(900, None),
                stroke_color="black",
                stroke_width=2
            )
            .with_position(("center", "center"))
            .with_start(start)
            .with_duration(dur)
        )

        clips.append(txt)
        start += dur

    video = CompositeVideoClip([bg, *clips]).with_audio(audio)

    video.write_videofile(
        VIDEO_FILE,
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )

    print("✅ Video created")


# =========================
# YOUTUBE UPLOAD
# =========================
def upload_to_youtube():
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]

    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json",
        scopes
    )
    credentials = flow.run_local_server(port=0)

    youtube = build("youtube", "v3", credentials=credentials)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Amazing Fact #Shorts",
                "description": "AI generated YouTube Short\n#Shorts",
                "tags": ["Shorts", "Facts", "AI"],
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(VIDEO_FILE)
    )

    response = request.execute()
    print("✅ Uploaded video ID:", response["id"])


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    with open(SCRIPT_FILE, "r") as f:
        script = f.read()

    generate_voice(script)
    create_video(script)
    upload_to_youtube()
