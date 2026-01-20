from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    """User model for storing user preferences."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    language = Column(String(10), default='en')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    report_count = Column(Integer, default=0)
    is_blocked = Column(Boolean, default=False)

class Scammer(Base):
    """Scammer model for storing scammer information."""
    __tablename__ = 'scammers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    username = Column(String(100), index=True)
    telegram_link = Column(String(500))
    binance_id = Column(String(100))
    crypto_wallet = Column(String(200))
    report_count = Column(Integer, default=0)
    reporter_count = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    first_reported = Column(DateTime)
    last_reported = Column(DateTime)
    is_active = Column(Boolean, default=True)
    risk_score = Column(Integer, default=0)

class Report(Base):
    """Report model for storing individual reports."""
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, nullable=False)
    reporter_username = Column(String(100))
    scammer_id = Column(Integer, nullable=False)
    scammer_name = Column(String(200))
    scammer_username = Column(String(100))
    scammer_link = Column(String(500))
    binance_id = Column(String(100))
    crypto_wallet = Column(String(200))
    amount = Column(Float, default=0.0)
    currency = Column(String(10), default='USDT')
    description = Column(Text)
    evidence_url = Column(String(500))
    status = Column(String(20), default='pending')  # pending, confirmed, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_anonymous = Column(Boolean, default=False)

class Statistics(Base):
    """Statistics model for storing aggregated data."""
    __tablename__ = 'statistics'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.utcnow)
    total_reports = Column(Integer, default=0)
    total_scammers = Column(Integer, default=0)
    total_reporters = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    reports_today = Column(Integer, default=0)
    new_scammers_today = Column(Integer, default=0)
