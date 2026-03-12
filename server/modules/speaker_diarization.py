import torch
from pyannote.audio import Pipeline

class SpeakerDiarization:
    def __init__(self, api_key: str):
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=api_key
        )
        
        # GPU if available (not in my local pipipi)
        if torch.cuda.is_available():
            self.pipeline.to(torch.device("cuda"))
        elif torch.backends.mps.is_available():
            self.pipeline.to(torch.device("mps")) # -> For Apple Silicon

    def diarize(self, audio_data: torch.Tensor, sample_rate: int = 16000, num_speakers: int = None, min_speakers: int = None, max_speakers: int = None):
        # Audio has to be mono and has shape (1, samples)
        if audio_data.dim() == 1:
            audio_data = audio_data.unsqueeze(0)
        elif audio_data.dim() == 2 and audio_data.shape[0] > 1:
            audio_data = torch.mean(audio_data, dim=0, keepdim=True)
            
        # The pipeline expects a dictionary with "waveform" and "sample_rate" when passing a torch tensor directly
        params = {}
        if num_speakers is not None:
            params["num_speakers"] = num_speakers
        if min_speakers is not None:
            params["min_speakers"] = min_speakers
        if max_speakers is not None:
            params["max_speakers"] = max_speakers

        diarization = self.pipeline({"waveform": audio_data, "sample_rate": sample_rate}, **params)
        
        if diarization is None:
            return []
            
        if hasattr(diarization, "speaker_diarization"):
            annotation = diarization.speaker_diarization
        else:
            annotation = diarization

        results = []
        if hasattr(annotation, "itertracks"):
            for segment, _, speaker in annotation.itertracks(yield_label=True):
                results.append({
                    "start": segment.start,
                    "end": segment.end,
                    "speaker": speaker
                })
            
        return results
