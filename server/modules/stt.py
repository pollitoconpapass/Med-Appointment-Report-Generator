import json
import io
from groq import Groq
from typing import Union

class WhisperSTT:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = Groq(api_key=self.api_key)

    def stt(self, audio_input: Union[str, io.BytesIO], language="en"):
        if isinstance(audio_input, str):
            file = open(audio_input, "rb")
            close_file = True
        else:
            file = audio_input
            close_file = False
        
        try:
            transcription = self.client.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3-turbo", 
                response_format="verbose_json",
                language=language,
                temperature=0.0
            )
            return json.dumps(transcription, indent=2, default=str)
        finally:
            if close_file:
                file.close()
