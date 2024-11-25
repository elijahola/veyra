from utils.twitter_clients import get_read_client
from utils.database import get_db
from utils.rate_limit import RateLimiter

def fetch_followers(username="AbbleIntel", max_followers=1000):
    """
    Fetch followers for a given Twitter username and store them in MongoDB.
    """
    db = get_db()
    followers_collection = db["followers"]
    client = get_read_client()
    rate_limiter = RateLimiter(max_calls=15, period=15 * 60)

    try:
        # Fetch user details
        user_response = client.get_user(username=username)
        if not user_response.data:
            return {"status": "error", "message": "User not found"}
        
        user_id = user_response.data.id
        all_followers = []
        pagination_token = None

        while len(all_followers) < max_followers:
            rate_limiter.wait_for_slot()
            try:
                # Fetch followers in batches
                response = client.get_users_followers(
                    id=user_id,
                    max_results=100,
                    pagination_token=pagination_token,
                )

                if not response.data:
                    break

                all_followers.extend(response.data)
                pagination_token = response.meta.get("next_token", None)
                if not pagination_token:
                    break

            except Exception as e:
                return {"status": "error", "message": f"Error fetching followers: {str(e)}"}

        # Store followers in MongoDB
        for follower in all_followers:
            followers_collection.update_one(
                {"user_id": follower.id}, {"$set": follower}, upsert=True
            )

        return {"status": "success", "count": len(all_followers)}

    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch followers: {str(e)}"}

def handler(req, res):
    """
    Vercel handler for the fetch_followers endpoint.
    """
    try:
        username = req.query.get("username", "AbbleIntel")  # Use a default if not provided
        max_followers = int(req.query.get("max_followers", 1000))  # Default to 1000
        response = fetch_followers(username=username, max_followers=max_followers)
        return res.json(response)
    except Exception as e:
        return res.json({"status": "error", "message": f"Handler error: {str(e)}"})
