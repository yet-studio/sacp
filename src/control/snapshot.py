"""
SafeAI CodeGuard Protocol - Snapshot Management
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
import tempfile
import time

@dataclass
class Snapshot:
    """System state snapshot"""
    id: str
    timestamp: float
    files: Dict[str, bytes]  # path -> content
    metadata: Optional[Dict[str, Any]] = None

class SnapshotManager:
    """Manages system state snapshots for rollback"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        self.snapshots_dir = self.base_dir / ".snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)
        
        # Keep track of snapshots
        self.snapshots: Dict[str, Snapshot] = {}
        self._load_snapshots()

    def create_snapshot(self, metadata: Optional[Dict[str, Any]] = None) -> Snapshot:
        """Create a new snapshot"""
        snapshot_id = f"snapshot_{int(time.time())}"
        files = {}
        
        # Store current file states
        for root, _, filenames in os.walk(self.base_dir):
            if ".snapshots" in Path(root).parts:
                continue
                
            for filename in filenames:
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(self.base_dir)
                
                with open(file_path, 'rb') as f:
                    content = f.read()
                files[str(rel_path)] = content
        
        # Create snapshot
        snapshot = Snapshot(
            id=snapshot_id,
            timestamp=time.time(),
            files=files,
            metadata=metadata or {}
        )
        
        # Save snapshot metadata
        self._save_snapshot_metadata(snapshot)
        self.snapshots[snapshot_id] = snapshot
        return snapshot
        
    def rollback_to_snapshot(self, snapshot: Snapshot) -> None:
        """Rollback to a previous snapshot"""
        if snapshot.id not in self.snapshots:
            raise ValueError(f"Snapshot {snapshot.id} not found")
            
        # Restore files
        for rel_path, content in snapshot.files.items():
            file_path = self.base_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(content)

    def get_snapshots(self) -> List[Snapshot]:
        """Get list of available snapshots"""
        return list(self.snapshots.values())

    def _save_snapshot_metadata(self, snapshot: Snapshot):
        """Save snapshot metadata to disk"""
        metadata_file = self.snapshots_dir / f"{snapshot.id}.json"
        with open(metadata_file, 'w') as f:
            json.dump({
                'id': snapshot.id,
                'timestamp': snapshot.timestamp,
                'metadata': snapshot.metadata
            }, f, indent=2)

    def _load_snapshots(self):
        """Load existing snapshots from disk"""
        if not self.snapshots_dir.exists():
            return
            
        for metadata_file in self.snapshots_dir.glob("*.json"):
            try:
                with open(metadata_file) as f:
                    data = json.load(f)
                    snapshot = Snapshot(
                        id=data['id'],
                        timestamp=data['timestamp'],
                        files={},  # Load files from disk
                        metadata=data.get('metadata')
                    )
                    self.snapshots[snapshot.id] = snapshot
            except Exception as e:
                logging.error(f"Error loading snapshot {metadata_file}: {e}")
