import logging
import os
from datetime import datetime, timedelta
from itertools import cycle

import discord
import httpx
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


class YtVideo(BaseModel):
    id: str
    publishedAt: datetime
    channel_name: str | None = None
    title: str | None = None
    live: bool = False

    @property
    def watch_url(self):
        return f"https://www.youtube.com/watch?v={self.id}"


class YtNotification(BaseDbModel):
    YOUTUBE_API_KEYS = cycle(os.getenv("YT_API_KEYS").split(","))

    class Meta:
        table = "yt_notifications"

    id = fields.UUIDField(primary_key=True)
    discord_channel_id = fields.BigIntField()
    discord_guild_id = fields.BigIntField()

    yt_channel_id = fields.CharField(max_length=100)
    yt_upload_playlist_id = fields.CharField(max_length=100)
    yt_channel_username = fields.CharField(max_length=100)
    yt_last_video_id = fields.CharField(max_length=100, null=True)
    yt_last_uploaded_at = fields.DatetimeField(null=True)

    regular_video_msg = fields.CharField(max_length=255, default="{ping} {channel} just uploaded {title} at {link}!")
    live_video_msg = fields.CharField(max_length=255, default="{ping} {channel} just went live at {link}!")
    ping_role_id = fields.BigIntField(null=True)

    yt_last_fetched_at = fields.DatetimeField(auto_now=True)

    @property
    def yt_channel_url(self):
        return f"https://www.youtube.com/channel/{self.yt_channel_id}"

    async def search_yt_channel(self, username: str) -> YtChannel | None:
        async with httpx.AsyncClient() as client:

            # Check if input is a username
            url = f"https://www.googleapis.com/youtube/v3/channels"
            params = {
                "part": "snippet",
                "forHandle": username.strip(),
                "key": self.yt_api_key,
                "maxResults": 1,
            }
            response = await client.get(url, params=params)
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                return YtChannel(**data["items"][0])

        return None

    async def setup(self) -> None:
        self.yt_upload_playlist_id = await self.get_uploads_playlist_id(self.yt_channel_id)
        latest_video = await self.fetch_latest_video_details()

        if latest_video:
            self.yt_last_video_id = latest_video.id
            self.yt_last_uploaded_at = latest_video.publishedAt

        self.yt_last_fetched_at = self.bot.current_time
        await self.save()

    async def send_notification(self, video: YtVideo):
        """
        Sends a notification to the Discord channel when a new video is uploaded to the YouTube channel.
        """
        from quotient.cogs.premium import Feature, can_use_feature

        if video.live:
            is_allowed, _ = await can_use_feature(Feature.YT_LIVE_NOTI_SETUP, self.discord_guild_id)
            if not is_allowed:
                return

        msg = (self.live_video_msg if video.live else self.regular_video_msg).format(
            ping=f"<@&{self.ping_role_id}>" if self.ping_role_id else "",
            channel=video.channel_name,
            title=video.title,
            link=video.watch_url,
        )

        channel: discord.TextChannel | None = await self.bot.get_or_fetch(
            self.bot.get_channel, self.bot.fetch_channel, self.discord_channel_id
        )
        if not channel:
            return await self.delete()

        try:
            await channel.send(
                msg,
                allowed_mentions=discord.AllowedMentions(roles=[discord.Object(id=self.ping_role_id)]) if self.ping_role_id else None,
            )
        except discord.HTTPException as e:
            self.bot.logger.error(f"Failed to yt send notification to {channel.id} - {e}")
            pass

    @property
    def yt_api_key(self) -> str:
        """
        Returns the next available YouTube API key from the list of keys.
        """
        return next(YtNotification.YOUTUBE_API_KEYS)

    async def fetch_latest_video_details(self, partial: bool = True) -> YtVideo | None:
        """
        Fetches the details of the lastest uploaded video from the YouTube channel.
        """
        async with httpx.AsyncClient() as client:
            url = f"https://www.googleapis.com/youtube/v3/playlistItems"
            params = {
                "part": "snippet,contentDetails",
                "playlistId": self.yt_upload_playlist_id,
                "key": self.yt_api_key,
                "maxResults": 1,
                "order": "date",
            }

            response = await client.get(url, params=params)
            if response.status_code == 404:
                await self.delete()
                return None

            data = response.json()

            if "items" in data and len(data["items"]) > 0:
                video_id = data["items"][0]["snippet"]["resourceId"]["videoId"]
                published_at = datetime.fromisoformat(data["items"][0]["contentDetails"]["videoPublishedAt"]) + timedelta(
                    hours=5, minutes=30
                )
                if partial or self.yt_last_video_id == video_id:
                    return YtVideo(id=video_id, publishedAt=published_at)

                video = await self.fetch_video_by_id(video_id)
                if video:
                    return YtVideo(
                        id=video_id,
                        publishedAt=published_at,
                        title=video["snippet"]["title"],
                        live=video["snippet"]["liveBroadcastContent"] == "live",
                        channel_name=video["snippet"]["channelTitle"],
                    )

        return None

    async def get_uploads_playlist_id(self, channel_id: str) -> str:
        url = f"https://www.googleapis.com/youtube/v3/channels" f"?part=contentDetails" f"&id={channel_id}" f"&key={self.yt_api_key}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()
            # Extract the uploads playlist ID
            try:
                playlist_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
                return playlist_id
            except (IndexError, KeyError) as e:
                self.bot.logger.exception(f"Failed to retrieve uploads playlist ID: {e}")
                return None

    async def fetch_video_by_id(self, yt_video_id: str):
        async with httpx.AsyncClient() as client:
            url = f"https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "snippet",
                "id": yt_video_id,
                "key": self.yt_api_key,
                "maxResults": 1,
            }
            response = await client.get(url, params=params)

            data = response.json()

            logger.debug(f"Video details fetched for {yt_video_id}: {data}")

            if "items" in data and len(data["items"]) > 0:
                return data["items"][0]

        return None
