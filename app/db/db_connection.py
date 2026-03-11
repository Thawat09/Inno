from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import Config


class Database:

    def __init__(self):
        self.engine = create_engine(
            Config.DB_URI,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def get_session(self):
        return self.SessionLocal()


db = Database()