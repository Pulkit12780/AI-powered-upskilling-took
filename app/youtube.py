from googleapiclient.discovery import build
from app.config import settings
from app.schemas import CourseRec

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = build("youtube", "v3", developerKey=settings.youtube_api_key)
    return _client


def search_videos(query: str, max_results: int = 3) -> list[CourseRec]:
    youtube = _get_client()
    response = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results,
        relevanceLanguage="en",
    ).execute()

    results = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        channel = item["snippet"]["channelTitle"]
        results.append(CourseRec(
            title=title,
            platform=f"YouTube — {channel}",
            url=f"https://www.youtube.com/watch?v={video_id}",
        ))
    return results
