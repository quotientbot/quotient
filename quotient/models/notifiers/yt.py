import logging
import os
from datetime import timedelta

import discord
import httpx
from fastapi import Path
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from tortoise import fields

from quotient.models import BaseDbModel

logger = logging.getLogger(os.getenv("INSTANCE_TYPE"))


class YtChannelSnippet(BaseModel):
    title: str
    description: str
    thumbnails: dict

    @property
    def thumbnail(self):
        return self.thumbnails["default"]["url"]


class YtChannel(BaseModel):
    id: str
    snippet: YtChannelSnippet

    @property
    def yt_channel_url(self):
        return f"https://www.youtube.com/channel/{self.id}"


class YtNotification(BaseDbModel):
    class Meta:
        table = "yt_notifications"

    id = fields.UUIDField(primary_key=True)
    discord_channel_id = fields.BigIntField()
    discord_guild_id = fields.BigIntField()

    yt_channel_id = fields.CharField(max_length=100)
    yt_channel_username = fields.CharField(max_length=100)
    regular_video_msg = fields.CharField(max_length=255, default="{ping} {channel} just uploaded {title} at {link}!")
    live_video_msg = fields.CharField(max_length=255, default="{ping} {channel} just went live at {link}!")

    ping_role_id = fields.BigIntField(null=True)

    lease_ends_at = fields.DatetimeField()  # Time before which we must resubscribe to pubsubhubbub.

    @property
    def yt_channel_url(self):
        return f"https://www.youtube.com/channel/{self.yt_channel_id}"

    @staticmethod
    async def search_yt_channel(username: str) -> YtChannel | None:
        async with httpx.AsyncClient() as client:

            # Check if input is a username
            url = f"https://www.googleapis.com/youtube/v3/channels"
            params = {
                "part": "snippet",
                "forHandle": username.strip(),
                "key": os.getenv("YT_API_KEY"),
                "maxResults": 1,
            }
            response = await client.get(url, params=params)
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                return YtChannel(**data["items"][0])

        return None

    @staticmethod
    async def get_video_by_id(yt_video_id: str):
        async with httpx.AsyncClient() as client:
            url = f"https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "snippet",
                "id": yt_video_id,
                "key": os.getenv("YT_API_KEY"),
                "maxResults": 1,
            }
            response = await client.get(url, params=params)
            data = response.json()

            logger.debug(f"Video details fetched for {yt_video_id}: {data}")

            if "items" in data and len(data["items"]) > 0:
                return data["items"][0]
        return None

    @staticmethod
    async def get_record(record: str = Path(...)) -> "YtNotification":
        if not (r := await YtNotification.get_or_none(id=record)):
            raise HTTPException(status_code=400, detail="Bad Request")

        return r

    async def setup_or_resubscribe(self) -> None:
        """
        Sets up or resubscribes the notifier to receive notifications from a YouTube channel.

        This function sends a POST request to the YouTube PubSubHubbub endpoint to subscribe to the channel's feed.
        It includes the necessary parameters such as the callback URL, mode, topic, verification tokens, and lease duration.

        Raises:
            httpx.HTTPError: If the POST request to the PubSubHubbub endpoint fails.
        """
        async with httpx.AsyncClient() as client:
            url = "https://pubsubhubbub.appspot.com/subscribe"
            data = {
                "hub.callback": os.getenv("YT_CALLBACK_URL") + f"/{self.id}",
                "hub.mode": "subscribe",
                "hub.topic": f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={self.yt_channel_id}",
                "hub.verify": "async",
                "hub.verify_token": os.getenv("YT_SUBSCRIBE_REQ_TOKEN"),  # YT regularly sends a GET request to verify the sub
                "hub.secret": os.getenv("YT_NOTIFICATION_TOKEN"),  # YT sends a POST request with a signature to verify the noti
                "hub.lease_seconds": 86400,  # 24 hours
            }
            response = await client.post(url, data=data)
            self.bot.logger.debug(f"Subscribing to {self.yt_channel_id} - {response.text}")
            response.raise_for_status()

            self.lease_ends_at = self.bot.current_time + timedelta(seconds=86400)
            await self.save(update_fields=["lease_ends_at"])

    async def send_notification(self, channel: str, title: str, link: str, video_type: str):
        """
        Sends a notification to the Discord channel when a new video is uploaded to the YouTube channel.

        Args:
            channel (str): The name of the YouTube channel.
            title (str): The title of the video.
            link (str): The URL of the video.
        """
        if video_type == "live":
            if not self.bot.is_pro_guild(self.discord_guild_id):
                return

        msg = (self.live_video_msg if video_type == "live" else self.regular_video_msg).format(
            ping=f"<@&{self.ping_role_id}>" if self.ping_role_id else "",
            channel=channel,
            title=title,
            link=link,
        )

        channel: discord.TextChannel | None = await self.bot.get_or_fetch(
            self.bot.get_channel, self.bot.fetch_channel, self.discord_channel_id
        )
        if not channel:
            return await self.delete()

        try:
            await channel.send(msg, allowed_mentions=discord.AllowedMentions(roles=[self.ping_role_id]) if self.ping_role_id else None)
        except discord.HTTPException as e:
            self.bot.logger.error(f"Failed to yt send notification to {channel.id} - {e}")
