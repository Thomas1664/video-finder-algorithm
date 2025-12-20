import pandas as pd
from sqlmodel import Session, func
from sqlalchemy import select
from src.database.db import Database, Preference
from sqlalchemy.dialects.sqlite import Insert, insert
from datetime import datetime


def save_video_rating_to_database(video_id: str, liked: bool, notes: str, db: Database):
    stmt: Insert = insert(Preference).values(
        video_id=video_id,
        liked=liked,
        notes=notes,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=['video_id'],
        set_={
            'liked': liked,
            'notes': notes,
            'created_at': datetime.now(),
        }
    )
    with Session(db.engine) as session:
        session.exec(stmt)
        session.commit()

def get_training_data_from_database(db: Database) -> pd.DataFrame:
    with Session(db.engine) as session:
        query = '''
            SELECT vf.*, p.liked
            FROM video_features vf
            JOIN preferences p ON vf.video_id = p.video_id
        '''
        df = pd.read_sql_query(query, session.connection())
    return df

def get_unrated_videos_with_features_from_database(db: Database) -> pd.DataFrame:
    with Session(db.engine) as session:
        query = '''
            SELECT v.*, vf.*
            FROM videos v
            JOIN video_features vf ON v.id = vf.video_id
            LEFT JOIN preferences p ON v.id = p.video_id
            WHERE p.video_id IS NULL
            ORDER BY v.view_count DESC
        '''
        df = pd.read_sql_query(query, session.connection())
    return df

def get_rated_count_from_database(db: Database) -> int:
    with Session(db.engine) as session:
        count = session.exec(select(func.count()).select_from(Preference)).scalar_one()
    return count
