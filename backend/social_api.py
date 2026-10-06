import httpx
import time
import asyncio
from typing import Optional
from . import models

class RateLimitError(Exception):
    pass

class SocialAPIClient:
    def __init__(self, platform: str, credential: models.Credential):
        self.platform = platform
        self.credential = credential
        self.max_retries = 3

    async def _request_with_backoff(self, method: str, url: str, **kwargs) -> httpx.Response:
        for attempt in range(self.max_retries):
            async with httpx.AsyncClient() as client:
                response = await client.request(method, url, **kwargs)
                if response.status_code == 429:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                response.raise_for_status()
                return response
        raise RateLimitError(f"Rate limit exceeded for {self.platform} after {self.max_retries} retries")

class MetaAPIClient(SocialAPIClient):
    def __init__(self, credential: models.Credential):
        super().__init__("meta", credential)
        self.base_url = "https://graph.facebook.com/v20.0"

    async def publish_post(self, content: str, page_id: str = "me") -> str:
        # Mocking actual implementation since we don't have real credentials
        # url = f"{self.base_url}/{page_id}/feed"
        # data = {"message": content, "access_token": self.credential.access_token}
        # response = await self._request_with_backoff("POST", url, data=data)
        # return response.json().get("id")
        
        # MOCK IMPLEMENTATION
        print(f"[META API] Publishing: {content}")
        await asyncio.sleep(1)
        return "mock_meta_post_123"

class XAPIClient(SocialAPIClient):
    def __init__(self, credential: models.Credential):
        super().__init__("x", credential)
        self.base_url = "https://api.twitter.com/2"

    async def publish_post(self, content: str) -> str:
        # url = f"{self.base_url}/tweets"
        # headers = {"Authorization": f"Bearer {self.credential.access_token}"}
        # json_data = {"text": content}
        # response = await self._request_with_backoff("POST", url, headers=headers, json=json_data)
        # return response.json().get("data", {}).get("id")
        
        # MOCK IMPLEMENTATION
        print(f"[X API] Publishing: {content}")
        await asyncio.sleep(1)
        return "mock_x_post_456"

class GenericMockClient(SocialAPIClient):
    def __init__(self, platform: str, credential: models.Credential):
        super().__init__(platform, credential)
    
    async def publish_post(self, content: str) -> str:
        print(f"[{self.platform.upper()} API] Publishing: {content}")
        await asyncio.sleep(1)
        return f"mock_{self.platform}_post_789"

def get_client(platform: str, credential: models.Credential) -> SocialAPIClient:
    if platform == "meta":
        return MetaAPIClient(credential)
    elif platform == "x":
        return XAPIClient(credential)
    return GenericMockClient(platform, credential)
