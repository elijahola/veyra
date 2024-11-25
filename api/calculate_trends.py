from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import os

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["veyra"]
tweets_collection = db["tweets"]
trends_collection = db["sentiment_trends"]

def calculate_sentiment_trends():
    try:
        print("[Info] Calculating sentiment trends...")
        trends = tweets_collection.aggregate([
            {
                "$group": {
                    "_id": {"day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}},
                    "average_sentiment": {"$avg": "$sentiment_score"},
                    "total_tweets": {"$sum": 1}
                }
            },
            {"$sort": {"_id.day": 1}}
        ])

        for trend in trends:
            trends_collection.update_one(
                {"day": trend["_id"]["day"]},
                {
                    "$set": {
                        "average_sentiment": trend["average_sentiment"],
                        "total_tweets": trend["total_tweets"],
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True,
            )
            print(f"[Success] Updated sentiment trend for {trend['_id']['day']}")
        return {"status": "success", "message": "Sentiment trends updated successfully."}
    except Exception as e:
        print(f"[Error] Failed to calculate sentiment trends: {e}")
        return {"status": "error", "message": str(e)}

def extract_trending_hashtags(limit=10):
    try:
        print("[Info] Extracting trending hashtags...")
        tweets = tweets_collection.find({}, {"content": 1})
        hashtag_count = {}

        for tweet in tweets:
            hashtags = [word.lower() for word in tweet["content"].split() if word.startswith("#")]
            for hashtag in hashtags:
                hashtag_count[hashtag] = hashtag_count.get(hashtag, 0) + 1

        sorted_hashtags = sorted(hashtag_count.items(), key=lambda x: x[1], reverse=True)
        trending = sorted_hashtags[:limit]
        print(f"[Success] Trending hashtags: {trending}")
        return {"status": "success", "trending_hashtags": trending}
    except Exception as e:
        print(f"[Error] Failed to extract trending hashtags: {e}")
        return {"status": "error", "message": str(e)}

def handler(req, res):
    trends_response = calculate_sentiment_trends()
    hashtags_response = extract_trending_hashtags()

    return res.json({
        "sentiment_trends": trends_response,
        "trending_hashtags": hashtags_response
    })
