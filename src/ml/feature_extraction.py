from typing import Any
from src.database.db import VideoFeatures
from src.youtube.details import YouTubeVideo

def calculate_basic_video_metrics(video: YouTubeVideo) -> dict[str, Any]:
    return {
        "title_length": len(video.title),
        "description_length": len(video.description),
        "view_like_ratio": video.view_like_ratio(),
        "engagement_score": video.engagement_score(),
    }

def detect_keyword_features_in_video(title: str, description: str) -> dict[str, Any]:
    tutorial_keywords = ['tutorial', 'learn', 'course', 'guide', 'how to']
    time_keywords = ['24 hours', '1 day', '1 hour', 'minutes', 'seconds', 'crash course']
    beginner_keywords = ['beginner', 'start', 'basics', 'introduction', 'getting started']
    ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'neural network']
    challenge_keywords = ['challenge', 'build', 'create', 'project', 'coding']

    return {
        "has_tutorial_keywords": any(kw in title or kw in description for kw in tutorial_keywords),
        "has_time_constraint": any(kw in title for kw in time_keywords),
        "has_beginner_keywords": any(kw in title or kw in description for kw in beginner_keywords),
        "has_ai_keywords": any(kw in title or kw in description for kw in ai_keywords),
        "has_challenge_keywords": any(kw in title for kw in challenge_keywords),
    }

def calculate_title_sentiment_score(title: str) -> float:
    positive_words = ['amazing', 'best', 'awesome', 'great', 'perfect', 'love', 'incredible']
    negative_words = ['hard', 'difficult', 'impossible', 'failed', 'broke', 'wrong']

    positive_count = sum(1 for word in positive_words if word in title)
    negative_count = sum(1 for word in negative_words if word in title)
    return positive_count - negative_count

def extract_all_features_from_video(video: YouTubeVideo) -> VideoFeatures:
    title = video.title.lower()
    description = video.description.lower()

    basic_metrics = calculate_basic_video_metrics(video)
    keyword_features = detect_keyword_features_in_video(title, description)
    sentiment_score = calculate_title_sentiment_score(title)
    return VideoFeatures.model_validate({
        'video_id': video.id,
        **basic_metrics,
        **keyword_features,
        'title_sentiment': sentiment_score
    })
