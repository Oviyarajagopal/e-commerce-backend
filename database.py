from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


# Engine
engine = create_engine(DATABASE_URL)

# Session (DB connection for each request)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class (all models inherit this)
Base = declarative_base()