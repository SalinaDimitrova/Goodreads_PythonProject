from .database import Base, engine
from . import models  # важно: импортва всички модели

def init_db():
    Base.metadata.create_all(bind=engine)
