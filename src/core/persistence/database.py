"""
SafeAI CodeGuard Protocol - Database Management
Core database functionality and connection management.
"""

from typing import Optional, Type, TypeVar, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    sessionmaker,
    Session,
    declarative_base
)
from sqlalchemy.engine import Engine
import logging
import os

T = TypeVar('T')

# Create declarative base
Base = declarative_base()


class Database:
    """Database connection and session management"""
    
    def __init__(
        self,
        url: str = 'sqlite:///sacp.db',
        echo: bool = False
    ):
        self.logger = logging.getLogger(__name__)
        self.url = url
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self.echo = echo
    
    def init(self) -> None:
        """Initialize database connection"""
        try:
            self._engine = create_engine(
                self.url,
                echo=self.echo
            )
            Base.metadata.create_all(self._engine)
            self._session_factory = sessionmaker(
                bind=self._engine,
                expire_on_commit=False
            )
            self.logger.info(f"Database initialized: {self.url}")
        
        except Exception as e:
            self.logger.error(
                f"Database initialization failed: {e}",
                exc_info=True
            )
            raise
    
    def get_session(self) -> Session:
        """Get a new database session"""
        if not self._session_factory:
            raise RuntimeError("Database not initialized")
        return self._session_factory()
    
    def add(self, obj: T) -> T:
        """Add an object to the database"""
        with self.get_session() as session:
            session.add(obj)
            session.commit()
            return obj
    
    def get(self, model: Type[T], id: int) -> Optional[T]:
        """Get an object by ID"""
        with self.get_session() as session:
            return session.get(model, id)
    
    def query(self, model: Type[T], **filters) -> list[T]:
        """Query objects with filters"""
        with self.get_session() as session:
            q = session.query(model)
            for key, value in filters.items():
                q = q.filter(getattr(model, key) == value)
            return q.all()
    
    def update(self, obj: T) -> T:
        """Update an object"""
        with self.get_session() as session:
            session.merge(obj)
            session.commit()
            return obj
    
    def delete(self, obj: T) -> None:
        """Delete an object"""
        with self.get_session() as session:
            session.delete(obj)
            session.commit()


# Global database instance
_db: Optional[Database] = None


def init_db(
    url: Optional[str] = None,
    echo: bool = False
) -> Database:
    """Initialize global database instance"""
    global _db
    
    if not url:
        # Use environment variable or default
        url = os.getenv(
            'SACP_DATABASE_URL',
            'sqlite:///sacp.db'
        )
    
    _db = Database(url=url, echo=echo)
    _db.init()
    return _db


def get_db() -> Database:
    """Get global database instance"""
    if not _db:
        raise RuntimeError(
            "Database not initialized. Call init_db() first."
        )
    return _db
