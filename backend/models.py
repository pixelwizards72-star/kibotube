from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Credential(Base):
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, unique=True, index=True)
    is_connected = Column(Boolean, default=False)
    username = Column(String, nullable=True)
    followers = Column(Integer, default=0)
    
    # OAuth 2.0 Credentials
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    # Platform specific metadata
    page_id = Column(String, nullable=True)     # For Facebook Pages
    page_name = Column(String, nullable=True)   # For Facebook Pages
    subscribers = Column(Integer, default=0)
    api_key = Column(String, nullable=True)
    api_secret = Column(String, nullable=True)

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    image_url = Column(String, nullable=True)
    content_type = Column(String, default="post") # 'post', 'reel', 'story'
    platform = Column(String, index=True)
    source_engine = Column(String, default="engine_1")
    scheduled_time = Column(DateTime, default=datetime.datetime.utcnow)
    is_approved = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)
    error_message = Column(String, nullable=True)
    
    likes_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    
    comments = relationship("Comment", back_populates="post")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    external_comment_id = Column(String, index=True)
    user_handle = Column(String)
    content = Column(String)
    reply_draft = Column(String, nullable=True)
    is_approved = Column(Boolean, default=False)
    is_replied = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    post = relationship("Post", back_populates="comments")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, index=True)
    sender_handle = Column(String)
    content = Column(String)
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class AgentConfig(Base):
    __tablename__ = "agent_config"

    id = Column(Integer, primary_key=True, index=True)
    gemini_api_key = Column(String, default="")
    focus_areas = Column(String, default="")
    tone_of_voice = Column(String, default="Professional yet engaging")
    post_patterns = Column(String, default="Short paragraphs")
    response_style = Column(String, default="Helpful and polite")
    auto_pilot = Column(Boolean, default=False)
    news_engine_enabled = Column(Boolean, default=False)
    news_rss_url = Column(String, nullable=True)

class ScrapedArticle(Base):
    __tablename__ = "scraped_articles"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    published_at = Column(DateTime, default=datetime.datetime.utcnow)
