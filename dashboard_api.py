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

    def get_recommendations(self):
        if self.model_trained and self.model:
            video_features = get_unrated_videos_with_features_from_database(self.db)
            recommendations = predict_video_preferences_with_model(self.model, video_features)
            return recommendations[:12]  # Return 12 videos for dashboard
        else:
            fallback_videos = get_unrated_videos_from_database(12, self.db)
            fallback_videos = [video.model_dump() for video in fallback_videos]
            for video in fallback_videos:
                video['like_probability'] = 0.5  # Default probability
            return fallback_videos
    
    def get_liked_videos(self):
        """Get videos that user liked, ordered by AI match confidence"""
        
        try:
            with Session(self.db.engine) as session:
                stmt = (
                    select(Preference, Video, VideoFeatures)
                    .join(Preference.video)
                    .join(Video.features)
                    .where(Preference.liked == True)
                    .order_by(Video.view_count.desc())
                )
                results = session.exec(stmt).all()

            
            liked_videos = []
            for _, vid, _ in results:
                video = {
                    'id': vid.id,
                    'title': vid.title,
                    'channel_name': vid.channel_name,
                    'view_count': vid.view_count,
                    'url': f"https://www.youtube.com/watch?v={vid.id}",
                    'duration_seconds': vid.duration_seconds
                }
                liked_videos.append(video)
            
            # If model is trained, predict confidence for liked videos
            if self.model_trained and self.model and liked_videos:
                # Create pandas DataFrame for prediction
                df_data = []
                for _, vid, features in results:
                    row_data = {
                        'id': vid.id,
                        'title': vid.title,
                        'channel_name': vid.channel_name,
                        'view_count': vid.view_count,
                        'title_length': features.title_length,
                        'description_length': features.description_length,
                        'view_like_ratio': features.view_like_ratio,
                        'engagement_score': features.engagement_score,
                        'title_sentiment': features.title_sentiment,
                        'has_tutorial_keywords': features.has_tutorial_keywords,
                        'has_beginner_keywords': features.has_beginner_keywords,
                        'has_ai_keywords': features.has_ai_keywords,
                        'has_challenge_keywords': features.has_challenge_keywords,
                        'has_time_constraint': features.has_time_constraint,
                        'duration_seconds': vid.duration_seconds,
                    }
                    df_data.append(row_data)
                
                video_features_df = pd.DataFrame(df_data)
                
                # Get predictions for confidence scores
                predictions = predict_video_preferences_with_model(self.model, video_features_df)
                
                # Sort by confidence and return
                return sorted(predictions, key=lambda x: x.get('like_probability', 0), reverse=True)
            
            # If no model, return with default confidence
            for video in liked_videos:
                video['like_probability'] = 0.8  # High default for liked videos
                
            return liked_videos
            
        except Exception as e:
            print(f"Error getting liked videos: {e}")
            return []

db = Database('db_test.db')
dashboard_api = DashboardAPI(db)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/recommendations')
def get_recommendations():
    #try:
        recommendations = dashboard_api.get_recommendations()
        
        formatted_recommendations = []
        for video in recommendations:
            formatted_recommendations.append({
                'id': video['id'],
                'title': video['title'],
                'channel_name': video['channel_name'],
                'view_count': video['view_count'],
                'url': video['url'],
                'thumbnail': f"https://img.youtube.com/vi/{video['id']}/hqdefault.jpg",
                'confidence': round(video.get('like_probability', 0.5) * 100),
                'views_formatted': format_view_count(video['view_count']),
                'duration': video['duration']
            })
        
        return jsonify({
            'success': True,
            'videos': formatted_recommendations,
            'model_trained': dashboard_api.model_trained,
            'total_ratings': get_rated_count_from_database(dashboard_api.db)
        })
    
"""except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500"""

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
    try:
        liked_videos = dashboard_api.get_liked_videos()
        
        formatted_videos = []
        for video in liked_videos:
            formatted_videos.append({
                'id': video['id'],
                'title': video['title'],
                'channel_name': video['channel_name'],
                'view_count': video['view_count'],
                'url': video['url'],
                'thumbnail': f"https://img.youtube.com/vi/{video['id']}/hqdefault.jpg",
                'confidence': round(video.get('like_probability', 0.8) * 100),
                'views_formatted': format_view_count(video['view_count']),
                'duration': video['duration']
            })
        
        return jsonify({
            'success': True,
            'videos': formatted_videos,
            'total_liked': len(formatted_videos)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
