"""
Modelos de datos
"""

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class Objection:
    """Representa una objeción detectada"""

    type: str
    intensity: int
    matched_text: str
    pattern: str
    timestamp: str
    speaker: str
    full_text: str
    context_before: str = ""
    context_after: str = ""

    def to_dict(self) -> Dict:
        """Convierte a diccionario"""
        return asdict(self)


@dataclass
class Turn:
    """Representa un turno de conversación"""

    speaker: str
    speaker_num: int
    timestamp: str
    text: str

    def to_dict(self) -> Dict:
        """Convierte a diccionario"""
        return {
            "speaker": self.speaker,
            "speaker_num": self.speaker_num,
            "timestamp": self.timestamp,
            "text": self.text,
        }
