# Medical Appointment Report Generator (MARGe) 🩺💊

A web application that transcribes medical appointments and generates summarized medical reports using AI technology.

## Features

- Audio transcription support with Whisper (via Groq):
  - Spanish
  - English

- Speaker diarization (pyannote.audio)
- Detect 3 seconds of silence and generate a chunk (silero-vad)
- Add a 2s overlap from previous
- Medical report generation with GPT-OSS LLM(via Groq)
- Editable report from the frontend (Milkdown)

## Project Flow

```
Microphone Input
      ↓
  silero-vad  ←— detects silence of 5 seconds
      ↓
 Audio Chunk (with 2s overlap from previous)
      ↓
  Groq Whisper API  ←— transcribes chunk
      ↓
 Transcript Queue  ←— appends in order
      ↓ (live, streaming to UI)
 Live Transcript Display  ←— doctor can see it updating
      ↓
 [Doctor presses "End Appointment"]
      ↓
 Full Transcript → Groq LLM (GPT-OSS)
      ↓
 Structured Medical Report (Markdown format)
      ↓
 Editable Report UI  ←— doctor reviews, edits, saves (using Mildown)
```

## Project Plan

### Websocket: /ws/audio

streams - Client raw audio (e.g., 1-second chunks)

- Server buffers audio in memory
- Server runs VAD on buffer every chunk
- On 5s silence: create chunk (with 2s overlap), transcribe, push transcript back
- Server keeps sliding window to maintain overlap

### REST Endpoins

1. POST `/appointment/start` - Initialize session, laguage, buffer
2. POST `/appointment/end` - Stop, save transcript return full transcript
3. POST `/report/generate` - Generate medical report from full transcript (streaming)
