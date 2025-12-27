from typing import Sequence
import pandas as pd
from sqlmodel import Session, func, select
from src.database.db import Database, Preference, Video, VideoFeatures
from sqlalchemy.dialects.sqlite import Insert, insert
import sqlalchemy
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


def get_unrated_videos_with_features_from_database(db: Database) -> Sequence[tuple[Preference, Video, VideoFeatures]]:
    stmt = (
        select(Preference, Video, VideoFeatures)
        .join(Video.features)
        .outerjoin(Preference, Video.id == Preference.video_id)
        .where(Preference.video_id.is_(None))
        .order_by(Video.view_count.desc())
    )
    with Session(db.engine) as session:
        results = session.exec(stmt).all()
    return results


def get_liked_videos_from_db(db: Database) -> Sequence[tuple[Preference, Video, VideoFeatures]]:
    stmt = (
        select(Preference, Video, VideoFeatures)
        .join(Preference.video)
        .join(Video.features)
        .where(Preference.liked == True)
        .order_by(Video.view_count.desc())
    )
    with Session(db.engine) as session:
        results = session.exec(stmt).all()
    return results


def get_rated_count_from_database(db: Database) -> int:
    with Session(db.engine) as session:
        count = session.exec(sqlalchemy.select(func.count()).select_from(Preference)).scalar_one()
    return count
