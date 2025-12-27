from typing import Any
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from dotenv import load_dotenv
import pandas as pd
import os
from src.database.db import Database, Preference, Video, VideoFeatures
from src.database.preference_operations import get_liked_videos_from_db, get_training_data_from_database, get_unrated_videos_with_features_from_database, get_rated_count_from_database, save_video_rating_to_database
from src.database.video_operations import get_unrated_videos_from_database, save_video_features_to_database, save_videos_to_database
from src.ml.feature_extraction import extract_all_features_from_video
from src.ml.model_training import Model
from src.youtube.details import get_video_details_from_youtube
from src.youtube.search import search_and_save_videos

load_dotenv()

app = Flask(__name__)
CORS(app)


class DashboardAPI:
    def __init__(self, db: Database):
        self.model = Model()
        self.model_trained = False
        self.db = db
        self._initialize_model()

    def _initialize_model(self):
        rated_count = get_rated_count_from_database(self.db)
        if rated_count >= 10:
            training_data = get_training_data_from_database(self.db)
            if self.model.train(training_data):
                self.model_trained = True

    def get_recommendations(self) -> list[dict[str, Any]]:
        if self.model_trained and self.model:
            results = get_unrated_videos_with_features_from_database(self.db)
            video_features = [feature for _, _,feature in results]
            videos = pd.DataFrame([video.model_dump() for _, video, _ in results])
            # Return 27 videos for dashboard
            recommendations = self.predict(video_features)
            videos_and_preds = videos.merge(recommendations['like_probability'], left_on='id', right_index=True).head(27)
            return videos_and_preds.to_dict(orient='records')
        else:
            fallback_videos = get_unrated_videos_from_database(27, self.db)
            fallback_videos = [video.model_dump() for video in fallback_videos]
            for video in fallback_videos:
                video['like_probability'] = 0.5  # Default probability
            return fallback_videos

    def predict(self, features: list[VideoFeatures], default_prob=0.5):
        # Create pandas DataFrame for prediction
        feature_dict = [feature.model_dump() for feature in features]
        video_features_df = pd.DataFrame(feature_dict).set_index('video_id')

        if self.model_trained and self.model:
            # Get predictions for confidence scores
            predictions = self.model.predict(video_features_df)
            return predictions.sort_values(by='like_probability', ascending=False)
        video_features_df['like_probability'] = default_prob
        return video_features_df

    def get_liked_videos(self) -> list[dict[str, Any]]:
        """Get videos that user liked, ordered by AI match confidence"""
        results = get_liked_videos_from_db(self.db)
        liked_videos = pd.DataFrame([video.model_dump() for _, video, _ in results])
        features = [features for _, _, features in results]
        # Get predictions for confidence scores
        predictions = self.predict(features, default_prob=0.8) # High default for liked videos
        best_matches = liked_videos.merge(predictions['like_probability'], left_on='id', right_index=True)
        return best_matches.to_dict(orient='records')


def format_seconds(total_seconds: int) -> str:
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def format_video_response(videos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    formatted_videos = []
    for video in videos:
        result = {
            'id': video['id'],
            'title': video['title'],
            'channel_name': video['channel_name'],
            'channel_id': video['channel_id'],
            'view_count': video['view_count'],
            'like_count': video['like_count'],
            'url': f'https://www.youtube.com/watch?v={video["id"]}',
            'thumbnail': f"https://img.youtube.com/vi/{video['id']}/hqdefault.jpg",
            'views_formatted': format_view_count(video['view_count']),
            'likes_formatted': format_view_count(video['like_count']),
            'published_at': video['published_at'],
            'description': video['description'],
        }
        like_prob = video.get('like_probability')
        if like_prob:
            result['confidence'] = round(like_prob * 100)
        duration = video.get('duration_seconds')
        if duration:
            result['duration'] = format_seconds(video['duration_seconds'])
        else:
            result['duration'] = format_seconds(int(video['duration'].total_seconds()))
        formatted_videos.append(result)
    return formatted_videos


db = Database('db_test.db')
dashboard_api = DashboardAPI(db)


@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/recommendations')
def get_recommendations():
    recommendations = dashboard_api.get_recommendations()
    formatted_recommendations = format_video_response(recommendations)

    return jsonify({
        'success': True,
        'videos': formatted_recommendations,
        'model_trained': dashboard_api.model_trained,
        'total_ratings': get_rated_count_from_database(dashboard_api.db)
    })


@app.route('/api/rate', methods=['POST'])
def rate_video():
    try:
        data = request.json
        video_id = data.get('video_id')
        liked = data.get('liked')

        if not video_id or liked is None:
            return jsonify({
                'success': False,
                'error': 'Missing video_id or liked parameter'
            }), 400

        # Save the rating
        save_video_rating_to_database(video_id, liked, "", dashboard_api.db)

        # Check if we should retrain the model
        model_retrained = False
        rated_count = get_rated_count_from_database(dashboard_api.db)

        if rated_count >= 10:  # Minimum ratings needed for training
            # Retrain the model with new data
            training_data = get_training_data_from_database(dashboard_api.db)
            success = dashboard_api.model.train(training_data)

            if success:
                dashboard_api.model_trained = True
                model_retrained = True

        return jsonify({
            'success': True,
            'message': 'Rating saved successfully',
            'model_retrained': model_retrained,
            'total_ratings': rated_count
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/liked')
def get_liked_videos():
    liked_videos = dashboard_api.get_liked_videos()
    formatted_videos = format_video_response(liked_videos)

    return jsonify({
        'success': True,
        'videos': formatted_videos,
        'total_liked': len(formatted_videos)
    })


@app.route('/api/search', methods=['POST'])
def search_videos():
    api_key = os.getenv('YOUTUBE_API_KEY')
    data: dict = request.json
    query: str = data.get('query')
    if not query or len(query) == 0:
        return jsonify({
            'success': False,
            'error': 'Missing or empty query!'
        }), 400

    results = search_and_save_videos(db, api_key, query, 28)
    videos = pd.DataFrame([video.model_dump() for video, _ in results])
    features = [features for _, features in results]
    recommendations = dashboard_api.predict(features)
    videos_and_preds = videos.merge(recommendations['like_probability'], left_on='id', right_index=True).head(27)
    videos = format_video_response(videos_and_preds.to_dict(orient='records'))

    return jsonify({
        'success': True,
        'videos': videos
    }), 200


@app.route('/api/video/<video_id>')
def get_video_details(video_id: str):
    api_key = os.getenv('YOUTUBE_API_KEY')

    videos = get_video_details_from_youtube(api_key, [video_id])
    if len(videos) != 1:
        return jsonify({
            'success': False,
            'error': 'Video not found'
        }), 404

    save_videos_to_database(videos, db)
    video = videos[0]
    features = extract_all_features_from_video(video)
    save_video_features_to_database(features, db)
    formatted_videos = format_video_response([video.model_dump()])

    return jsonify({
        'success': True,
        'videos': formatted_videos
    })


def format_view_count(count: int):
    if count >= 1000000:
        return f"{count/1000000:.1f}M views"
    elif count >= 1000:
        return f"{count/1000:.1f}K views"
    else:
        return f"{count} views"


if __name__ == '__main__':
    app.run(debug=True, port=5001)
