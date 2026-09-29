# store/functions/reddit.py
"""
Helper for fetching recent public activity from GitHub's Events API.

GitHub's public events endpoint is open (no auth needed for low-volume
requests) and returns JSON, making it a reliable stand-in for a
third-party API integration.

The function is kept under the name `get_reddit_posts` so existing
imports in views.py continue to work without changes.
"""

import certifi
import requests


def get_reddit_posts(subreddit="github"):
    """
    Fetch recent public GitHub events.
    """
    url = "https://api.github.com/events"
    headers = {
        "User-Agent": "DjangoEcommerceApp/1.0",
        "Accept": "application/vnd.github+json",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=10,
            verify=certifi.where(),
        )
    except requests.RequestException as exc:
        print(f"[github] network error: {exc}")
        return None

    if response.status_code != 200:
        print(f"[github] failed to fetch data: HTTP {response.status_code}")
        return None

    events = response.json()
    posts = []
    for event in events[:25]:  # keep it to 25 items
        actor = event.get("actor", {}).get("login", "unknown")
        repo = event.get("repo", {}).get("name", "unknown")
        event_type = event.get("type", "Event")
        posts.append({
            "title": f"{event_type} on {repo}",
            "author": actor,
            "url": f"https://github.com/{repo}",
        })
    return posts