import datetime
import random
from sqlalchemy.orm import Session
from backend.database import engine, Base, SessionLocal
from backend import models

# Recreate all tables
Base.metadata.create_all(bind=engine)

def seed_db():
    db = SessionLocal()
    
    # Check if already seeded (by checking AgentConfig)
    if not db.query(models.AgentConfig).first():
        print("Seeding database with mock data...")
        
        # 1. Agent Config
        config = models.AgentConfig(
            gemini_api_key="",
            focus_areas="Tech, General",
            tone_of_voice="Professional",
            post_patterns="Short paragraphs",
            response_style="Helpful and polite"
        )
        db.add(config)
        
        # 2. Connections (Profiles)
        platforms = ['meta', 'x', 'tiktok', 'instagram']
        for p in platforms:
            cred = models.Credential(
                platform=p,
                username=f"kibotube_{p}",
                followers=random.randint(5000, 50000),
                subscribers=random.randint(1000, 10000),
                is_connected=False
            )
            db.add(cred)
            
        db.commit()

        # 3. Posts (30 Day Planner)
        now = datetime.datetime.utcnow()
        # Seed past 15 days, today, and future 15 days
        for i in range(-15, 16):
            # Create 1-3 posts per day
            for _ in range(random.randint(1, 3)):
                scheduled_time = now + datetime.timedelta(days=i)
                # Add some random hour/minute jitter
                scheduled_time = scheduled_time.replace(
                    hour=random.randint(8, 20), 
                    minute=random.randint(0, 59)
                )
                
                platform = random.choice(platforms)
                content_type = random.choice(["post", "reel", "story"])
                
                post = models.Post(
                    content=f"Mock scheduled {content_type} for {platform} on day {i}. #planning",
                    image_url=f"https://image.pollinations.ai/prompt/professional%20content%20day%20{i}?width=800&height=600&nologo=true",
                    content_type=content_type,
                    platform=platform,
                    source_engine="engine_1",
                    scheduled_time=scheduled_time,
                    is_approved=True,
                    is_published=scheduled_time < now, # Published if in the past
                    likes_count=random.randint(10, 500) if scheduled_time < now else 0,
                    shares_count=random.randint(1, 50) if scheduled_time < now else 0,
                    comments_count=random.randint(0, 100) if scheduled_time < now else 0,
                    impressions=random.randint(1000, 5000) if scheduled_time < now else 0
                )
                db.add(post)
                
        # 4. Messages (Unified Inbox)
        for _ in range(20):
            msg = models.Message(
                platform=random.choice(platforms),
                sender_handle=f"user_{random.randint(100,999)}",
                content=random.choice([
                    "Hey, how much is your service?",
                    "I love your recent post!",
                    "Do you offer customer support on weekends?",
                    "Can we collaborate?",
                    "Please check my DM!"
                ]),
                is_read=random.choice([True, False]),
                timestamp=now - datetime.timedelta(hours=random.randint(1, 48))
            )
            db.add(msg)
            
        db.commit()
        print("Database seeded successfully with Meta Business Suite mock data!")
    else:
        print("Database already seeded.")
        
    db.close()

if __name__ == "__main__":
    seed_db()
