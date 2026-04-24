from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🔗 MySQL connection URL
DATABASE_URL = "mysql+pymysql://root:Viya2105#@localhost:3306/ecommerce_db"

# Engine
engine = create_engine(DATABASE_URL)

# Session (DB connection for each request)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class (all models inherit this)
Base = declarative_base()