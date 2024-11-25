from utils.twitter_clients import get_read_client
from utils.database import get_db
from utils.rate_limit import RateLimiter

def fetch_followers(username="AbbleIntel", max_followers=1000):
    db = get_db()
    followers_collection = db["followers"]
    client = get_read_client()
    rate_limiter = RateLimiter(max_calls=15, period=15 * 60)

    user_response = client.get_user(username=username)
    user_id = user_response.data.id
    all_followers = []
    pagination_token = None

    while len(all_followers) < max_followers:
        rate_limiter.wait_for_slot()
        response = client.get_users_followers(
            id=user_id,
            max_results=100,
            pagination_token=pagination_token
        )
        all_followers.extend(response.data)
        pagination_token = response.meta.get("next_token")
        if not pagination_token:
            break

    for follower in all_followers:
        followers_collection.update_one(
            {"user_id": follower.id}, {"$set": follower}, upsert=True
        )

    return {"status": "success", "count": len(all_followers)}

def handler(req, res):
    response = fetch_followers()
    return res.json(response)
