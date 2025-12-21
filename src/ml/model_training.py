from sklearn.ensemble import RandomForestClassifier
import pandas as pd


class Model:
    feature_columns = [
        'title_length', 'description_length', 'view_like_ratio', 'engagement_score',
        'title_sentiment', 'has_tutorial_keywords', 'has_time_constraint',
        'has_beginner_keywords', 'has_ai_keywords', 'has_challenge_keywords'
    ]

    def __init__(self) -> None:
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)


    def train(self, training_data: pd.DataFrame) -> bool:
        if len(training_data) < 10:
            print("Need at least 10 rated videos to train model")
            return False

        X = training_data[self.feature_columns]
        y = training_data['liked']

        self.model.fit(X, y)
        print(f"Model trained on {len(training_data)} rated videos")
        return True


    def predict(self, video_features: pd.DataFrame) -> pd.DataFrame:
        if video_features.empty:
            return pd.DataFrame()
        # ensure columns are in correct order
        X = video_features[self.feature_columns]
        probabilities = self.model.predict_proba(X)[:, 1]

        video_features_copy = video_features.copy()
        video_features_copy['like_probability'] = probabilities

        return video_features_copy.sort_values(by='like_probability', ascending=False)
