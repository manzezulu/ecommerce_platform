# store/functions/reddit.py
"""
Helper for fetching posts from Reddit's public JSON endpoint.
"""

import requests


def get_reddit_posts(subreddit="movies"):
    """Fetch the hot posts from a subreddit's JSON feed.

    Args:
        subreddit: name of the subreddit (no "r/" prefix).

    Returns:
        list of dicts with keys 'title', 'author', 'url', or None on error.
    """
    url = f"https://www.reddit.com/r/{subreddit}/.json"
    headers = {"User-Agent": "DjangoEcommerceApp/1.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as exc:
        print(f"[reddit] network error: {exc}")
        return None

    if response.status_code != 200:
        print(f"[reddit] failed to fetch data: HTTP {response.status_code}")
        return None

    data = response.json()
    posts = []
    for item in data.get("data", {}).get("children", []):
        post = item.get("data", {})
        posts.append({
            "title": post.get("title", "(no title)"),
            "author": post.get("author", "[deleted]"),
            "url": "https://www.reddit.com" + post.get("permalink", ""),
        })
    return posts