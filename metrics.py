"""
Call Metrics Analyzer - Compact Version
========================================
Analyzes call transcripts for speaker time and sentiment.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from transformers import pipeline

logger = logging.getLogger(__name__)


class CallAnalyzer:
    """Analyzes call transcripts for speaker metrics and sentiment."""
    
    def __init__(self, model_name: str = "pysentimiento/robertuito-sentiment-analysis"):
        logger.info(f"Loading sentiment model: {model_name}")
        self.sentiment_analyzer = pipeline("sentiment-analysis", model=model_name)
        self.pattern = r"(Speaker\s\d+):\s*\{\s*(\d+:\d+)\s*\}\s*(.*)"
    
    @staticmethod
    def time_to_seconds(timestamp: str) -> int:
        """Convert 'm:ss' to seconds."""
        m, s = timestamp.split(":")
        return int(m) * 60 + int(s)
    
    def analyze_sentiment(self, texts: List[str]) -> float:
        """Calculate average sentiment (-1 to 1)."""
        if not texts:
            return 0.0
        
        results = self.sentiment_analyzer(texts, truncation=True, max_length=128, batch_size=8)
        score_map = {"POS": 1, "NEG": -1, "NEU": 0}
        scores = [score_map.get(r["label"], 0) for r in results]
        return round(sum(scores) / len(scores), 3)
    
    def parse_transcript(self, text: str) -> Optional[Dict]:
        """Parse transcript and extract metrics."""
        matches = re.findall(self.pattern, text)
        if not matches:
            return None
        
        s1_time, s2_time = 0, 0
        s1_texts, s2_texts = [], []
        
        times = [self.time_to_seconds(m[1]) for m in matches]
        times.append(times[-1])
        
        for i, (speaker, _, speech) in enumerate(matches):
            duration = max(0, times[i + 1] - times[i])
            
            if speaker == "Speaker 1":
                s1_time += duration
                s1_texts.append(speech)
            elif speaker == "Speaker 2":
                s2_time += duration
                s2_texts.append(speech)
        
        return {
            "duracion_total_seg": max(times),
            "tiempo_speaker1_seg": s1_time,
            "tiempo_speaker2_seg": s2_time,
            "sentimiento_speaker1": self.analyze_sentiment(s1_texts),
            "sentimiento_speaker2": self.analyze_sentiment(s2_texts),
        }
    
    def process_directory(self, input_dir: Path) -> pd.DataFrame:
        """Process all .txt files in directory."""
        logger.info(f"Processing transcripts from: {input_dir}")
        
        results = []
        for file_path in input_dir.glob("*.txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    metrics = self.parse_transcript(f.read())
                
                if metrics:
                    metrics["archivo"] = file_path.name
                    results.append(metrics)
                    logger.info(f"✅ {file_path.name}")
            except Exception as e:
                logger.error(f"Error in {file_path.name}: {e}")
        
        logger.info(f"✅ Processed {len(results)} files")
        return pd.DataFrame(results)