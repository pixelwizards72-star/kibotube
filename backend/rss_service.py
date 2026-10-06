import feedparser

def fetch_top_articles(rss_url: str, limit: int = 5):
    """
    Fetches the latest articles from an RSS feed.
    Returns a list of dicts: [{'title': str, 'link': str, 'summary': str}]
    """
    if not rss_url:
        return []
    
    feed = feedparser.parse(rss_url)
    articles = []
    
    for entry in feed.entries[:limit]:
        # Provide fallback if summary is missing
        summary = entry.get('summary', '')
        if not summary and hasattr(entry, 'content'):
            summary = entry.content[0].value
        
        articles.append({
            'title': entry.get('title', 'No Title'),
            'link': entry.get('link', ''),
            'summary': summary
        })
        
    return articles
