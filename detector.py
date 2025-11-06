"""
Objection Detection Module
===========================

Detects customer objections in call center transcriptions using regex patterns.
Analyzes text to identify objection types, intensity levels, and contextual information.

Main functionality:
- Pattern-based objection detection
- Text normalization for Spanish accents
- Intensity classification (low, medium, high)
- Context extraction (before/after objection)
- Conversation-level analysis

"""

import re
from typing import List

from core.models import Objection, Turn
from config.settings import (
    OBJECTION_PATTERNS,
    INTENSITY_MAP,
    CLIENT_SPEAKER_DEFAULT,
    CONTEXT_WINDOW_SIZE
)


class ObjectionDetector:
    """
    Detects objections in text using regex patterns.
    
    Attributes:
        rules: Dictionary of objection patterns by type and category
        intensity_map: Mapping of categories to intensity levels (1-3)
    """

    def __init__(self):
        self.rules = OBJECTION_PATTERNS
        self.intensity_map = INTENSITY_MAP

    def normalize_text(self, text: str) -> str:
        """
        Normalizes text for pattern matching.
        
        Removes Spanish accents and converts to lowercase.
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text without accents
        """
        text = text.lower()
        text = re.sub(r"[áàäâ]", "a", text)
        text = re.sub(r"[éèëê]", "e", text)
        text = re.sub(r"[íìïî]", "i", text)
        text = re.sub(r"[óòöô]", "o", text)
        text = re.sub(r"[úùüû]", "u", text)
        return text

    def detect_in_text(
        self,
        text: str,
        timestamp: str = "",
        speaker: str = "",
        context_before: str = "",
        context_after: str = "",
    ) -> List[Objection]:
        """
        Detects objections in a single text segment.
        
        Args:
            text: Text to analyze
            timestamp: Timestamp of the text segment
            speaker: Speaker identifier
            context_before: Text from previous turn (for context)
            context_after: Text from next turn (for context)
            
        Returns:
            List of detected Objection objects
        """
        normalized = self.normalize_text(text)
        objections = []

        for obj_type, categories in self.rules.items():
            for category, patterns in categories.items():
                for pattern in patterns:
                    match = re.search(pattern, normalized)
                    if match:
                        objections.append(
                            Objection(
                                type=obj_type,
                                intensity=self.intensity_map.get(category, 1),
                                matched_text=match.group(0),
                                pattern=pattern,
                                timestamp=timestamp,
                                speaker=speaker,
                                full_text=text,
                                context_before=context_before,
                                context_after=context_after,
                            )
                        )
                        break  # Only one objection per category

        return objections

    def detect_in_conversation(
        self, 
        turns: List[Turn], 
        client_speaker: int = None
    ) -> List[Objection]:
        """
        Analyzes complete conversation, focusing on client turns only.
        
        Args:
            turns: List of conversation turns
            client_speaker: Speaker number for client (default from settings)
            
        Returns:
            List of all detected objections in the conversation
        """
        if client_speaker is None:
            client_speaker = CLIENT_SPEAKER_DEFAULT
            
        all_objections = []

        for i, turn in enumerate(turns):
            if turn.speaker_num == client_speaker:
                context_before = ""
                context_after = ""

                if i > 0:
                    context_before = turns[i - 1].text[:CONTEXT_WINDOW_SIZE]
                if i < len(turns) - 1:
                    context_after = turns[i + 1].text[:CONTEXT_WINDOW_SIZE]

                objections = self.detect_in_text(
                    text=turn.text,
                    timestamp=turn.timestamp,
                    speaker=turn.speaker,
                    context_before=context_before,
                    context_after=context_after,
                )
                all_objections.extend(objections)

        return all_objections