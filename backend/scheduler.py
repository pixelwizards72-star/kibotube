import asyncio
import datetime
from sqlalchemy.orm import Session
from . import models, database, social_api, ai_agent, rss_service

async def check_and_publish_posts():
    db = database.SessionLocal()
    try:
        now = datetime.datetime.utcnow()
        posts_to_publish = db.query(models.Post).filter(
            models.Post.is_approved == True,
            models.Post.is_published == False,
            models.Post.scheduled_time <= now
        ).all()

        for post in posts_to_publish:
            cred = db.query(models.Credential).filter(models.Credential.platform == post.platform).first()
            if cred and cred.is_connected:
                try:
                    client = social_api.get_client(post.platform, cred)
                    post_id = await client.publish_post(post.content)
                    post.is_published = True
                    print(f"Successfully published post {post.id} to {post.platform}. Ext ID: {post_id}")
                except Exception as e:
                    post.error_message = str(e)
                    print(f"Error publishing post {post.id}: {e}")
            else:
                post.error_message = f"Account for {post.platform} not connected."

        db.commit()
    finally:
        db.close()

async def cron_worker():
    while True:
        try:
            await check_and_publish_posts()
        except Exception as e:
            print(f"Cron loop error: {e}")
        await asyncio.sleep(60)

async def news_worker():
    while True:
        try:
            db = database.SessionLocal()
            config = db.query(models.AgentConfig).first()
            if config and config.news_engine_enabled and config.news_rss_url:
                print("[NEWS ENGINE] Waking up to fetch RSS feed...")
                articles = rss_service.fetch_top_articles(config.news_rss_url, limit=5)
                for article in articles:
                    # Check if already scraped
                    if not db.query(models.ScrapedArticle).filter_by(url=article['link']).first():
                        print(f"[NEWS ENGINE] Found new trending article: {article['title']}")
                        db.add(models.ScrapedArticle(url=article['link']))
                        db.commit()
                        
                        # AI Rewrite
                        post_content, image_url = await ai_agent.ai_engine.generate_from_article(article, tone=config.tone_of_voice)
                        
                        # Schedule to publish in 5 minutes across Meta and X
                        for platform in ["meta", "x"]:
                            sched_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
                            new_post = models.Post(
                                content=post_content,
                                image_url=image_url,
                                content_type="post",
                                platform=platform,
                                scheduled_time=sched_time,
                                is_approved=True,
                                is_published=False
                            )
                            db.add(new_post)
                        db.commit()
                        break # Only post 1 new article per cycle
            db.close()
        except Exception as e:
            print(f"News worker error: {e}")
            
        await asyncio.sleep(2 * 60 * 60) # 2 hours

def start_scheduler():
    print("Starting background scheduler loops...")
    asyncio.create_task(cron_worker())
    asyncio.create_task(news_worker())
