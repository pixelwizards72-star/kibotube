from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from contextlib import asynccontextmanager
from pydantic import BaseModel

from . import models, schemas, database, scheduler, ai_agent
from .database import engine

models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start_scheduler()
    yield

app = FastAPI(title="KiboTube Meta Business Suite V2", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to KiboTube Meta Business Suite"}

@app.get("/profiles/", response_model=List[schemas.CredentialOut])
def get_profiles(db: Session = Depends(database.get_db)):
    return db.query(models.Credential).all()

@app.post("/profiles/connect/{platform}", response_model=schemas.CredentialOut)
def connect_profile(platform: str, username: str, db: Session = Depends(database.get_db)):
    cred = db.query(models.Credential).filter(models.Credential.platform == platform).first()
    if not cred:
        cred = models.Credential(platform=platform)
        db.add(cred)
    cred.username = username
    cred.is_connected = True
    cred.followers = 15400
    cred.subscribers = 2300
    db.commit()
    db.refresh(cred)
    return cred

@app.post("/posts/", response_model=schemas.PostOut)
def create_post(post: schemas.PostCreate, db: Session = Depends(database.get_db)):
    db_post = models.Post(**post.dict())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.get("/posts/", response_model=List[schemas.PostOut])
def read_posts(skip: int = 0, limit: int = 100, platform: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.Post)
    if platform and platform != "all":
        query = query.filter(models.Post.platform == platform.lower())
    return query.order_by(models.Post.scheduled_time.asc()).offset(skip).limit(limit).all()

@app.put("/posts/{post_id}", response_model=schemas.PostOut)
def update_post(post_id: int, post_update: schemas.PostUpdate, db: Session = Depends(database.get_db)):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    update_data = post_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_post, key, value)
        
    db.commit()
    db.refresh(db_post)
    return db_post

@app.get("/inbox/", response_model=List[schemas.MessageOut])
def get_inbox(platform: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.Message)
    if platform and platform != "all":
        query = query.filter(models.Message.platform == platform.lower())
    return query.order_by(models.Message.timestamp.desc()).all()

@app.get("/agent-config/", response_model=schemas.AgentConfigOut)
def get_agent_config(db: Session = Depends(database.get_db)):
    config = db.query(models.AgentConfig).first()
    if not config:
        config = models.AgentConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@app.put("/agent-config/", response_model=schemas.AgentConfigOut)
def update_agent_config(config_update: schemas.AgentConfigBase, db: Session = Depends(database.get_db)):
    config = db.query(models.AgentConfig).first()
    if not config:
        config = models.AgentConfig(**config_update.dict())
        db.add(config)
    else:
        update_data = config_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config

@app.get("/stats/", response_model=schemas.StatSummary)
def get_stats(platform: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(
        func.sum(models.Post.likes_count).label('total_likes'),
        func.sum(models.Post.shares_count).label('total_shares'),
        func.sum(models.Post.comments_count).label('total_comments'),
        func.sum(models.Post.impressions).label('total_impressions')
    )
    if platform and platform != "all":
        query = query.filter(models.Post.platform == platform.lower())
    result = query.first()
    return schemas.StatSummary(
        total_likes=result.total_likes or 0,
        total_shares=result.total_shares or 0,
        total_comments=result.total_comments or 0,
        total_impressions=result.total_impressions or 0,
        platform=platform
    )

class DraftRequest(BaseModel):
    focus_area: str
    description: str
    tone: str
    platform: str
    content_type: str
    rss_url: Optional[str] = None

class BulkDraftRequest(DraftRequest):
    days: int
    source_engine: str = "engine_1"
    posts_per_day: int = 1

@app.post("/ai/generate-draft")
async def generate_draft(req: DraftRequest):
    content, image_url = await ai_agent.ai_engine.generate_manual_draft(
        req.focus_area, req.description, req.tone, req.platform, req.content_type, req.rss_url
    )
    return {"content": content, "image_url": image_url}

@app.post("/ai/generate-bulk")
async def generate_bulk(req: BulkDraftRequest, db: Session = Depends(database.get_db)):
    try:
        count = await ai_agent.ai_engine.generate_bulk_schedule(
            req.days, req.focus_area, req.description, req.tone, req.platform, req.content_type, req.rss_url, req.source_engine, req.posts_per_day
        )
        return {"status": "success", "scheduled_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# Simulated OAuth 2.0 Endpoints
# ==========================================

class AuthCallback(BaseModel):
    code: str

@app.post("/auth/{platform}/callback")
def auth_callback(platform: str, req: AuthCallback, db: Session = Depends(database.get_db)):
    """Simulates exchanging an auth code for access tokens."""
    import random
    
    profile = db.query(models.Credential).filter(models.Credential.platform == platform).first()
    if not profile:
        profile = models.Credential(platform=platform)
        db.add(profile)
        
    profile.is_connected = True
    profile.access_token = f"simulated_access_token_{random.randint(1000,9999)}"
    profile.refresh_token = f"simulated_refresh_token_{random.randint(1000,9999)}"
    profile.token_expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=60)
    profile.followers = random.randint(1000, 100000)
    
    if platform != "meta":
        profile.username = f"RealUser_{platform}_{random.randint(10,99)}"
        
    db.commit()
    db.refresh(profile)
    return profile

@app.get("/auth/facebook/pages")
def get_facebook_pages(db: Session = Depends(database.get_db)):
    """Simulates fetching the Facebook Pages the authenticated user administers."""
    profile = db.query(models.Credential).filter(models.Credential.platform == "meta").first()
    if not profile or not profile.access_token:
        raise HTTPException(status_code=401, detail="Not authenticated with Facebook")
    
    # Return mock pages
    return [
        {"id": "1001", "name": "My Business Official Page", "category": "Brand"},
        {"id": "1002", "name": "My Personal Creator Page", "category": "Creator"},
        {"id": "1003", "name": "Test Sandbox Page", "category": "Community"}
    ]

class SelectPageReq(BaseModel):
    page_id: str
    page_name: str

@app.post("/auth/facebook/select-page")
def select_facebook_page(req: SelectPageReq, db: Session = Depends(database.get_db)):
    profile = db.query(models.Credential).filter(models.Credential.platform == "meta").first()
    if not profile:
        raise HTTPException(status_code=404, detail="Meta profile not found")
        
    profile.page_id = req.page_id
    profile.page_name = req.page_name
    profile.username = req.page_name # Map username to page name for UI
    db.commit()
    return {"status": "success", "page_name": req.page_name}
