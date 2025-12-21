import pytest
from src.database.db import Database
from src.youtube.details import YouTubeVideo
from datetime import datetime, timedelta


@pytest.fixture
def db() -> Database:
    database = Database(":memory:")
    return database


def create_youtube_video():
    return YouTubeVideo(
        id="vid1",
        title="a very interesting yt video",
        channel_id="chan1",
        channel_name="test channel",
        description="video description",
        published_at=datetime.now(),
        tags=["interesting", "emotional", "john oliver"],
        category_id=67,
        thumbnail_url="url",
        view_count=200_000,
        like_count=5_000,
        comment_count=150,
        duration=timedelta(days=10)
    )
