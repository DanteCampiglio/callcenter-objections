"""
Semantic Objection Detection Module
====================================

Detects customer objections using semantic similarity with sentence embeddings.
Uses a multilingual transformer model to match conversation segments against
a catalog of known objection patterns.

Main functionality:
- Converts regex patterns to natural language phrases
- Generates embeddings for objection catalog
- Segments conversations into semantic chunks
- Detects objections via cosine similarity
- Processes batch transcription files

Author: Syngenta Team
Date: 2025
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import spacy
from sentence_transformers import SentenceTransformer, util

from config.settings import (
    EMBEDDING_MODEL_PATH,
    OBJECTION_PATTERNS,
    SIMILARITY_THRESHOLD,
    MIN_SENTENCE_LENGTH,
    MIN_CHUNK_WORDS,
    SENTENCE_WINDOW_SIZE,
    SENTENCE_OVERLAP,
    IRRELEVANT_PHRASES,
    CLEAN_DATA_DIR,
    RESULTS_DIR,
    SPACY_MODEL
)


# ============================================================================
# CATALOG GENERATION
# ============================================================================

def regex_to_phrase(regex_pattern: str) -> str:
    """
    Converts regex pattern to natural language phrase.
    
    Removes regex syntax elements to create readable text for embeddings.
    
    Args:
        regex_pattern: Regex pattern string
        
    Returns:
        Cleaned phrase without regex syntax
    """
    phrase = regex_pattern
    phrase = re.sub(r"\\b", "", phrase)
    phrase = re.sub(r"\(\?:.*?\)", "", phrase)
    phrase = re.sub(r"\(.*?\?\)", "", phrase)
    phrase = re.sub(r"[\\\(\)\?\|]", " ", phrase)
    phrase = re.sub(r"\s+", " ", phrase)
    return phrase.strip()


def build_objection_catalog() -> List[Dict[str, str]]:
    """
    Builds objection catalog from pattern configurations.
    
    Returns:
        List of dictionaries with phrase, category, and type
    """
    catalog = [
        {
            "frase": regex_to_phrase(pattern),
            "categoria": category,
            "tipo": obj_type
        }
        for category, sub_patterns in OBJECTION_PATTERNS.items()
        for obj_type, pattern_list in sub_patterns.items()
        for pattern in pattern_list
        if regex_to_phrase(pattern)
    ]
    
    print(f"[INFO] Embedding catalog generated with {len(catalog)} base phrases.")
    return catalog


# ============================================================================
# EMBEDDING MODEL
# ============================================================================

class ObjectionEmbeddingDetector:
    """
    Detects objections using semantic similarity with embeddings.
    
    Attributes:
        model: Sentence transformer model for embeddings
        catalog: List of objection patterns with metadata
        base_embeddings: Pre-computed embeddings for catalog
        nlp: SpaCy language model for text processing
    """
    
    def __init__(self):
        """Initializes models and generates catalog embeddings."""
        print(f"[INFO] Loading embedding model from {EMBEDDING_MODEL_PATH}")
        self.model = SentenceTransformer(EMBEDDING_MODEL_PATH)
        
        self.catalog = build_objection_catalog()
        self.base_embeddings = self.model.encode(
            [item["frase"] for item in self.catalog],
            convert_to_tensor=True
        )
        
        print(f"[INFO] Loading SpaCy model: {SPACY_MODEL}")
        self.nlp = spacy.load(SPACY_MODEL)
    
    # ========================================================================
    # TEXT SEGMENTATION
    # ========================================================================
    
    @staticmethod
    def is_relevant(phrase: str) -> bool:
        """
        Filters out short and irrelevant phrases.
        
        Args:
            phrase: Text phrase to evaluate
            
        Returns:
            True if phrase is relevant for analysis
        """
        phrase_lower = phrase.lower().strip()
        
        if phrase_lower in IRRELEVANT_PHRASES:
            return False
        
        if len(phrase.split()) < MIN_CHUNK_WORDS:
            return False
        
        return True
    
    def segment_turn(self, text: str) -> List[str]:
        """
        Segments text into overlapping sentence windows.
        
        Groups complete sentences to maintain context while analyzing.
        
        Args:
            text: Input text to segment
            
        Returns:
            List of text chunks (sentence windows)
        """
        doc = self.nlp(text)
        sentences = [
            sent.text.strip() 
            for sent in doc.sents 
            if len(sent.text.strip()) > MIN_SENTENCE_LENGTH
        ]
        
        chunks = []
        for i in range(0, len(sentences), SENTENCE_WINDOW_SIZE - SENTENCE_OVERLAP):
            chunk = " ".join(sentences[i:i + SENTENCE_WINDOW_SIZE])
            if self.is_relevant(chunk):
                chunks.append(chunk)
        
        return chunks
    
    # ========================================================================
    # OBJECTION DETECTION
    # ========================================================================
    
    def detect_objection_semantic(
        self, 
        phrase: str, 
        threshold: float = None
    ) -> Tuple[bool, Optional[Dict], float]:
        """
        Detects objections using semantic similarity.
        
        Args:
            phrase: Text phrase to analyze
            threshold: Similarity threshold (default from settings)
            
        Returns:
            Tuple of (is_objection, matched_catalog_item, similarity_score)
        """
        if threshold is None:
            threshold = SIMILARITY_THRESHOLD
        
        phrase_embedding = self.model.encode(phrase, convert_to_tensor=True)
        similarities = util.cos_sim(phrase_embedding, self.base_embeddings)[0]
        
        max_similarity = similarities.max().item()
        max_index = similarities.argmax().item()
        
        if max_similarity >= threshold:
            match = self.catalog[max_index]
            return True, match, max_similarity
        
        return False, None, max_similarity
    
    # ========================================================================
    # TRANSCRIPTION PROCESSING
    # ========================================================================
    
    @staticmethod
    def load_clean_transcription(file_path: Path) -> List[Dict[str, str]]:
        """
        Loads and parses cleaned transcription file.
        
        Args:
            file_path: Path to transcription file
            
        Returns:
            List of turn dictionaries with text content
        """
        transcription = []
        
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Skip metadata lines
            if line.lower().startswith((
                "automatically transcribed",
                "total recording length",
                "---",
                "end of transcript",
            )):
                i += 1
                continue
            
            # Parse speaker turns
            match = re.match(r"Speaker\s+(\d+):\s*(\{\s*[\d:]+\s*\})?", line)
            if match:
                text = ""
                j = i + 1
                
                # Collect text until next speaker
                while j < len(lines) and not lines[j].startswith("Speaker"):
                    if lines[j].strip():
                        text += " " + lines[j].strip()
                    j += 1
                
                transcription.append({"texto": text.strip()})
                i = j
            else:
                i += 1
        
        return transcription
    
    def process_transcription(
        self, 
        transcription: List[Dict[str, str]], 
        filename: str,
        threshold: float = None
    ) -> List[Dict]:
        """
        Processes full transcription and detects objections.
        
        Args:
            transcription: List of turn dictionaries
            filename: Source filename for tracking
            threshold: Similarity threshold
            
        Returns:
            List of detected objection dictionaries
        """
        if threshold is None:
            threshold = SIMILARITY_THRESHOLD
        
        results = []
        chunks_processed = 0
        chunks_discarded = 0
        
        for turn in transcription:
            chunks = self.segment_turn(turn["texto"])
            
            for chunk in chunks:
                chunks_processed += 1
                is_obj, obj_ref, similarity = self.detect_objection_semantic(
                    chunk, threshold
                )
                
                if is_obj:
                    results.append({
                        "archivo_origen": filename,
                        "frase_original": chunk,
                        "patron_mas_cercano": obj_ref["frase"],
                        "categoria": obj_ref["categoria"],
                        "tipo": obj_ref["tipo"],
                        "similitud": round(similarity, 3),
                    })
                else:
                    chunks_discarded += 1
        
        print(
            f"  └─ Chunks: {chunks_processed} | "
            f"Discarded: {chunks_discarded} | "
            f"Objections: {len(results)}"
        )
        
        return results
    
    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================
    
    def process_folder(
        self, 
        folder_path: Path = None, 
        threshold: float = None
    ) -> List[Dict]:
        """
        Processes all transcription files in a folder.
        
        Args:
            folder_path: Path to folder with .txt files (default from settings)
            threshold: Similarity threshold
            
        Returns:
            List of all detected objections across files
        """
        if folder_path is None:
            folder_path = CLEAN_DATA_DIR
        
        if threshold is None:
            threshold = SIMILARITY_THRESHOLD
        
        folder = Path(folder_path)
        txt_files = sorted(folder.glob("*.txt"))
        
        if not txt_files:
            print(f"[ERROR] No .txt files found in {folder}")
            return []
        
        print(f"[INFO] Found {len(txt_files)} .txt files")
        print(f"{'='*80}\n")
        
        all_detections = []
        
        for file_path in txt_files:
            print(f"[PROCESSING] {file_path.name}")
            
            try:
                transcription = self.load_clean_transcription(file_path)
                detections = self.process_transcription(
                    transcription, 
                    filename=file_path.name,
                    threshold=threshold
                )
                all_detections.extend(detections)
                
            except Exception as e:
                print(f"  └─ [ERROR] {e}")
                continue
        
        return all_detections

