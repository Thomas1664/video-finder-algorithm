# Video Inspiration Finder

AI-powered YouTube video recommendation system that learns your preferences.
This repository only includes the API backup while the frontend is now done in React. I'm planning to open source the frontend as well in the near future.
This work is enspired by [rosadiaznewyork
video-finder-algorithm](https://github.com/rosadiaznewyork/video-finder-algorithm).

## Quick Start

```bash
# Install dependencies (preferably in a virtual environment)
pip install -r requirements.txt
python dashboard_api.py
```

## Requirements

- **Python 3.10+**
- **YouTube Data API v3 Key** from [Google Cloud Console](https://console.cloud.google.com/)

## Setup

1. **Get YouTube API Key**:
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create project and enable YouTube Data API v3
   - Create API key

2. **Configure environment variables**:

   ```bash
   cp .env.example .env
   # Edit .env and add your API key:
   # YOUTUBE_API_KEY=your_actual_api_key_here
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

## Web Dashboard

- Access at: http://localhost:5001
- YouTube-like interface with AI confidence scores
- Rate videos to train the AI model

## Troubleshooting

**API Key Issues**:

- Ensure YouTube Data API v3 is enabled
- Check your API key has quota remaining

**Database Issues**: Delete `video_inspiration.db`

## Key changes

- Single entrypoint (flask server)
- Use ORM for database management
- Unit tests
- More flexible search
- Frontend in React

## Future work

- Evaluate usefulness of ORM for fetching videos and features from db
- Improve video feature selection for broader topics. Features are currently focused on Python and AI.
