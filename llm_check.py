"""
LLM Objection Validator Module
================================

Validates sales objections detected by embeddings using AWS Bedrock Claude model.
Filters false positives through advanced semantic analysis.

Main functionality:
- Queries AWS Bedrock Claude for objection validation
- Processes batch detections from JSON
- Generates validated CSV reports with proper column ordering

Author: Syngenta Team
Date: 2025
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
import boto3
from botocore.exceptions import ClientError

from config.settings import (
    BEDROCK_REGION,
    BEDROCK_MODEL_ID,
    BEDROCK_MAX_TOKENS,
    BEDROCK_TEMPERATURE,
    LLM_VALIDATION_KEYWORDS,
    OBJECTION_PROMPT_TEMPLATE,
    OUTPUT_COLUMNS_ORDER
)

logger = logging.getLogger(__name__)


# ============================================================================
# LLM VALIDATOR CLASS
# ============================================================================

class BedrockObjectionValidator:
    """
    Validates sales objections using AWS Bedrock Claude model.
    
    Attributes:
        bedrock_runtime: Boto3 Bedrock client
        model_id: Bedrock model identifier
        max_tokens: Maximum response tokens
        temperature: Model temperature (0.0 = deterministic)
    """
    
    def __init__(
        self,
        region_name: str = None,
        model_id: str = None,
        max_tokens: int = None,
        temperature: float = None
    ):
        """
        Initialize Bedrock client with configuration.
        
        Args:
            region_name: AWS region (default from settings)
            model_id: Bedrock model ID (default from settings)
            max_tokens: Max response tokens (default from settings)
            temperature: Model temperature (default from settings)
        """
        self.region_name = region_name or BEDROCK_REGION
        self.model_id = model_id or BEDROCK_MODEL_ID
        self.max_tokens = max_tokens or BEDROCK_MAX_TOKENS
        self.temperature = temperature or BEDROCK_TEMPERATURE
        
        logger.info(f"Initializing Bedrock client (region: {self.region_name})")
        
        try:
            self.bedrock_runtime = boto3.client(
                service_name="bedrock-runtime",
                region_name=self.region_name
            )
            logger.info("✅ Bedrock client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise
    
    # ========================================================================
    # BEDROCK QUERY
    # ========================================================================
    
    def query_bedrock(self, prompt: str) -> Optional[str]:
        """
        Query AWS Bedrock model with prompt.
        
        Args:
            prompt: Input prompt for the model
            
        Returns:
            Model response text or None if error
        """
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
        })

        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=body
            )
            response_body = json.loads(response["body"].read())
            return response_body["content"][0]["text"].strip()
            
        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error querying Bedrock: {e}")
            return None
    
    # ========================================================================
    # OBJECTION VALIDATION
    # ========================================================================
    
    def validate_objection(
        self, 
        detection: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Validate if a phrase is a sales objection using LLM.
        
        Args:
            detection: Detection dictionary with phrase and metadata
            
        Returns:
            Updated detection with LLM validation or None if error
        """
        phrase = detection.get("frase_original", "")
        category = detection.get("categoria", "")
        obj_type = detection.get("tipo", "")
        
        # Build prompt from template
        prompt = OBJECTION_PROMPT_TEMPLATE.format(
            category=category,
            obj_type=obj_type,
            phrase=phrase
        )
        
        # Query LLM
        response = self.query_bedrock(prompt)
        
        if response is None:
            logger.warning(f"No response from LLM for phrase: {phrase[:50]}...")
            return None
        
        response_clean = response.strip().upper()
        logger.info(f"[{category}] {phrase[:60]}... → {response_clean}")
        
        # Flexible validation with multiple keywords
        is_objection = any(
            keyword in response_clean 
            for keyword in LLM_VALIDATION_KEYWORDS
        )
        
        # Add validation results
        result = detection.copy()
        result["respuesta_llm"] = response_clean
        result["validado_llm"] = is_objection
        
        return result
    
    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================
    
    def process_detections(
        self, 
        detections: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Process multiple detections with LLM validation.
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            DataFrame with validated objections only (formatted columns)
        """
        validated_results = []
        total = len(detections)
        
        logger.info(f"Processing {total} detections with LLM validation...")
        
        for i, detection in enumerate(detections, 1):
            logger.info(f"\n[{i}/{total}]")
            
            try:
                validation = self.validate_objection(detection)
                
                # Only keep validated objections
                if validation and validation.get("validado_llm"):
                    validated_results.append(validation)
                    
            except Exception as e:
                logger.error(f"Error processing detection {i}: {e}")
                continue
        
        logger.info(
            f"\n✅ Validation complete: {len(validated_results)}/{total} "
            f"objections confirmed"
        )
        
        # Convert to DataFrame and format columns
        df = pd.DataFrame(validated_results)
        return self._format_columns(df)
    
    def process_from_json(
        self, 
        json_path: Path
    ) -> pd.DataFrame:
        """
        Load detections from JSON and process with LLM validation.
        
        Args:
            json_path: Path to JSON file with detections
            
        Returns:
            DataFrame with validated objections (formatted)
        """
        logger.info(f"Loading detections from {json_path}")
        
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                detections = json.load(f)
            
            logger.info(f"Loaded {len(detections)} detections")
            return self.process_detections(detections)
            
        except FileNotFoundError:
            logger.error(f"File not found: {json_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            raise
    
    # ========================================================================
    # OUTPUT FORMATTING (PRIVATE)
    # ========================================================================
    
    @staticmethod
    def _format_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Reorder DataFrame columns for better readability.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with reordered columns
        """
        if df.empty:
            return df
        
        # Keep specified columns that exist
        existing_cols = [
            col for col in OUTPUT_COLUMNS_ORDER 
            if col in df.columns
        ]
        
        # Add extra columns not in order list
        extra_cols = [
            col for col in df.columns 
            if col not in OUTPUT_COLUMNS_ORDER
        ]
        
        return df[existing_cols + extra_cols]