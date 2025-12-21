from typing import Any
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from dotenv import load_dotenv
from sqlmodel import Session, select
import pandas as pd
import os
from src.database.db import Database, Preference, Video, VideoFeatures
from src.database.preference_operations import get_training_data_from_database, get_unrated_videos_with_features_from_database, get_rated_count_from_database, save_video_rating_to_database
from src.database.video_operations import get_unrated_videos_from_database
from src.ml.model_training import create_recommendation_model, train_model_on_user_preferences
from src.ml.predictions import predict_video_preferences_with_model
from src.youtube.search import search_and_save_videos

load_dotenv()

app = Flask(__name__)
CORS(app)

class DashboardAPI:
    def __init__(self, db: Database):
        self.model = None
        self.model_trained = False
        self.db = db
        self._initialize_model()

    def _initialize_model(self):
        rated_count = get_rated_count_from_database(self.db)
        if rated_count >= 10:
            self.model = create_recommendation_model()
            training_data = get_training_data_from_database(self.db)
            success = train_model_on_user_preferences(self.model, training_data)
            if success:
                self.model_trained = True

    def get_recommendations(self) -> list[dict[str, Any]]:
        if self.model_trained and self.model:
            video_features = get_unrated_videos_with_features_from_database(self.db)
            # Return 12 videos for dashboard
            recommendations = predict_video_preferences_with_model(self.model, video_features).head(12)
            return recommendations.to_dict(orient='records')
        else:
            fallback_videos = get_unrated_videos_from_database(12, self.db)
            fallback_videos = [video.model_dump() for video in fallback_videos]
            for video in fallback_videos:
                video['like_probability'] = 0.5  # Default probability
            return fallback_videos

    def get_liked_videos(self) -> list[dict[str, Any]]:
        """Get videos that user liked, ordered by AI match confidence"""
        with Session(self.db.engine) as session:
            stmt = (
                select(Preference, Video, VideoFeatures)
                .join(Preference.video)
                .join(Video.features)
                .where(Preference.liked == True)
                .order_by(Video.view_count.desc())
            )
            results = session.exec(stmt).all()
        liked_videos = pd.DataFrame([video.model_dump() for _, video, _ in results])

        # If model is trained, predict confidence for liked videos
        if self.model_trained and self.model and not liked_videos.empty:
            # Create pandas DataFrame for prediction
            video_features_df = pd.DataFrame([features.model_dump() for _, _, features in results])
            video_features_df = video_features_df.set_index('video_id')

            # Get predictions for confidence scores
            predictions = predict_video_preferences_with_model(self.model, video_features_df)
            best_matches = liked_videos.merge(predictions['like_probability'], left_on='id', right_index=True).sort_values(by='like_probability', ascending=False)
            return best_matches.to_dict(orient='records')

        # If no model, return with default confidence
        liked_videos['like_probability'] = 0.8  # High default for liked videos
        return liked_videos.to_dict(orient='records')


def format_video_response(videos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    formatted_videos = []
    for video in videos:
        formatted_videos.append({
            'id': video['id'],
            'title': video['title'],
            'channel_name': video['channel_name'],
            'view_count': video['view_count'],
            'url': f'https://www.youtube.com/watch?v={video["id"]}',
            'thumbnail': f"https://img.youtube.com/vi/{video['id']}/hqdefault.jpg",
            'confidence': round(video['like_probability'] * 100),
            'views_formatted': format_view_count(video['view_count']),
            'duration': video['duration_seconds']
        })
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
            if not dashboard_api.model:
                dashboard_api.model = create_recommendation_model()

            training_data = get_training_data_from_database(dashboard_api.db)
            success = train_model_on_user_preferences(dashboard_api.model, training_data)

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
    #try:
    data: dict = request.json
    query: str = data.get('query')
    if not query or len(query) == 0:
        return jsonify({
            'success': False,
            'error': 'Missing or empty query!'
        }), 400

    search_and_save_videos(db, api_key, query, 28)

    return jsonify({
        'success': True
    }), 200
    """except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500"""

def format_view_count(count: int):
    if count >= 1000000:
        return f"{count/1000000:.1f}M views"
    elif count >= 1000:
        return f"{count/1000:.1f}K views"
    else:
        return f"{count} views"

if __name__ == '__main__':
    app.run(debug=True, port=5001)
