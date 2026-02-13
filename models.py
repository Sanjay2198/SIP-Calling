"""
Database models for SIP client
Stores contacts and call history
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional, cast
import yaml

Base = declarative_base()

class Contact(Base):
    """Contact information"""
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    sip_uri = Column(String(200), nullable=False, unique=True)
    phone_number = Column(String(20))
    email = Column(String(100))
    notes = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        created_at = cast(Optional[datetime], self.created_at)
        updated_at = cast(Optional[datetime], self.updated_at)
        return {
            'id': self.id,
            'name': self.name,
            'sip_uri': self.sip_uri,
            'phone_number': self.phone_number,
            'email': self.email,
            'notes': self.notes,
            'created_at': created_at.isoformat() if created_at is not None else None,
            'updated_at': updated_at.isoformat() if updated_at is not None else None
        }


class CallHistory(Base):
    """Call history records"""
    __tablename__ = 'call_history'
    
    id = Column(Integer, primary_key=True)
    remote_uri = Column(String(200), nullable=False)
    direction = Column(String(20), nullable=False)  # 'inbound' or 'outbound'
    status = Column(String(50), nullable=False)  # 'answered', 'missed', 'rejected', 'failed'
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    duration = Column(Float, default=0.0)  # in seconds
    recording_path = Column(String(500))
    transcript = Column(String)
    summary = Column(String(1000))
    sentiment = Column(String(50))
    notes = Column(String(500))
    
    def to_dict(self):
        start_time = cast(Optional[datetime], self.start_time)
        end_time = cast(Optional[datetime], self.end_time)
        return {
            'id': self.id,
            'remote_uri': self.remote_uri,
            'direction': self.direction,
            'status': self.status,
            'start_time': start_time.isoformat() if start_time is not None else None,
            'end_time': end_time.isoformat() if end_time is not None else None,
            'duration': self.duration,
            'recording_path': self.recording_path,
            'transcript': self.transcript,
            'summary': self.summary,
            'sentiment': self.sentiment,
            'notes': self.notes
        }


# Database initialization
def init_db(config_path='config.yaml'):
    """Initialize database with tables"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    db_url = config.get('database', {}).get('url', 'sqlite:///sip_client.db')
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    return Session()


def get_session(config_path='config.yaml'):
    """Get database session"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    db_url = config.get('database', {}).get('url', 'sqlite:///sip_client.db')
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == '__main__':
    # Initialize database
    session = init_db()
    print("Database initialized successfully!")
    print(f"Tables created: {Base.metadata.tables.keys()}")
