import logging
from json import JSONDecodeError

import fastjsonschema
from httpx import AsyncClient, HTTPError, Headers

from .schemas import schema


class Twitter:
    def __init__(self, token: str):
        self.client = AsyncClient()
        self.client.headers = Headers({
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "holo observatory bot/1.0.0"
        })

    async def fetch(self, user_id: int, since_id: int = 1):
        url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        payload = {
            "user_id": user_id,
            "since_id": since_id,
            "exclude_replies": True,
            "include_rts": True
        }

        try:
            resp = await self.client.get(url, params=payload)
        except HTTPError:
            logging.error("Twitter api fetch error.")
            return since_id, None

        try:
            r = resp.json()
            schema(r)
        except (JSONDecodeError, fastjsonschema.JsonSchemaException):
            logging.error(f"Malformed Twitter API response: {resp.text}")
            return since_id, None

        if not r:
            return since_id, None

        tweet_list = []
        for _, tweet in zip(range(5), r):
            is_rt = "retweeted_status" in tweet.keys()
            tweet_text = tweet["text"]
            tweet_media = tweet["entities"].get("media", [])
            tweet_photos = [medium["media_url"] for medium in tweet_media if medium["type"] == "photo"]
            tweet_list.append((tweet_text, tweet_photos, is_rt))

        return r[0]["id"], tweet_list
