import requests
from src.database.db import Database, VideoFeatures
from src.database.video_operations import save_video_features_to_database, save_videos_to_database
from src.ml.feature_extraction import extract_all_features_from_video
from src.youtube.details import YouTubeVideo, get_video_details_from_youtube

def search_youtube_videos_by_query(api_key: str, query: str, max_results: int) -> list[str]:
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'key': api_key,
        'q': query,
        'part': 'snippet',
        'type': 'video',
        'order': 'viewCount',
        'maxResults': max_results,
        'videoCategoryId': '28',
        'publishedAfter': '2020-01-01T00:00:00Z',
        'relevanceLanguage': 'en'
    }

    response = requests.get(search_url, params=params)
    data = response.json()
    if 'items' not in data:
        return []
    video_ids = [item['id']['videoId'] for item in data['items']]
    return video_ids

def search_and_save_videos(db: Database, api_key: str, query: str, max_results: int) -> list[tuple[YouTubeVideo, VideoFeatures]]:
    video_ids = search_youtube_videos_by_query(api_key, query, max_results)
    videos = get_video_details_from_youtube(api_key, video_ids)
    save_videos_to_database(videos, db)
    video_features = [(video, extract_all_features_from_video(video)) for video in videos]
    for _, features in video_features:
        save_video_features_to_database(features, db)
    return video_features

def get_coding_search_queries() -> list[str]:
    return [
        # Add your own search queries here
        # Examples:
        # "python tutorial",
        # "javascript project",
        # "machine learning basics",
        # "web development",
        # "coding interview prep"
    ]
