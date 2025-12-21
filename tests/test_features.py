import pytest
from sqlmodel import Session, select
from setup import db
from src.database.db import VideoFeatures
from src.database.video_operations import save_video_features_to_database


def _create_video_features(vid: str, view_like_ratio, engagement_score: float):
    return VideoFeatures(
        video_id=vid,
        title_length=5,
        description_length=10,
        view_like_ratio=view_like_ratio,
        engagement_score=engagement_score,
        title_sentiment=0.0,
        has_tutorial_keywords=False,
        has_time_constraint=False,
        has_beginner_keywords=False,
        has_ai_keywords=False,
        has_challenge_keywords=False,
    )


def test_add_features(db):
    features = _create_video_features("vid1", 0.5, 0.2)
    save_video_features_to_database(features, db)
    features.engagement_score = 0.3
    save_video_features_to_database(features, db)
    stmt = select(VideoFeatures)

    with Session(db.engine) as session:
        results = session.exec(stmt).all()
        assert len(results) == 1
        assert results[0] == features
        assert results[0].engagement_score == 0.3
