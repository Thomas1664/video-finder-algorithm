import requests
from datetime import datetime, timedelta
from pydantic import AliasChoices, AliasPath, BaseModel, Field, ValidationError

class YouTubeVideo(BaseModel):
    id: str
    title: str = Field(validation_alias=AliasChoices(AliasPath('snippet', 'title'), 'title'))
    channel_id: str = Field(validation_alias=AliasChoices(AliasPath('snippet', 'channelId'), 'channel_id'))
    channel_name: str = Field(validation_alias=AliasChoices(AliasPath('snippet', 'channelTitle'), 'channel_name'))
    description: str = Field(validation_alias=AliasChoices(AliasPath('snippet', 'description'), 'description'))
    published_at: datetime = Field(validation_alias=AliasChoices(AliasPath('snippet', 'publishedAt'), 'published_at'))
    tags: list[str] = Field(validation_alias=AliasChoices(AliasPath('snippet', 'tags'), 'tags'), default=[])
    category_id: int = Field(validation_alias=AliasChoices(AliasPath('snippet', 'categoryId'), 'category_id'))
    thumbnail_url: str = Field(validation_alias=AliasChoices(AliasPath('snippet', 'thumbnails', 'high', 'url'), 'thumbnail_url'))
    view_count: int = Field(validation_alias=AliasChoices(AliasPath('statistics', 'viewCount'), 'view_count'))
    like_count: int = Field(validation_alias=AliasChoices(AliasPath('statistics', 'likeCount'), 'like_count'), default=0)
    comment_count: int = Field(validation_alias=AliasChoices(AliasPath('statistics', 'commentCount'), 'comment_count'))
    duration: timedelta = Field(validation_alias=AliasChoices(AliasPath('contentDetails', 'duration'), 'duration'))

    def view_like_ratio(self):
        return self.like_count / max(self.view_count, 1)
    
    def engagement_score(self):
        return (self.like_count + self.view_count) / max(self.view_count, 1)

    def __hash__(self) -> int:
        return self.id.__hash__()

def get_video_details_from_youtube(api_key: str, video_ids: list[str]) -> list[YouTubeVideo]:
    if not video_ids:
        return []

    details_url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        'key': api_key,
        'id': ','.join(video_ids),
        'part': 'snippet,statistics,contentDetails'
    }

    try:
        response = requests.get(details_url, params=params)
        data = response.json()

        videos = []
        for item in data.get('items', []):
            video: YouTubeVideo = YouTubeVideo.model_validate(item)
            if is_relevant_coding_video(video):
                videos.append(video)

        return videos

    except Exception as e:
        print(f"Error getting video details: {e}")
        return []

def is_relevant_coding_video(video: YouTubeVideo) -> bool:
    title = video.title.lower()
    description = video.description.lower()

    programming_keywords = [
        'coding', 'programming', 'javascript', 'python', 'react', 'web development',
        'tutorial', 'learn', 'build', 'create', 'app', 'website', 'algorithm', 'ai'
    ]

    if video.view_count < 100000:
        return False

    has_programming = any(keyword in title or keyword in description
                        for keyword in programming_keywords)

    return has_programming
