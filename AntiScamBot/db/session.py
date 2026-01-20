from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config.settings import DATABASE_URL

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Scoped session for thread safety
Session = scoped_session(SessionFactory)

def get_db_session():
    """Get database session."""
    session = Session()
    try:
        yield session
    finally:
        session.close()

def init_db():
    """Initialize database tables."""
    from db.models import Base
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully.")
