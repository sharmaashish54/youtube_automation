import os
import base64
import requests
from openai import OpenAI

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
# CONFIG (SET THESE)
# =========================

VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Rachel

OUTPUT_DIR = "output"
SCRIPT_FILE = "script.txt"
BACKGROUND_IMAGE = "background.jpg"
AUDIO_FILE = f"{OUTPUT_DIR}/voice.mp3"
VIDEO_FILE = f"{OUTPUT_DIR}/kids_moral_short.mp4"

os.makedirs(OUTPUT_DIR, exist_ok=True)

client = OpenAI(api_key=OPENAI_API_KEY)


# =========================
# 1. AI STORY GENERATION
# =========================
def generate_kids_story():
    prompt = """
    Write a short moral story for kids aged 3 to 9.
    Language: Simple English
    Length: 8 to 10 short lines
    Tone: Warm, positive, child-friendly
    End with: Moral:
    Topic: honesty or kindness
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )

    story = response.choices[0].message.content.strip()

    with open(SCRIPT_FILE, "w") as f:
        f.write(story)

    print("✅ AI story generated")
    return story


# =========================
# 2. AI BACKGROUND IMAGE
# =========================
def generate_background_image(story):
    scene_prompt = (
        "A cheerful cartoon illustration for a kids moral story. "
        "Soft colors, friendly characters, safe environment. "
        "Scene inspired by: " + story.split("\n")[0]
    )

    result = client.images.generate(
        model="gpt-image-1",
        prompt=scene_prompt,
        size="1024x1792"
    )

    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    with open(BACKGROUND_IMAGE, "wb") as f:
        f.write(image_bytes)

    print("✅ AI background image generated")


# =========================
# 3. ELEVENLABS VOICE
# =========================
def generate_voice(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.8
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    with open(AUDIO_FILE, "wb") as f:
        f.write(response.content)

    print("✅ Voiceover generated")


# =========================
# 4. VIDEO CREATION
# =========================
def create_video(script):
    audio = AudioFileClip(AUDIO_FILE)

    bg = (
        ImageClip(BACKGROUND_IMAGE)
        .resized((1080, 1920))
        .with_duration(audio.duration)
    )

    lines = [l.strip() for l in script.split("\n") if l.strip()]
    clips = []

    start = 0
    dur = audio.duration / len(lines)

    for line in lines:
        txt = (
            TextClip(
                text=line.upper(),
                font_size=80,
                color="yellow",
                method="caption",
                size=(900, None),
                stroke_color="black",
                stroke_width=3
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
# 5. YOUTUBE UPLOAD
# =========================
def upload_to_youtube():
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]

    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json", scopes
    )
    credentials = flow.run_local_server(port=0)

    youtube = build("youtube", "v3", credentials=credentials)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "A Beautiful Moral Story for Kids 🌈 #Shorts",
                "description": (
                    "A short moral story for kids aged 3 to 9.\n\n"
                    "These stories teach honesty, kindness and good values.\n\n"
                    "#KidsStories #MoralStory #Shorts #BedtimeStories"
                ),
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(VIDEO_FILE)
    )

    response = request.execute()
    print("✅ Uploaded to YouTube:", response["id"])


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    story = generate_kids_story()
    generate_background_image(story)
    generate_voice(story)
    create_video(story)
    upload_to_youtube()
