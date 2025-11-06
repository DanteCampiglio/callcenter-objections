"""
Call Summarizer Module
======================
Generates concise summaries of call transcripts using AWS Bedrock Claude.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import boto3
import pandas as pd

logger = logging.getLogger(__name__)


class CallSummarizer:
    """Summarizes call transcripts using AWS Bedrock Claude."""
    
    def __init__(
        self,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        region: str = "eu-central-1",
        max_tokens: int = 150,
        temperature: float = 0.0
    ):
        """
        Initialize Bedrock client.
        
        Args:
            model_id: Claude model identifier
            region: AWS region
            max_tokens: Maximum tokens for summary
            temperature: Model temperature (0.0 = deterministic)
        """
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        logger.info(f"Initializing Bedrock client in {region}")
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=region
        )
    
    def summarize(self, text: str) -> Optional[str]:
        """
        Generate summary for transcript text.
        
        Args:
            text: Full transcript text
            
        Returns:
            Two-line summary or None if error
        """
        prompt = f"""Resume la siguiente conversación telefónica en español en un máximo de dos líneas, destacando lo más importante:

{text}"""
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}]
        })
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body
            )
            output = json.loads(response["body"].read())
            return output["content"][0]["text"].strip()
        
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return None
    
    def process_directory(self, input_dir: Path) -> pd.DataFrame:
        """
        Process all transcript files in directory.
        
        Args:
            input_dir: Directory with .txt transcripts
            
        Returns:
            DataFrame with filenames and summaries
        """
        logger.info(f"Processing transcripts from: {input_dir}")
        
        results = []
        
        for file_path in input_dir.glob("*.txt"):
            try:
                text = file_path.read_text(encoding="utf-8")
                summary = self.summarize(text)
                
                if summary:
                    results.append({
                        "archivo": file_path.name,
                        "resumen": summary
                    })
                    logger.info(f"✅ {file_path.name}")
                else:
                    logger.warning(f"⚠️ No summary for {file_path.name}")
            
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
        
        logger.info(f"✅ Generated {len(results)} summaries")
        return pd.DataFrame(results)