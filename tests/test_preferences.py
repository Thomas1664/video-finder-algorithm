import pytest
from datetime import datetime
from sqlmodel import Session

from src.database.preference_operations import (
    save_video_rating_to_database,
    get_training_data_from_database,
    get_unrated_videos_with_features_from_database,
    get_rated_count_from_database,
)
from src.database.db import Database, Video, VideoFeatures, Preference


@pytest.fixture
def db() -> Database:
    db_file = ":memory:"
    database = Database(str(db_file))
    return database


def _create_video(session: Session, vid: str, view_count: int = 0):
    v = Video(
        id=vid,
        title=f"Title {vid}",
        description="desc",
        view_count=view_count,
        like_count=0,
        comment_count=0,
        duration_seconds=60,
        published_at=datetime.now(),
        channel_name="chan",
        channel_id="chanid",
        thumbnail_url="url",
        tags="[]",
        category_id=0,
        created_at=datetime.now(),
    )
    session.add(v)
    return v


def _create_video_features(session: Session, vid: str, title_length: int = 5, view_like_ratio: float = 0.0):
    vf = VideoFeatures(
        video_id=vid,
        title_length=title_length,
        description_length=10,
        view_like_ratio=view_like_ratio,
        engagement_score=0.1,
        title_sentiment=0.0,
        has_tutorial_keywords=False,
        has_time_constraint=False,
        has_beginner_keywords=False,
        has_ai_keywords=False,
        has_challenge_keywords=False,
    )
    session.add(vf)
    return vf


def test_save_rating(db):
    with Session(db.engine) as session:
        _create_video(session, "id1", 500)
    
    save_video_rating_to_database("id1", True, "note", db)
    with Session(db.engine) as session:
        pref = session.get(Preference, "id1")
        assert pref is not None
        assert pref.liked == True
        assert pref.notes == "note"
    # test updating an existing rating
    save_video_rating_to_database("id1", False, "note", db)
    with Session(db.engine) as session:
        pref = session.get(Preference, "id1")
        assert pref is not None
        assert pref.liked == False


def test_count(db):
    save_video_rating_to_database("id1", False, "note", db)
    save_video_rating_to_database("id2", True, "note", db)
    count = get_rated_count_from_database(db)
    assert count == 2
