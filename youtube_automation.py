import os
import requests
from moviepy import ImageClip, TextClip, CompositeVideoClip, AudioFileClip
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from gtts import gTTS

# =========================================================
# CONFIG
# =========================================================
ELEVEN_API_KEY = "sk_109d154cc7ee93b814a98cd032003be19829ad5dd0c4dc18"
VOICE_ID = "Rachel"

OLLAMA_URL = "http://localhost:11434/api/generate"

BACKGROUND_IMAGE = "background.jpg"   # 1080x1920 preferred
OUTPUT_DIR = "output"
AUDIO_FILE = f"{OUTPUT_DIR}/voice.mp3"
VIDEO_FILE = f"{OUTPUT_DIR}/short.mp4"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================================================
# 1. AI STORY GENERATION (OLLAMA - FREE)
# =========================================================
def generate_story():
    prompt = """
Create a short moral story for kids aged 3 to 9.

Rules:
- English language
- Maximum 70 words
- Simple, friendly vocabulary
- One clear moral
- Happy ending
- Perfect for a 30-second YouTube Short

Return ONLY the story text.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        },
        timeout=60
    )

    response.raise_for_status()
    story = response.json()["response"].strip()
    return story

# =========================================================
# 2. VOICE GENERATION (ELEVENLABS - SAFE)
# =========================================================
def generate_voice(text):
    try:
        print("🎙 Trying ElevenLabs...")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {
            "xi-api-key": ELEVEN_API_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "text": text,
            "voice_settings": {
                "stability": 0.6,
                "similarity_boost": 0.8
            }
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code != 200 or not response.headers.get(
            "Content-Type", ""
        ).startswith("audio"):
            raise Exception("ElevenLabs failed")

        with open(AUDIO_FILE, "wb") as f:
            f.write(response.content)

        print("✅ ElevenLabs voice generated")

    except Exception as e:
        print("⚠️ ElevenLabs failed, using Google TTS")

        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(AUDIO_FILE)

        print("✅ Google TTS voice generated")

# =========================================================
# 3. VIDEO CREATION (MOVIEPY 2.x)
# =========================================================
def create_video(script):
    audio = AudioFileClip(AUDIO_FILE)

    bg = (
        ImageClip(BACKGROUND_IMAGE)
        .resized(new_size=(1080, 1920))
        .with_duration(audio.duration)
    )

    sentences = [s.strip() for s in script.split(".") if s.strip()]
    duration_per_line = audio.duration / max(len(sentences), 1)

    text_clips = []
    start_time = 0

    for line in sentences:
        txt = (
            TextClip(
                text=line,
                font_size=72,
                color="white",
                size=(900, None),
                method="caption",
                stroke_color="black",
                stroke_width=2
            )
            .with_position("center")
            .with_start(start_time)
            .with_duration(duration_per_line)
        )

        text_clips.append(txt)
        start_time += duration_per_line

    video = CompositeVideoClip([bg, *text_clips]).with_audio(audio)
    video.write_videofile(
        VIDEO_FILE,
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )

    print("✅ Video created")

# =========================================================
# 4. YOUTUBE UPLOAD
# =========================================================
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
                "title": "A Beautiful Moral Story for Kids ❤️ #Shorts",
                "description": (
                    "A short and sweet moral story for kids.\n\n"
                    "🧒 Age Group: 3–9 years\n"
                    "✨ Learn values with fun stories\n\n"
                    "#KidsStories #MoralStory #Shorts"
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
    print("✅ Uploaded video ID:", response["id"])

# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    print("🧠 Generating story...")
    story = generate_story()
    print("\n📖 STORY:\n", story)

    print("\n🎙 Generating voice...")
    generate_voice(story)

    print("\n🎬 Creating video...")
    create_video(story)

    print("\n📤 Uploading to YouTube...")
    upload_to_youtube()
