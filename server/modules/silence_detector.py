import os
import torch
import torchaudio
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps


class SilenceDetector:
    def __init__(self):
        self.model = load_silero_vad()
        self.sample_rate = 16000

    def get_timestamps(self, audio_path):
        wav = read_audio(audio_path)
        speech_timestamps = get_speech_timestamps(
            wav,
            self.model,
            return_seconds=True,
        )
        return speech_timestamps

    def get_timestamps_from_tensor(self, audio_tensor: torch.Tensor, sample_rate: int = 16000):
        if audio_tensor.shape[0] > 1:
            audio_tensor = audio_tensor.mean(dim=0, keepdim=True)
        
        audio_tensor = audio_tensor.squeeze()
        if audio_tensor.dim() == 0:
            audio_tensor = audio_tensor.unsqueeze(0)
        
        speech_timestamps = get_speech_timestamps(
            audio_tensor,
            self.model,
            sampling_rate=sample_rate,
            return_seconds=True,
        )
        return speech_timestamps
    
    def detect_silence(self, audio_path, seconds=2):
        speech_timestamps = self.get_timestamps(audio_path)
        silence_periods = []
        
        if not speech_timestamps:
            return silence_periods
            
        for i in range(len(speech_timestamps) - 1):
            current_end = speech_timestamps[i]['end']
            next_start = speech_timestamps[i + 1]['start']
            if next_start - current_end >= seconds:
                silence_periods.append({
                    'start': current_end,
                    'end': next_start,
                    'speech_before': speech_timestamps[i],
                    'speech_after': speech_timestamps[i + 1]
                })
        
        return silence_periods

    def create_chunk(self, audio_path, start_time, end_time, overlap_seconds=2, output_path=None):
        waveform, sr = torchaudio.load(audio_path)
        
        if sr != self.sample_rate:
            waveform = torchaudio.functional.resample(waveform, sr, self.sample_rate)
            sr = self.sample_rate
        
        start_sample = int((start_time - overlap_seconds) * sr)
        if start_sample < 0:
            start_sample = 0
        
        end_sample = int(end_time * sr)
        
        chunk = waveform[:, start_sample:end_sample]
        
        if output_path is None:
            output_path = f"chunk_{start_time}_{end_time}.wav"
        
        torchaudio.save(output_path, chunk, self.sample_rate)
        return output_path

    def get_chunks(self, audio_path, silence_threshold=5, overlap_seconds=2):
        speech_timestamps = self.get_timestamps(audio_path)
        chunks = []
        
        if not speech_timestamps:
            return chunks
        
        for i in range(len(speech_timestamps) - 1):
            current_end = speech_timestamps[i]['end']
            next_start = speech_timestamps[i + 1]['start']
            
            if next_start - current_end >= silence_threshold:
                chunk_info = {
                    'start_time': current_end - overlap_seconds,
                    'end_time': next_start,
                    'silence_start': current_end,
                    'silence_end': next_start
                }
                chunks.append(chunk_info)
        
        return chunks

    def process_audio_to_chunks(self, audio_path, output_dir="chunks", silence_threshold=5, overlap_seconds=2):
        os.makedirs(output_dir, exist_ok=True)
        
        chunks = self.get_chunks(audio_path, silence_threshold, overlap_seconds)
        chunk_files = []
        
        for i, chunk_info in enumerate(chunks):
            output_path = os.path.join(output_dir, f"chunk_{i}.wav")
            self.create_chunk(
                audio_path,
                chunk_info['start_time'],
                chunk_info['end_time'],
                overlap_seconds,
                output_path
            )
            chunk_files.append({
                'file': output_path,
                'start': chunk_info['start_time'],
                'end': chunk_info['end_time']
            })
        
        return chunk_files
