import tweepy
import os

def get_read_client():
    """Initialize Twitter client for read operations."""
    return tweepy.Client(
        bearer_token=os.getenv("READ_BEARER_TOKEN"),
        consumer_key=os.getenv("READ_API_KEY"),
        consumer_secret=os.getenv("READ_API_SECRET"),
        access_token=os.getenv("READ_ACCESS_TOKEN"),
        access_token_secret=os.getenv("READ_ACCESS_SECRET"),
        wait_on_rate_limit=True,
    )

def get_write_client():
    """Initialize Twitter client for write operations."""
    return tweepy.Client(
        bearer_token=os.getenv("WRITE_BEARER_TOKEN"),
        consumer_key=os.getenv("WRITE_API_KEY"),
        consumer_secret=os.getenv("WRITE_API_SECRET"),
        access_token=os.getenv("WRITE_ACCESS_TOKEN"),
        access_token_secret=os.getenv("WRITE_ACCESS_SECRET"),
        wait_on_rate_limit=True,
    )
