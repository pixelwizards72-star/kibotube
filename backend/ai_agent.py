import asyncio
import json
import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models, rss_service

class RealGemini:
    def __init__(self, api_key: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def generate_content(self, prompt: str) -> str:
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            return f"[Gemini API Error]: {str(e)}"

    async def generate_image(self, prompt: str) -> str:
        try:
            import google.generativeai as genai
            model = genai.ImageGenerationModel("imagen-3.0-generate-001")
            result = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                output_mime_type="image/jpeg"
            )
            import base64
            encoded = base64.b64encode(result.images[0].image.image_bytes).decode('utf-8')
            return f"data:image/jpeg;base64,{encoded}"
        except Exception as e:
            print(f"Gemini Image API failed: {e}. Falling back to dynamic AI generation URL.")
            import urllib.parse
            encoded_prompt = urllib.parse.quote(prompt[:100])
            return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=600&nologo=true"

class MockGemini:
    async def generate_content(self, prompt: str) -> str:
        await asyncio.sleep(2) # simulate delay
        if "JSON" in prompt:
            days = 30
            if "EXACTLY 60" in prompt:
                days = 60
            posts = [f"Mock AI Bulk Post {i+1}: 🚀 Exploring the future! #tech #growth" for i in range(days)]
            return json.dumps(posts)

        if "draft" in prompt.lower() or "generate" in prompt.lower() or "write" in prompt.lower() or "rewrite" in prompt.lower():
            return "🚀 Based on top news and feedback, here is a highly engaging draft optimized for your audience!"
        elif "reply" in prompt.lower():
            return "Thanks for engaging! We love hearing from our community. 🙌"
        return "Generated content based on AI."

    async def generate_image(self, prompt: str) -> str:
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt[:100])
        return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=600&nologo=true"

