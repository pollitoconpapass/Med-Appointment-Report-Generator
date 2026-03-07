import io
import torch
from typing import Optional
from pydub import AudioSegment


def process_webm_bytes(webm_bytes: bytes, target_sample_rate: int = 16000) -> Optional[torch.Tensor]:
    try:
        audio = AudioSegment.from_file(io.BytesIO(webm_bytes), format="webm")
        audio = audio.set_frame_rate(target_sample_rate).set_channels(1).set_sample_width(2)
        
        samples = torch.tensor(audio.get_array_of_samples(), dtype=torch.float32) / 32768.0
        samples = samples.unsqueeze(0)
        
        return samples
    except Exception as e:
        print(f"Error processing WebM: {e}")
        return None