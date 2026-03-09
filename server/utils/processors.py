import io
import torch
from typing import Optional
from pydub import AudioSegment
import tempfile
import os


def process_webm_bytes(webm_bytes: bytes, session_id: str, target_sample_rate: int = 16000) -> Optional[torch.Tensor]:
    try:
        print(f"Received {len(webm_bytes)} bytes for session {session_id}")
    
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
                tmp.write(webm_bytes)
                tmp_path = tmp.name
            
            audio = AudioSegment.from_file(tmp_path, format="webm")
            audio = audio.set_frame_rate(target_sample_rate).set_channels(1).set_sample_width(2)
        finally:
            if tmp_path:
                os.unlink(tmp_path)
        
        samples = torch.tensor(audio.get_array_of_samples(), dtype=torch.float32) / 32768.0
        samples = samples.unsqueeze(0)
        
        return samples
    except Exception as e:
        print(f"Error processing WebM: {e}")
        return None
