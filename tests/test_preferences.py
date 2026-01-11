import pytest
from datetime import datetime
from sqlmodel import Session
from database.preference_operations import (
    save_video_rating_to_database,
    get_training_data_from_database,
    get_unrated_videos_with_features_from_database,
    get_rated_count_from_database,
)
from database.db import Video, Preference
from setup import db
from database.video_operations import get_unrated_videos_from_database


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
    session.commit()
    return v


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


def test_get_unrated_videos(db):
    with Session(db.engine) as session:
        video1 = _create_video(session, "vid1", 200)
        video2 = _create_video(session, "vid2", 200)
    save_video_rating_to_database("vid1", False, "note", db)
    unrated = get_unrated_videos_from_database(10, db)
    assert len(unrated) == 1
    assert unrated[0].id == "vid2"
