import httpx
import asyncio

async def test_webhooks():
    # Wait for backend to start
    await asyncio.sleep(2)
    
    # 1. Create a post
    print("Creating mock post...")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post("http://localhost:8000/posts/", json={
                "content": "A brand new day! ☀️",
                "platform": "meta"
            })
            post = res.json()
            post_id = post["id"]
            print(f"Created post: {post_id}")
            
            # 2. Approve post
            print("Approving post...")
            await client.put(f"http://localhost:8000/posts/{post_id}", json={
                "is_approved": True
            })
            
            # 3. Create mock comment (Webhook)
            print("Simulating incoming comment webhook...")
            await client.post("http://localhost:8000/comments/", json={
                "post_id": post_id,
                "external_comment_id": "ext_123",
                "user_handle": "alice",
                "content": "Love this! What are your plans?"
            })
            print("Webhook sent successfully.")
            
        except Exception as e:
            print(f"E2E Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_webhooks())
