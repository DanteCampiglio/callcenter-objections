"""
Conversation Analyzer Module
============================

Analyzes complete conversations to detect and classify objections in call center
transcriptions. Processes conversation turns, identifies objection patterns, and
generates comprehensive analysis reports.

Main functionality:
- Parses conversation transcriptions
- Detects objections using ObjectionDetector
- Calculates objection statistics and metrics
- Generates structured analysis reports


"""

from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter

from .detector import ObjectionDetector
from .models import Turn, Objection
from ..io.parser import parse_transcription
from ..config.settings import (
    DEFAULT_CLIENT_SPEAKER,
    ANALYSIS_INCLUDE_TURNS,
    ANALYSIS_INCLUDE_OBJECTION_DETAILS,
    ANALYSIS_CALCULATE_INTENSITY
)


class ConversationAnalyzer:

    def __init__(self, detector: Optional[ObjectionDetector] = None):
        self.detector = detector or ObjectionDetector()

    def analyze_file(
        self,
        file_path: Path,
        client_speaker: Optional[int] = None,
        include_turns: Optional[bool] = None,
        include_details: Optional[bool] = None
    ) -> Dict:
        if client_speaker is None:
            client_speaker = DEFAULT_CLIENT_SPEAKER
        if include_turns is None:
            include_turns = ANALYSIS_INCLUDE_TURNS
        if include_details is None:
            include_details = ANALYSIS_INCLUDE_OBJECTION_DETAILS

        turns = parse_transcription(file_path)
        objections = self.detector.detect_in_conversation(turns, client_speaker)

        return self._build_result(
            file_path=file_path,
            turns=turns,
            objections=objections,
            client_speaker=client_speaker,
            include_turns=include_turns,
            include_details=include_details
        )

    def analyze_multiple_files(
        self,
        file_paths: List[Path],
        client_speaker: Optional[int] = None
    ) -> List[Dict]:
        return [
            self.analyze_file(file_path, client_speaker)
            for file_path in file_paths
        ]

    def _build_result(
        self,
        file_path: Path,
        turns: List[Turn],
        objections: List[Objection],
        client_speaker: int,
        include_turns: bool,
        include_details: bool
    ) -> Dict:
        client_turns = [t for t in turns if t.speaker_num == client_speaker]

        result = {
            "file": file_path.name,
            "total_turns": len(turns),
            "client_turns": len(client_turns),
            "objections_found": len(objections),
            "objection_types": self._count_objection_types(objections),
        }

        if ANALYSIS_CALCULATE_INTENSITY:
            result["avg_intensity"] = self._calculate_avg_intensity(objections)

        if include_details:
            result["objections"] = [obj.to_dict() for obj in objections]

        if include_turns:
            result["turns"] = [turn.to_dict() for turn in turns]

        return result

    @staticmethod
    def _count_objection_types(objections: List[Objection]) -> Dict[str, int]:
        return dict(Counter(obj.type for obj in objections))

    @staticmethod
    def _calculate_avg_intensity(objections: List[Objection]) -> float:
        if not objections:
            return 0.0
        return sum(obj.intensity for obj in objections) / len(objections)

    def get_summary_statistics(self, results: List[Dict]) -> Dict:
        if not results:
            return {
                "total_files": 0,
                "total_objections": 0,
                "avg_objections_per_file": 0.0,
                "most_common_objection": None,
                "overall_avg_intensity": 0.0
            }

        total_objections = sum(r["objections_found"] for r in results)
        all_types = []
        all_intensities = []

        for result in results:
            all_types.extend(result["objection_types"].keys())
            if "avg_intensity" in result:
                all_intensities.append(result["avg_intensity"])

        most_common = Counter(all_types).most_common(1)
        most_common_type = most_common[0][0] if most_common else None

        return {
            "total_files": len(results),
            "total_objections": total_objections,
            "avg_objections_per_file": total_objections / len(results),
            "most_common_objection": most_common_type,
            "overall_avg_intensity": (
                sum(all_intensities) / len(all_intensities)
                if all_intensities else 0.0
            )
        }