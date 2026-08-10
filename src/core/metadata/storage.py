"""
Call metadata storage system for restaurant booking automation
Stores call data in JSON format for browser-use consumption
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import asyncio
from pydantic import BaseModel, Field
import uuid

logger = logging.getLogger(__name__)

class CallMetadata(BaseModel):
    """Model for call metadata"""
    call_id: str = Field(..., description="Unique call identifier")
    restaurant_id: str = Field(..., description="Restaurant identifier")
    customer_phone: str = Field(..., description="Customer phone number")
    customer_name: Optional[str] = Field(None, description="Customer name if provided")
    booking_request: Dict[str, Any] = Field(..., description="Extracted booking details")
    call_status: str = Field(..., description="Current call status")
    transcript: Optional[str] = Field(None, description="Call transcript")
    recording_url: Optional[str] = Field(None, description="Call recording URL")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Call timestamp")
    processing_status: str = Field(default="pending", description="Processing status for automation")
    automation_result: Optional[Dict[str, Any]] = Field(None, description="Result of browser automation")
    retry_count: int = Field(default=0, description="Number of automation retries")
    priority: str = Field(default="normal", description="Processing priority")

class MetadataStorage:
    """Production-ready metadata storage system"""
    
    def __init__(self, storage_dir: str = "call_metadata"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.pending_dir = self.storage_dir / "pending"
        self.processing_dir = self.storage_dir / "processing"
        self.completed_dir = self.storage_dir / "completed"
        self.failed_dir = self.storage_dir / "failed"
        
        # Create subdirectories
        for dir_path in [self.pending_dir, self.processing_dir, self.completed_dir, self.failed_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self._lock = asyncio.Lock()
    
    async def save_call_metadata(self, metadata: CallMetadata) -> str:
        """Save call metadata to JSON file"""
        async with self._lock:
            filename = f"{metadata.call_id}.json"
            filepath = self.pending_dir / filename
            
            # Convert datetime to ISO format for JSON serialization
            metadata_dict = metadata.dict()
            metadata_dict['timestamp'] = metadata.timestamp.isoformat()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved call metadata: {filename}")
            return str(filepath)
    
    async def get_pending_calls(self, limit: int = 50) -> List[CallMetadata]:
        """Get list of pending calls for processing"""
        async with self._lock:
            pending_calls = []
            
            for filepath in self.pending_dir.glob("*.json"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Convert ISO timestamp back to datetime
                    data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                    metadata = CallMetadata(**data)
                    pending_calls.append(metadata)
                    
                    if len(pending_calls) >= limit:
                        break
                        
                except Exception as e:
                    logger.error(f"Error reading {filepath}: {e}")
            
            # Sort by timestamp and priority
            priority_order = {"high": 0, "normal": 1, "low": 2}
            pending_calls.sort(key=lambda x: (priority_order.get(x.priority, 1), x.timestamp))
            
            return pending_calls
    
    async def move_to_processing(self, call_id: str) -> bool:
        """Move call from pending to processing"""
        async with self._lock:
            src = self.pending_dir / f"{call_id}.json"
            dst = self.processing_dir / f"{call_id}.json"
            
            if src.exists():
                src.rename(dst)
                logger.info(f"Moved {call_id} to processing")
                return True
            return False
    
    async def move_to_completed(self, call_id: str, automation_result: Dict[str, Any]) -> bool:
        """Move call from processing to completed with results"""
        async with self._lock:
            src = self.processing_dir / f"{call_id}.json"
            dst = self.completed_dir / f"{call_id}.json"
            
            if src.exists():
                # Update metadata with automation results
                with open(src, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                data['processing_status'] = 'completed'
                data['automation_result'] = automation_result
                data['completed_at'] = datetime.utcnow().isoformat()
                
                # Save to completed
                with open(dst, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Remove from processing
                src.unlink()
                
                logger.info(f"Completed automation for {call_id}")
                return True
            return False
    
    async def move_to_failed(self, call_id: str, error: str) -> bool:
        """Move call from processing to failed with error details"""
        async with self._lock:
            src = self.processing_dir / f"{call_id}.json"
            dst = self.failed_dir / f"{call_id}.json"
            
            if src.exists():
                # Update metadata with error
                with open(src, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                data['processing_status'] = 'failed'
                data['error'] = error
                data['failed_at'] = datetime.utcnow().isoformat()
                data['retry_count'] = data.get('retry_count', 0) + 1
                
                # Save to failed
                with open(dst, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Remove from processing
                src.unlink()
                
                logger.error(f"Failed automation for {call_id}: {error}")
                return True
            return False
    
    async def retry_failed_calls(self, max_retries: int = 3) -> int:
        """Retry failed calls that haven't exceeded max retries"""
        async with self._lock:
            retried_count = 0
            
            for filepath in self.failed_dir.glob("*.json"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    retry_count = data.get('retry_count', 0)
                    if retry_count < max_retries:
                        # Move back to pending
                        call_id = data['call_id']
                        dst = self.pending_dir / f"{call_id}.json"
                        filepath.rename(dst)
                        
                        # Reset processing status
                        with open(dst, 'r', encoding='utf-8') as f:
                            retry_data = json.load(f)
                        retry_data['processing_status'] = 'pending'
                        retry_data.pop('error', None)
                        
                        with open(dst, 'w', encoding='utf-8') as f:
                            json.dump(retry_data, f, indent=2, ensure_ascii=False)
                        
                        retried_count += 1
                        logger.info(f"Retrying call {call_id} (attempt {retry_count + 1})")
                        
                except Exception as e:
                    logger.error(f"Error retrying {filepath}: {e}")
            
            return retried_count
    
    async def get_call_metadata(self, call_id: str) -> Optional[CallMetadata]:
        """Get specific call metadata by ID"""
        for directory in [self.pending_dir, self.processing_dir, self.completed_dir, self.failed_dir]:
            filepath = directory / f"{call_id}.json"
            if filepath.exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                    return CallMetadata(**data)
                except Exception as e:
                    logger.error(f"Error reading {filepath}: {e}")
        
        return None
    
    async def cleanup_old_files(self, days: int = 30) -> int:
        """Clean up old completed and failed files"""
        async with self._lock:
            cleaned_count = 0
            cutoff_date = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
            
            for directory in [self.completed_dir, self.failed_dir]:
                for filepath in directory.glob("*.json"):
                    if filepath.stat().st_mtime < cutoff_date:
                        filepath.unlink()
                        cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old files")
            return cleaned_count

# Global storage instance
metadata_storage = MetadataStorage()
