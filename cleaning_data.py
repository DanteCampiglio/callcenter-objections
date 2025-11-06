"""
Text Cleaning Module
====================

Cleans and normalizes call center transcriptions by removing filler words,
normalizing accents, and standardizing text format while preserving speaker
information and timestamps.

Main functionality:
- Removes Spanish filler words (muletillas)
- Normalizes Unicode characters and accents
- Cleans punctuation and extra whitespace
- Preserves speaker labels and timestamps
- Batch processes transcription files

Author: Syngenta Team
Date: 2025
"""

import re
import unicodedata
from pathlib import Path
from typing import List

from config.settings import (
    FILLER_WORDS,
    RAW_DATA_DIR,
    CLEAN_DATA_DIR,
    PRESERVE_SPEAKER_FORMAT,
    NORMALIZE_ACCENTS,
    REMOVE_PUNCTUATION
)


FILLER_WORDS_RE = re.compile(
    r"(" + "|".join(FILLER_WORDS) + r")",
    flags=re.IGNORECASE
)


def normalize_accents(text: str) -> str:
    if not NORMALIZE_ACCENTS:
        return text
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def clean_text(text: str) -> str:
    text = text.lower()
    text = normalize_accents(text)
    text = FILLER_WORDS_RE.sub(" ", text)
    
    if REMOVE_PUNCTUATION:
        text = re.sub(r"[^\w\s]", " ", text)
    
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_transcription_with_speakers(text: str) -> str:
    if not PRESERVE_SPEAKER_FORMAT:
        return clean_text(text)
    
    lines = text.splitlines()
    result = []
    speaker_pattern = re.compile(r"^(Speaker\s+\d+:.*?\})\s*(.*)$")

    for line in lines:
        match = speaker_pattern.match(line)
        if match:
            header = match.group(1)
            content = match.group(2)
            clean_content = clean_text(content) if content.strip() else ""
            result.append(f"{header} {clean_content}".strip())
        else:
            if line.strip() and not line.strip().startswith("---"):
                result.append(clean_text(line))
            else:
                result.append(line)
    
    return "\n".join(result)


def process_transcriptions():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    CLEAN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    files = list(RAW_DATA_DIR.glob("*.txt"))
    print(f"Found {len(files)} files in {RAW_DATA_DIR}")

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        clean_text_result = clean_transcription_with_speakers(text)

        destination = CLEAN_DATA_DIR / file.name
        with open(destination, "w", encoding="utf-8") as f:
            f.write(clean_text_result)

        print(f"Cleaned and saved: {destination}")


if __name__ == "__main__":
    process_transcriptions()