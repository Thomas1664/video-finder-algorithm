from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import text
from sqlmodel import Session, select
from src.database.db import Database, Video, Preference
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
                if k != "id"  # your PK field
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],  # conflict on primary key
                set_=update_dict,
            )
            session.exec(stmt)
            session.commit()

def save_video_features_to_database(video_id: str, features: tuple, db: Database):
    # build a parameter dict for positional feature values
    # assumes the table has exactly 11 columns: video_id + 10 feature values
    params = {"video_id": video_id}
    for i, value in enumerate(features, start=1):
        params[f"f{i}"] = value

    # Use a parameterized INSERT OR REPLACE through SQLAlchemy engine
    stmt = text(
        "INSERT OR REPLACE INTO video_features VALUES (:video_id, :f1, :f2, :f3, :f4, :f5, :f6, :f7, :f8, :f9, :f10)"
    )

    with db.engine.begin() as conn:
        conn.execute(stmt, params)
        conn.commit()

def get_unrated_videos_from_database(limit: int, db: Database) -> list[dict]:
    stmt = (
        select(Video)
        .outerjoin(Preference, Video.id == Preference.video_id)
        .where(Preference.video_id.is_(None))
        .order_by(Video.view_count.desc())
        .limit(limit)
    )

    with Session(db.engine) as session:
        results = session.exec(stmt).all()

    videos: list[dict] = []
    for video in results:
        videos.append({
            'id': video.id,
            'title': video.title,
            'channel_name': video.channel_name,
            'view_count': video.view_count,
            'url': f"https://www.youtube.com/watch?v={video.id}",
            'duration': video.duration_seconds
        })
    return videos
