from app.database import SessionLocal

def get_db():
    db = SessionLocal()  # open a session (start a conversation with the DB)
    try:
        yield db         # hand it to whoever needs it
    finally:
        db.close()       # always close it when done, even if something crashes