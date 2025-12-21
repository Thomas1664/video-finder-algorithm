import pandas as pd
from sklearn.ensemble import RandomForestClassifier


def predict_video_preferences_with_model(model: RandomForestClassifier, video_features: pd.DataFrame) -> pd.DataFrame:
    if video_features.empty:
        return pd.DataFrame()
    
    feature_columns = [
        'title_length', 'description_length', 'view_like_ratio', 'engagement_score',
        'title_sentiment', 'has_tutorial_keywords', 'has_time_constraint',
        'has_beginner_keywords', 'has_ai_keywords', 'has_challenge_keywords'
    ]
    # ensure columns are in correct order
    X = video_features[feature_columns]
    probabilities = model.predict_proba(X)[:, 1]
    
    video_features_copy = video_features.copy()
    video_features_copy['like_probability'] = probabilities

    return video_features_copy.sort_values(by='like_probability', ascending=False)
