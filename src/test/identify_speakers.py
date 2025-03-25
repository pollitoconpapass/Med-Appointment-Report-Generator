import os
import time
import assemblyai as aai
from dotenv import load_dotenv


load_dotenv(dotenv_path="../../.env")

# === ELEMENTAL DATA ===
aai.settings.api_key = os.getenv("ASSEMBLY_API_KEY")
FILE_URL = "../../audios/Friends Conversation  English Conversation Practice.mp3"  # -> change it for your audio file


# === FOR IDENTIFYING SPEAKERS ===
start = time.time()
config = aai.TranscriptionConfig(speaker_labels=True, language_code="en-US")

transcriber = aai.Transcriber()
transcript = transcriber.transcribe(
  FILE_URL,
  config=config
)

for utterance in transcript.utterances:
  print(f"Speaker {utterance.speaker}: {utterance.text}")


print(f"\nTime taken: {time.time() - start} seconds")
