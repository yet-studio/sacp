"""
SafeAI CodeGuard Protocol - Large Codebase Support
Implements optimizations for handling large codebases.
"""

import os
import asyncio
from typing import Dict, List, Optional, Set, Generator
from dataclasses import dataclass, field
from datetime import datetime
import xxhash
from pathlib import Path
import aiofiles
import sqlite3
import aiosqlite
import msgpack

@dataclass
class CodeFile:
    """Represents a code file"""
    path: str
    size: int
    hash: str
    last_modified: datetime
    language: str
    metadata: Dict = field(default_factory=dict)

@dataclass
class ChangeSet:
    """Represents a set of file changes"""
    files: List[str]
    hash: str
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)

class CodebaseIndex:
    """Indexes and tracks large codebases"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """Ensure database exists with correct schema"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS files (
                    path TEXT PRIMARY KEY,
                    size INTEGER,
                    hash TEXT,
                    last_modified TEXT,
                    language TEXT,
                    metadata BLOB
                );
                
                CREATE TABLE IF NOT EXISTS changes (
                    hash TEXT PRIMARY KEY,
                    files TEXT,
                    timestamp TEXT,
                    metadata BLOB
                );
                
                CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash);
                CREATE INDEX IF NOT EXISTS idx_files_language ON files(language);
                CREATE INDEX IF NOT EXISTS idx_changes_timestamp ON changes(timestamp);
            """)
        finally:
            conn.close()
    
    async def index_file(self, file_path: str) -> CodeFile:
        """Index a single file"""
        path = Path(file_path)
        stats = path.stat()
        
        # Calculate file hash
        hasher = xxhash.xxh64()
        async with aiofiles.open(file_path, "rb") as f:
            while chunk := await f.read(8192):
                hasher.update(chunk)
        
        # Determine language
        language = path.suffix.lstrip(".").lower()
        
        code_file = CodeFile(
            path=str(path),
            size=stats.st_size,
            hash=hasher.hexdigest(),
            last_modified=datetime.fromtimestamp(stats.st_mtime),
            language=language
        )
        
        # Store in database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO files
                (path, size, hash, last_modified, language, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                code_file.path,
                code_file.size,
                code_file.hash,
                code_file.last_modified.isoformat(),
                code_file.language,
                msgpack.packb(code_file.metadata)
            ))
            await db.commit()
        
        return code_file
    
    async def index_directory(
        self,
        directory: str,
        exclude_patterns: List[str] = None
    ) -> List[CodeFile]:
        """Index all files in a directory"""
        exclude_patterns = exclude_patterns or []
        files = []
        
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                
                # Check exclusions
                if any(p in file_path for p in exclude_patterns):
                    continue
                
                try:
                    code_file = await self.index_file(file_path)
                    files.append(code_file)
                except Exception as e:
                    print(f"Error indexing {file_path}: {e}")
        
        return files
    
    async def track_changes(
        self,
        files: List[str],
        metadata: Dict = None
    ) -> ChangeSet:
        """Track a set of file changes"""
        # Calculate changeset hash
        hasher = xxhash.xxh64()
        for file_path in sorted(files):
            hasher.update(file_path.encode())
        
        change_set = ChangeSet(
            files=files,
            hash=hasher.hexdigest(),
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # Store in database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO changes
                (hash, files, timestamp, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                change_set.hash,
                msgpack.packb(change_set.files),
                change_set.timestamp.isoformat(),
                msgpack.packb(change_set.metadata)
            ))
            await db.commit()
        
        return change_set
    
    async def get_file_info(self, file_path: str) -> Optional[CodeFile]:
        """Get information about a file"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM files WHERE path = ?",
                (file_path,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return CodeFile(
                        path=row[0],
                        size=row[1],
                        hash=row[2],
                        last_modified=datetime.fromisoformat(row[3]),
                        language=row[4],
                        metadata=msgpack.unpackb(row[5])
                    )
        return None
    
    async def find_similar_files(
        self,
        file_path: str,
        threshold: float = 0.8
    ) -> List[str]:
        """Find files with similar content"""
        file_info = await self.get_file_info(file_path)
        if not file_info:
            return []
        
        similar_files = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT path FROM files WHERE language = ? AND path != ?",
                (file_info.language, file_path)
            ) as cursor:
                async for row in cursor:
                    other_path = row[0]
                    similarity = await self._calculate_similarity(
                        file_path,
                        other_path
                    )
                    if similarity >= threshold:
                        similar_files.append(other_path)
        
        return similar_files
    
    async def _calculate_similarity(
        self,
        file1: str,
        file2: str
    ) -> float:
        """Calculate similarity between two files"""
        # This is a simple implementation
        # Could be improved with more sophisticated algorithms
        async with aiofiles.open(file1, "r") as f1, \
                  aiofiles.open(file2, "r") as f2:
            content1 = await f1.read()
            content2 = await f2.read()
            
            # Use Jaccard similarity of lines
            lines1 = set(content1.splitlines())
            lines2 = set(content2.splitlines())
            
            intersection = len(lines1.intersection(lines2))
            union = len(lines1.union(lines2))
            
            return intersection / union if union > 0 else 0.0
    
    async def get_codebase_stats(self) -> Dict:
        """Get statistics about the indexed codebase"""
        stats = {
            "total_files": 0,
            "total_size": 0,
            "languages": {},
            "avg_file_size": 0
        }
        
        async with aiosqlite.connect(self.db_path) as db:
            # Get total files and size
            async with db.execute(
                "SELECT COUNT(*), SUM(size) FROM files"
            ) as cursor:
                row = await cursor.fetchone()
                stats["total_files"] = row[0] or 0
                stats["total_size"] = row[1] or 0
            
            # Get language distribution
            async with db.execute(
                "SELECT language, COUNT(*) FROM files GROUP BY language"
            ) as cursor:
                async for row in cursor:
                    stats["languages"][row[0]] = row[1]
            
            # Calculate average file size
            if stats["total_files"] > 0:
                stats["avg_file_size"] = (
                    stats["total_size"] / stats["total_files"]
                )
        
        return stats
