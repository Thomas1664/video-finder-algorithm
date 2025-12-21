from typing import Sequence
from sqlalchemy.dialects.sqlite import insert
from sqlmodel import Session, select
from src.database.db import Database, Video, Preference, VideoFeatures
from src.youtube.details import YouTubeVideo

def save_videos_to_database(videos: list[YouTubeVideo] | list[Video], db: Database):
    if len(videos) == 0:
        return
    db_videos: list["Video"] = []
    if isinstance(videos[0], YouTubeVideo):
        db_videos = [Video.from_youtube_api(video) for video in videos]

    with Session(db.engine) as session:
        for video in db_videos:
            data = video.model_dump()
            stmt = insert(Video).values(**data)
            update_dict = {
                k: stmt.excluded[k]
                for k in data.keys()
                if k != "id"
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_=update_dict,
            )
            session.exec(stmt)
            session.commit()

def save_video_features_to_database(features: VideoFeatures, db: Database):
    data = features.model_dump()
    stmt = insert(VideoFeatures).values(data)
    update_dict = {
        k: stmt.excluded[k]
        for k in data.keys()
        if k != "video_id"
    }
    stmt = stmt.on_conflict_do_update(
        index_elements=["video_id"],
        set_=update_dict,
    )
    with Session(db.engine) as session:
        session.exec(stmt)
        session.commit()

def get_unrated_videos_from_database(limit: int, db: Database) -> Sequence[Video]:
    stmt = (
        select(Video)
        .outerjoin(Preference, Video.id == Preference.video_id)
        .where(Preference.video_id.is_(None))
        .order_by(Video.view_count.desc())
        .limit(limit)
    )
    with Session(db.engine) as session:
        results = session.exec(stmt).all()
    return results
