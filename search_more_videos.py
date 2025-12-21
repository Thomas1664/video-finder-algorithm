import os
from dotenv import load_dotenv

from src.database.db import Database
from src.database.video_operations import save_videos_to_database, save_video_features_to_database
from src.youtube.search import search_youtube_videos_by_query, get_coding_search_queries
from src.youtube.details import YouTubeVideo, get_video_details_from_youtube
from src.ml.feature_extraction import extract_all_features_from_video

load_dotenv()

def search_more_videos(db: Database):
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("Error: YOUTUBE_API_KEY not found in environment variables")
        return

    print("🔍 Searching for more coding videos...")

    # Use different/additional search queries to find new videos
    additional_queries = [
        # Add your additional search queries here
        # Examples:
        # "python tutorial",
        # "web development course",
        # "coding interview prep",
        # "javascript frameworks",
        # "database tutorial"
        "US late night",
        "gardening",
        "machine learning tutorial",
        "rag tutorial",
        "python llm",
    ]

    all_videos: set[YouTubeVideo] = set()

    for query in additional_queries:
        print(f"  Searching: {query}")
        video_ids = search_youtube_videos_by_query(api_key, query, 10)
        videos = get_video_details_from_youtube(api_key, video_ids)
        all_videos.update(videos)


    if all_videos:
        save_videos_to_database(list(all_videos), db)

        for video in all_videos:
            features = extract_all_features_from_video(video)
            save_video_features_to_database(features, db)

        print(f"✅ Found and saved {len(all_videos)} new videos!")
    else:
        print("❌ No new videos found.")

if __name__ == "__main__":
    db = Database('db_test.db')
    search_more_videos(db)