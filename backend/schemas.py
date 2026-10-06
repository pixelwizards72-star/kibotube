from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CredentialBase(BaseModel):
    platform: str
    is_connected: bool = False
    username: Optional[str] = None
    followers: int = 0
    
    # Optional fields returned to frontend
    page_id: Optional[str] = None
    page_name: Optional[str] = None
    subscribers: Optional[int] = 0

class CredentialOut(CredentialBase):
    id: int
    class Config:
        from_attributes = True

class PostBase(BaseModel):
    content: str
    image_url: Optional[str] = None
    content_type: str = "post"
    platform: str
    source_engine: str = "engine_1"
    scheduled_time: Optional[datetime] = None

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    content: Optional[str] = None
    is_approved: Optional[bool] = None
    likes_count: Optional[int] = None
    shares_count: Optional[int] = None
    comments_count: Optional[int] = None
    impressions: Optional[int] = None

class PostOut(PostBase):
    id: int
    is_approved: bool
    is_published: bool
    error_message: Optional[str] = None
    likes_count: int
    shares_count: int
    comments_count: int
    impressions: int

    class Config:
        from_attributes = True

class MessageOut(BaseModel):
    id: int
    platform: str
    sender_handle: str
    content: str
    is_read: bool
    timestamp: datetime

    class Config:
        from_attributes = True

class AgentConfigBase(BaseModel):
    gemini_api_key: str
    focus_areas: str
    tone_of_voice: str
    post_patterns: str
    response_style: str
    auto_pilot: bool
    news_engine_enabled: bool = False
    news_rss_url: Optional[str] = None

class AgentConfigOut(AgentConfigBase):
    id: int
    class Config:
        from_attributes = True

class StatSummary(BaseModel):
    total_likes: int
    total_shares: int
    total_comments: int
    total_impressions: int
    platform: Optional[str] = None
