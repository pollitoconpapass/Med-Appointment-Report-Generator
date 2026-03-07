import torch
from typing import List
from dataclasses import dataclass, field

@dataclass
class Session:
    id: str
    language: str
    audio_buffer: List[torch.Tensor] = field(default_factory=list)
    transcript: List[dict] = field(default_factory=list)
    started_at: str = ""
    sample_rate: int = 16000