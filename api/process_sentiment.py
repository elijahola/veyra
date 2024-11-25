from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from utils.database import get_db
from pymongo import UpdateOne

def process_sentiment():
    db = get_db()
    tweets_collection = db["tweets"]
    analyzer = SentimentIntensityAnalyzer()

    tweets = tweets_collection.find({"sentiment_score": {"$exists": False}})
    operations = []
    for tweet in tweets:
        sentiment = analyzer.polarity_scores(tweet["content"])["compound"]
        operations.append(
            UpdateOne({"_id": tweet["_id"]}, {"$set": {"sentiment_score": sentiment}})
        )

    if operations:
        tweets_collection.bulk_write(operations)

    return {"status": "success"}

def handler(req, res):
    response = process_sentiment()
    return res.json(response)
