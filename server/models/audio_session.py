from typing import List, Optional
from dataclasses import dataclass, field
import torch

@dataclass
class Session:
    id: str
    language: str
    audio_buffer: List[torch.Tensor] = field(default_factory=list)
    webm_buffer: bytearray = field(default_factory=bytearray)
    webm_header: Optional[bytes] = None
    header_samples: int = 0
    last_processed_samples: int = 0
    transcript: List[dict] = field(default_factory=list)
    started_at: str = ""
    sample_rate: int = 16000