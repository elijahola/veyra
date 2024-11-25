import os
from utils.twitter_clients import get_read_client
from utils.database import get_db
from utils.rate_limit import RateLimiter
from datetime import datetime, timedelta

# MongoDB setup
db = get_db()
tweets_collection = db["tweets"]
nodes_collection = db["nodes"]

# Twitter Client
read_client = get_read_client()

# Hardcoded strong nodes
HARDCODED_NODES = [
    "bonk_inu",
    "moodengx",
    "abblecoin",
    "stevabble",
    "finnbags",
    "SolanaSensei",
    "sistineresearch",
    "SolanaLegend",
    "DegenerateNews",
    "frankdegods",
    "fxnction",
    "MustStopMurad",
    "CrashiusClay69",
    "MinisterOfNFTs",
    "colu_farmer",
    "JoshiedNFT",
    "CryptoKaleo",
    "cryptocom",
    "theunipcs",
    "iamkadense",
    "blknoiz06",
    "MacroCRG",
    "jyu_eth",
    "himgajria",
    "shawmakesmagic",
    "alphawifhat",
    "trader1sz",
    "beingRich2000",
    "just4sol",
    "notthreadguy",
    "pumpdotscience",
    "_kaitoai",
    "kunoo",
    "Rizzy1c",
    "Noahhweb3",
    "SolJakey",
    "nameisproh",
    "coingecko",
    "ShiLLin_ViLLian",
    "dubzyxbt",
    "Crouserrr",
    "moonshot",
    "RobinhoodApp",
    "shahh",
    "phantom",
    "moonshilla",
    "Regrets10x",
    "justindaily",
    "MediaGiraffes",
    "juxtin4fitness",
]



# Keywords/hashtags to filter relevant tweets
RELEVANT_KEYWORDS = [
    "$Abble", "#AbbleCoin", "AbbleCoin", "abble", "Abble",
    "meme", "meme stocks", "meme stonks", "stonks", "crypto", "solana",
    "spx", "pepe", "bonk", "wif", "moodeng", "dog wif hat", "fwog",
    "popcat", "lockin", "michi", "sigma", "truth terminal", "AI",
    "vvaifu", "ai16z", "act I", "mustard", "goat", "kacy", "fatha",
    "bully", "dolos", "shoggoth", "gnon", "luna", "virtuals", "forest",
    "chill guy", "quant", "supercycle real", "uro", "rif", "jarvis",
    "pnut", "ponke", "apu", "gme", "zerebro", "dna", "phdegens",
    "stonks", "stonksguy", "lester", "degods", "degodmode", "letsbonk",
    "#letsbonk", "bonk",
]

def is_tweet_relevant(content):
    return any(keyword.lower() in content.lower() for keyword in RELEVANT_KEYWORDS)

def fetch_tweets_from_nodes(nodes, max_tweets=10):
    stored_tweets = 0
    rate_limiter = RateLimiter(max_calls=15, period=15 * 60)

    for node in nodes:
        try:
            rate_limiter.wait_for_slot()

            user_data = nodes_collection.find_one({"username": node}, {"user_id": 1})
            if not user_data:
                print(f"User ID for {node} not cached. Skipping.")
                continue

            user_id = user_data["user_id"]
            start_time = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
            response = read_client.get_users_tweets(
                id=user_id,
                max_results=max_tweets,
                start_time=start_time,
                tweet_fields=["created_at", "text", "public_metrics"],
                exclude=["retweets", "replies"]
            )

            if not response.data:
                print(f"No tweets found for {node}.")
                continue

            for tweet in response.data:
                if not is_tweet_relevant(tweet.text):
                    continue

                if tweets_collection.find_one({"tweet_id": tweet.id}):
                    print(f"Tweet {tweet.id} already exists. Skipping.")
                    continue

                tweets_collection.insert_one({
                    "tweet_id": tweet.id,
                    "content": tweet.text,
                    "created_at": tweet.created_at,
                    "username": node,
                    "metrics": tweet.public_metrics,
                })
                stored_tweets += 1

                if stored_tweets >= max_tweets:
                    print("[Info] Reached max tweets limit. Stopping.")
                    return

        except Exception as e:
            print(f"[Error] Failed to fetch tweets for {node}: {e}")
            continue

    print(f"[Info] Total tweets stored: {stored_tweets}")

def handler(req, res):
    fetch_tweets_from_nodes(HARDCODED_NODES, max_tweets=10)
    return res.json({"status": "success", "message": "Tweets fetched successfully."})

