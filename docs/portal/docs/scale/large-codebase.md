# Large Codebase Support

The SafeAI CodeGuard Protocol provides specialized support for handling large codebases efficiently.

## Codebase Indexing

### SQLite Database

Uses SQLite for efficient codebase indexing:

```python
index = CodebaseIndex("codebase.db")

# Index a file
file_info = await index.index_file("path/to/file.py")

# Index directory
files = await index.index_directory(
    "project/src",
    exclude_patterns=[".git", "node_modules"]
)
```

### File Tracking

```python
# Track file changes
change_set = await index.track_changes([
    "file1.py",
    "file2.py"
])

# Get file info
file_info = await index.get_file_info("file1.py")
```

## Code Analysis

### Similar Files

Find files with similar content:

```python
similar = await index.find_similar_files(
    "file.py",
    threshold=0.8
)
```

### Codebase Statistics

Get insights about your codebase:

```python
stats = await index.get_codebase_stats()
print(f"Total files: {stats['total_files']}")
print(f"Total size: {stats['total_size']} bytes")
print(f"Languages: {stats['languages']}")
```

## Data Model

### Code File

```python
@dataclass
class CodeFile:
    path: str           # File path
    size: int          # File size in bytes
    hash: str          # Content hash
    last_modified: datetime
    language: str      # Programming language
    metadata: Dict     # Additional metadata
```

### Change Set

```python
@dataclass
class ChangeSet:
    files: List[str]   # Changed files
    hash: str          # Change set hash
    timestamp: datetime
    metadata: Dict     # Additional metadata
```

## Best Practices

1. **Indexing Strategy**:
   - Index incrementally
   - Use appropriate exclusions
   - Schedule regular reindexing

2. **Database Management**:
   - Monitor database size
   - Implement cleanup policies
   - Backup regularly

3. **Change Tracking**:
   - Track meaningful changes
   - Group related changes
   - Maintain change history

4. **Resource Usage**:
   - Control indexing batch size
   - Monitor memory usage
   - Implement timeouts

5. **Performance Tuning**:
   - Optimize queries
   - Use appropriate indexes
   - Cache frequent lookups
