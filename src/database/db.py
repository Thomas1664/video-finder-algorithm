from sqlmodel import TIMESTAMP, Column, Field, Relationship, SQLModel, create_engine, text
from datetime import datetime

class Video(SQLModel, table=True):
    __tablename__ = 'videos'

    id: str = Field(primary_key=True)
    title: str
    description: str
    view_count: int
    like_count: int
    comment_count: int
    duration: str
    published_at: str
    channel_name: str
    channel_id: str
    thumbnail_url: str
    tags: str
    category_id: int
    created_at: datetime = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),)
    )
    preference: "Preference" = Relationship(back_populates='video')
    features: "VideoFeatures" = Relationship(back_populates='video')

class Preference(SQLModel, table=True):
    __tablename__ = 'preferences'
    video_id: str = Field(primary_key=True, foreign_key='videos.id')
    liked: bool
    notes: str | None = Field(default=None)
    created_at: datetime = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),)
    )
    video: Video = Relationship(back_populates='preference')

class VideoFeatures(SQLModel, table=True):
    __tablename__ = 'video_preferences'
    video_id: str = Field(primary_key=True, foreign_key='videos.id')
    title_length: int
    description_length: int
    view_like_ratio: float
    engagement_score: float
    title_sentiment: float
    has_tutorial_keywords: bool
    has_time_constraint: bool
    has_beginner_keywords: bool
    has_ai_keywords: bool
    has_challenge_keywords: bool
    video: Video = Relationship(back_populates='features')


def setup_tables(db_path: str):
    engine = create_engine(db_path, echo=True)
    SQLModel.metadata.create_all(engine)
