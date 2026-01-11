from sqlmodel import TIMESTAMP, Column, Field, Relationship, SQLModel, create_engine, text
from datetime import datetime
import json
from src.youtube.details import YouTubeVideo

class Video(SQLModel, table=True):
    __tablename__ = 'videos'

    id: str = Field(primary_key=True, )
    title: str
    description: str
    view_count: int
    like_count: int
    comment_count: int
    duration_seconds: int
    published_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    channel_name: str
    channel_id: str
    thumbnail_url: str
    tags: str
    category_id: int
    created_at: datetime = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        default=datetime.now())
    )
    preference: "Preference" = Relationship(back_populates='video')
    features: "VideoFeatures" = Relationship(back_populates='video')

    @classmethod
    def from_youtube_api(cls, video: YouTubeVideo) -> "Video":
        return cls(
            id=video.id,
            title=video.title,
            description=video.description,
            channel_id=video.channel_id,
            channel_name=video.channel_name,
            published_at=video.published_at,
            thumbnail_url=video.thumbnail_url,
            tags=json.dumps(video.tags),
            category_id=video.category_id,
            view_count=video.view_count,
            like_count=video.like_count,
            comment_count=video.comment_count,
            duration_seconds=int(video.duration.total_seconds()),
            created_at=datetime.now()
        )

class Preference(SQLModel, table=True):
    __tablename__ = 'preferences'
    video_id: str = Field(primary_key=True, foreign_key='videos.id')
    liked: bool
    notes: str | None = Field(default=None)
    created_at: datetime = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        default=datetime.now()
        )
    )
    video: Video = Relationship(back_populates='preference')

class VideoFeatures(SQLModel, table=True):
    __tablename__ = 'video_features'
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


class Database():
    def __init__(self, db_path) -> None:
        self._db_path = f'sqlite:///{db_path}'
        self.engine = create_engine(self._db_path, echo=True)
        self._setup_tables()

    def _setup_tables(self):
        SQLModel.metadata.create_all(self.engine)
