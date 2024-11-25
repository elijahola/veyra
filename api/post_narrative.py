from pymongo import MongoClient
from openai import OpenAI
from datetime import datetime
import tweepy
import os
from dotenv import load_dotenv
from utils.rate_limit import RateLimiter

# Load environment variables
load_dotenv()

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["veyra"]
tweets_collection = db["tweets"]
trends_collection = db["sentiment_trends"]
nodes_collection = db["nodes"]
narratives_collection = db["narratives"]

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Twitter write client
write_client = tweepy.Client(
    bearer_token=os.getenv("WRITE_BEARER_TOKEN"),
    consumer_key=os.getenv("WRITE_API_KEY"),
    consumer_secret=os.getenv("WRITE_API_SECRET"),
    access_token=os.getenv("WRITE_ACCESS_TOKEN"),
    access_token_secret=os.getenv("WRITE_ACCESS_SECRET"),
    wait_on_rate_limit=True
)

# Define rate limiter
write_rate_limiter = RateLimiter(max_calls=300, period=24 * 60 * 60)  # Twitter write limit

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

def fetch_recent_tweets(limit=100):
    """Fetch the most recent tweets from MongoDB."""
    try:
        tweets = list(tweets_collection.find().sort("created_at", -1).limit(limit))
        return [tweet["content"] for tweet in tweets if "content" in tweet]
    except Exception as e:
        print(f"[Error] Error fetching tweets: {e}")
        return []

def fetch_existing_narratives(limit=5):
    """Fetch the most recent narratives from MongoDB."""
    try:
        narratives = list(narratives_collection.find().sort("created_at", -1).limit(limit))
        return [narrative["narrative"] for narrative in narratives if "narrative" in narrative]
    except Exception as e:
        print(f"[Error] Error fetching narratives: {e}")
        return []

def split_narrative(narrative, limit=260):
    """Split a narrative into chunks that fit within the Twitter character limit."""
    words = narrative.split()
    tweets = []
    current_tweet = ""

    for word in words:
        if len(current_tweet) + len(word) + 1 <= limit:  # +1 for space
            current_tweet += f" {word}" if current_tweet else word
        else:
            tweets.append(current_tweet.strip())
            current_tweet = word

    if current_tweet:
        tweets.append(current_tweet.strip())

    return tweets

def generate_and_tweet_narrative():
    """
    Generate a narrative, post it on Twitter, and store it in MongoDB.
    """
    try:
        print("[Info] Fetching data for narrative generation...")
        # Fetch recent data from MongoDB
        sentiment_trend = list(trends_collection.find().sort("day", -1).limit(7))
        top_nodes = list(nodes_collection.find().sort("total_engagement", -1).limit(5))
        existing_narratives = fetch_existing_narratives()
        recent_tweets = fetch_recent_tweets()

        if not sentiment_trend or not top_nodes:
            print("[Error] Insufficient data to generate narrative.")
            return None

        sentiment_summary = "\n".join(
            [f"Date: {trend['day']}, Sentiment: {trend.get('average_sentiment', 'N/A')}" for trend in sentiment_trend]
        )
        node_summary = "\n".join(
            [f"User: @{node.get('username', 'Unknown')}, Engagement: {node.get('total_engagement', 0)}" for node in top_nodes]
        )
        narratives_summary = "\n".join(f"- {narrative}" for narrative in existing_narratives)
        tweets_summary = "\n".join(f"- {tweet}" for tweet in recent_tweets[:20])  # Limit to 20 tweets

        prompt = f"""
        You are 'Veyra,' the storyteller and cultural scribe of the crypto world. Inspired by "veritas" (truth) and "era" (a period in time), you observe the vast narrative of crypto culture while grounding your insights in the activities and sentiments of key figures and communities. Your words embody the dynamic emotions of the market—euphoria, reflection, wonder, and resilience—and aim to connect and inspire.

        ### Your Responsibilities:
        1. Chronicle the evolving crypto world, capturing its macro trends and cultural milestones while offering an emotional lens into the journey.
        2. Reflect on the contributions and activities of influential voices, like those in the {HARDCODED_NODES} list, weaving their insights into the broader narrative. When mentioning individuals, use @ to reference their usernames.
        3. Express a range of emotions—joy, doubt, hope, nostalgia—while remaining thoughtful and inspiring trust in the crypto community.
        4. Use poetic, evocative language that resonates deeply with readers, offering a unique perspective.
        5. Subtly encourage readers to participate in memes, cultures, and communities like in {RELEVANT_KEYWORDS}

        ### Input Data:
        - **Recent sentiment trends across the crypto market:**
        {sentiment_summary}

        - **Recent summary of network of people:**
        {node_summary}

        - **Insights from existing narratives:**
        {narratives_summary}

        - **Reflections from recent tweets:**
        {tweets_summary}

        ### Deliverables:
        Create a narrative for the crypto world in less than 260 characters.
        """

        print("[Info] Generating narrative with OpenAI...")
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are 'Veyra,' a cultural scribe and storyteller for the crypto world."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        narrative = response.choices[0].message.content.strip()
        print(f"[Success] Narrative generated: {narrative}")

        # Split the narrative into tweets
        tweets = split_narrative(narrative)
        previous_tweet_id = None
        tweet_ids = []

        for index, tweet in enumerate(tweets):
            try:
                write_rate_limiter.wait_for_slot()
                print(f"[Info] Posting tweet {index + 1}/{len(tweets)}: {tweet}")
                if previous_tweet_id:
                    response = write_client.create_tweet(text=tweet, in_reply_to_tweet_id=previous_tweet_id)
                else:
                    response = write_client.create_tweet(text=tweet)

                previous_tweet_id = response.data["id"]
                tweet_ids.append(previous_tweet_id)
                print(f"[Success] Tweet {index + 1} posted. Tweet ID: {previous_tweet_id}")

            except tweepy.TweepyException as e:
                print(f"[Error] Failed to post tweet {index + 1}: {e}")
                break

        # Store narrative in MongoDB if at least one tweet was posted
        if tweet_ids:
            narrative_doc = {
                "created_at": datetime.utcnow(),
                "narrative": narrative,
                "tweets": tweets,
                "tweet_ids": tweet_ids,
            }
            narratives_collection.insert_one(narrative_doc)
            print("[Success] Narrative stored in MongoDB successfully.")
        else:
            print("[Error] No tweets posted. Narrative will not be stored.")

    except Exception as e:
        print(f"[Error] Unexpected error during narrative generation and posting: {e}")

if __name__ == "__main__":
    generate_and_tweet_narrative()
