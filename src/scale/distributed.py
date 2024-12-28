"""
SafeAI CodeGuard Protocol - Distributed Validation System
Implements distributed processing for large-scale code validation.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import aiohttp
import aioredis
import msgpack
from pathlib import Path

@dataclass
class ValidationTask:
    """Represents a validation task"""
    task_id: str
    file_path: str
    validation_type: str
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

@dataclass
class ValidationResult:
    """Result of a validation task"""
    task_id: str
    status: str
    issues: List[Dict]
    execution_time: float
    worker_id: str
    completed_at: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

class ValidationWorker:
    """Worker node for distributed validation"""
    
    def __init__(
        self,
        worker_id: str,
        redis_url: str,
        queue_name: str = "validation_tasks"
    ):
        self.worker_id = worker_id
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.running = False
        self.redis: Optional[aioredis.Redis] = None
        self.validators: Dict[str, Callable] = {}
    
    async def connect(self):
        """Connect to Redis"""
        self.redis = await aioredis.from_url(self.redis_url)
    
    async def register_validator(
        self,
        validation_type: str,
        validator: Callable
    ):
        """Register a validation function"""
        self.validators[validation_type] = validator
    
    async def start(self):
        """Start processing tasks"""
        if not self.redis:
            await self.connect()
        
        self.running = True
        while self.running:
            try:
                # Get task from queue
                task_data = await self.redis.blpop(self.queue_name, timeout=1)
                if not task_data:
                    continue
                
                # Deserialize task
                task_dict = msgpack.unpackb(task_data[1])
                task = ValidationTask(**task_dict)
                
                # Process task
                result = await self.process_task(task)
                
                # Store result
                result_key = f"result:{task.task_id}"
                await self.redis.set(
                    result_key,
                    msgpack.packb(result.__dict__),
                    ex=3600  # Expire after 1 hour
                )
                
            except Exception as e:
                # Log error and continue
                print(f"Error processing task: {e}")
    
    async def process_task(self, task: ValidationTask) -> ValidationResult:
        """Process a validation task"""
        start_time = datetime.now()
        issues = []
        
        try:
            if task.validation_type in self.validators:
                validator = self.validators[task.validation_type]
                issues = await validator(task.file_path)
            
            status = "completed"
        except Exception as e:
            status = "failed"
            issues = [{"error": str(e)}]
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return ValidationResult(
            task_id=task.task_id,
            status=status,
            issues=issues,
            execution_time=execution_time,
            worker_id=self.worker_id
        )
    
    async def stop(self):
        """Stop the worker"""
        self.running = False
        if self.redis:
            await self.redis.close()

class ValidationOrchestrator:
    """Orchestrates distributed validation tasks"""
    
    def __init__(
        self,
        redis_url: str,
        queue_name: str = "validation_tasks",
        max_concurrent: int = 100
    ):
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.max_concurrent = max_concurrent
        self.redis: Optional[aioredis.Redis] = None
        self.active_tasks: Dict[str, ValidationTask] = {}
    
    async def connect(self):
        """Connect to Redis"""
        self.redis = await aioredis.from_url(self.redis_url)
    
    async def submit_task(
        self,
        file_path: str,
        validation_type: str,
        priority: int = 0,
        metadata: Dict = None
    ) -> str:
        """Submit a validation task"""
        if not self.redis:
            await self.connect()
        
        task = ValidationTask(
            task_id=str(uuid.uuid4()),
            file_path=file_path,
            validation_type=validation_type,
            priority=priority,
            metadata=metadata or {}
        )
        
        # Store task in Redis
        await self.redis.rpush(
            self.queue_name,
            msgpack.packb(task.__dict__)
        )
        
        self.active_tasks[task.task_id] = task
        return task.task_id
    
    async def get_result(
        self,
        task_id: str,
        timeout: int = 30
    ) -> Optional[ValidationResult]:
        """Get result of a validation task"""
        if not self.redis:
            await self.connect()
        
        result_key = f"result:{task_id}"
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            result_data = await self.redis.get(result_key)
            if result_data:
                result_dict = msgpack.unpackb(result_data)
                return ValidationResult(**result_dict)
            await asyncio.sleep(0.1)
        
        return None
    
    async def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        if not self.redis:
            await self.connect()
        
        queue_length = await self.redis.llen(self.queue_name)
        active_tasks = len(self.active_tasks)
        
        return {
            "queue_length": queue_length,
            "active_tasks": active_tasks
        }
    
    async def clear_queue(self):
        """Clear the validation queue"""
        if not self.redis:
            await self.connect()
        
        await self.redis.delete(self.queue_name)
        self.active_tasks.clear()
    
    async def close(self):
        """Close connections"""
        if self.redis:
            await self.redis.close()