class AIEngine:
    def _get_model(self, db: Session):
        config = db.query(models.AgentConfig).first()
        if config and config.gemini_api_key:
            return RealGemini(config.gemini_api_key)
        return MockGemini()

    def _get_top_posts_context(self, db: Session) -> str:
        top_posts = db.query(models.Post).order_by(
            (models.Post.likes_count + models.Post.shares_count + models.Post.comments_count).desc()
        ).limit(3).all()
        
        if not top_posts:
            return "No previous posts available."
            
        context = "Top Performing Posts Feedback:\n"
        for p in top_posts:
            context += f"- Content: '{p.content}' (Platform: {p.platform}, Engagement: {p.likes_count + p.shares_count + p.comments_count})\n"
        return context

    async def generate_draft_post(self, prompt: str) -> str:
        db = SessionLocal()
        try:
            config = db.query(models.AgentConfig).first()
            tone = config.tone_of_voice if config else "Professional"
            patterns = config.post_patterns if config else "Standard"
            
            feedback_context = self._get_top_posts_context(db)
            model = self._get_model(db)
            
            full_prompt = (
                f"You are managing a social media account. Tone: {tone}. Pattern: {patterns}.\n"
                f"Audience Feedback Context:\n{feedback_context}\n\n"
                f"Generate a social media draft post for the following prompt: {prompt}"
            )
            content = await model.generate_content(full_prompt)
            return content
        finally:
            db.close()

    async def generate_contextual_reply(self, comment_content: str, post_content: str) -> str:
        db = SessionLocal()
        try:
            config = db.query(models.AgentConfig).first()
            style = config.response_style if config else "Helpful and polite"
            model = self._get_model(db)
            
            prompt = (
                f"Response Style: {style}.\n"
                f"Write a contextual reply to the comment: '{comment_content}'. "
                f"Original post: '{post_content}'."
            )
            reply = await model.generate_content(prompt)
            return reply
        finally:
            db.close()

    async def generate_manual_draft(self, focus_area: str, description: str, tone: str, platform: str, content_type: str, rss_url: str = None) -> str:
        db = SessionLocal()
        try:
            model = self._get_model(db)
            
            rss_context = ""
            if rss_url:
                articles = rss_service.fetch_top_articles(rss_url, limit=3)
                if articles:
                    rss_context = "Here are trending topics from the provided RSS feed to base your content on:\n"
                    for a in articles:
                        rss_context += f"- Title: {a['title']}\n  Summary: {a['summary']}\n"

            full_prompt = (
                f"Tone of voice: {tone}.\n"
                f"Platform: {platform}. Format: {content_type}.\n"
                f"Focus Area: {focus_area}\n"
                f"Detailed Instructions: {description}\n\n"
                f"{rss_context}\n"
                f"Write a single, highly engaging social media post based on the above criteria."
            )
            content = await model.generate_content(full_prompt)
            image_url = await model.generate_image(f"A high quality professional image about {focus_area}")
            return content, image_url
        finally:
            db.close()

    async def generate_bulk_schedule(self, days: int, focus_area: str, description: str, tone: str, platform: str, content_type: str, rss_url: str = None, source_engine: str = "engine_1", posts_per_day: int = 1):
        db = SessionLocal()
        total_posts = days * posts_per_day
        try:
            model = self._get_model(db)
            
            rss_context = ""
            if rss_url:
                # Fetch up to 10 articles to give it enough meat for 30/60 days variation
                articles = rss_service.fetch_top_articles(rss_url, limit=10)
                if articles:
                    rss_context = "Here are trending topics from the provided RSS feed to base your content on:\n"
                    for a in articles:
                        rss_context += f"- Title: {a['title']}\n  Summary: {a['summary']}\n"

            full_prompt = (
                f"You are an expert social media manager.\n"
                f"Tone of voice: {tone}.\n"
                f"Platform: {platform}. Format: {content_type}.\n"
                f"Focus Area: {focus_area}\n"
                f"Detailed Instructions: {description}\n\n"
                f"{rss_context}\n"
                f"Your task is to generate EXACTLY {total_posts} unique, highly engaging social media posts based on the above criteria.\n"
                f"Output MUST be valid JSON. Do not wrap it in markdown code blocks, just raw JSON.\n"
                f"The JSON MUST be an array of strings, where each string is a post.\n"
                f"Example: [\"Post 1 content here\", \"Post 2 content here\"]\n"
            )
            
            raw_content = await model.generate_content(full_prompt)
            
            cleaned = raw_content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            try:
                posts_array = json.loads(cleaned)
                if not isinstance(posts_array, list):
                    raise ValueError("JSON is not a list")
            except Exception as e:
                print(f"Failed to parse JSON: {cleaned}")
                raise Exception(f"Failed to parse AI output into JSON array: {str(e)}")

            posts_array = posts_array[:total_posts]
            
            now = datetime.datetime.utcnow()
            for i, content in enumerate(posts_array):
                day_offset = (i // posts_per_day) + 1
                intra_day_offset = i % posts_per_day
                hours_offset = intra_day_offset * (24 / posts_per_day)
                
                scheduled_time = now + datetime.timedelta(days=day_offset, hours=hours_offset)
                
                # To prevent 60-minute API timeouts during bulk generation, we map Pollinations directly
                # However, if it's the RealGemini, we can try, but 60 sync calls will fail. 
                # Let's use the fallback URL approach for bulk.
                import urllib.parse
                img_prompt = f"High quality image for {focus_area} day {i}"
                enc_prompt = urllib.parse.quote(img_prompt)
                bulk_img_url = f"https://image.pollinations.ai/prompt/{enc_prompt}?width=800&height=600&nologo=true"

                new_post = models.Post(
                    content=content,
                    image_url=bulk_img_url,
                    content_type=content_type,
                    platform=platform,
                    source_engine=source_engine,
                    scheduled_time=scheduled_time,
                    is_approved=True,
                    is_published=False
                )
                db.add(new_post)
            db.commit()
            
            return len(posts_array)
            
        finally:
            db.close()

    async def generate_from_article(self, article: dict, tone: str) -> str:
        db = SessionLocal()
        try:
            model = self._get_model(db)
            full_prompt = (
                f"You are a top-tier social media manager for a news aggregate account.\n"
                f"Tone: {tone}\n"
                f"Here is a raw news article from an RSS feed:\n"
                f"Title: {article['title']}\n"
                f"Summary: {article['summary']}\n"
                f"Link: {article['link']}\n\n"
                f"Rewrite this into a highly engaging, concise social media post (e.g. for Twitter or Facebook). "
                f"Make sure to include a hook, summarize the key point, use appropriate hashtags, and append the link at the end."
            )
            content = await model.generate_content(full_prompt)
            image_url = await model.generate_image(f"A high quality professional image about {article['title']}")
            return content, image_url
        finally:
            db.close()

ai_engine = AIEngine()
