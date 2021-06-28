from contextlib import suppress
from discord import Webhook, AsyncWebhookAdapter
from cogs.fun.helper import deliver_webhook
from utils import IST
from constants import EventType
from core import Cog, Quotient
from models import Autoevent
from discord.ext import tasks
import itertools
import discord
import json
from datetime import datetime
from aiohttp import ContentTypeError

__all__ = ("Funevents",)


class Funevents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.autoevent_dispatcher.start()

    def cog_unload(self):
        self.autoevent_dispatcher.cancel()

    async def request_json(self, uri, **kwargs):
        resp = await self.bot.session.get(uri, **kwargs)
        try:
            return await resp.json()
        except (json.JSONDecodeError, ContentTypeError) as e:
            print(f"Something wrong happened: {e}")

    async def handle_event(self, _type, records):
        if _type == EventType.meme:
            URL = "https://api.ksoft.si/images/random-meme"
            data = await self.request_json(URL, headers={"Authorization": self.bot.config.KSOFT_TOKEN})
            embed = discord.Embed(color=self.bot.color, url=data["source"], title=data["title"])
            embed.set_image(url=data["image_url"])
            embed.set_footer(text="👍 {} | 💬 {}".format(data["upvotes"], data["comments"]))

        elif _type == EventType.fact:
            URL = "https://happy-meme-a.glitch.me/fact"
            data = await self.request_json(URL)
            embed = discord.Embed(color=self.bot.color, title=f"{data['fact']}")
            embed.set_footer(text=self.bot.config.FOOTER, icon_url=self.bot.user.avatar_url)

        elif _type == EventType.quote:
            URL = "https://api.quotable.io/random"
            data = await self.request_json(URL)
            embed = discord.Embed(color=self.bot.color, title=f"{data['content']}")
            embed.set_footer(text=self.bot.config.FOOTER, icon_url=self.bot.user.avatar_url)
            embed.set_author(name=f"Author: {data['author']}")

        elif _type == EventType.joke:
            URL = "https://official-joke-api.appspot.com/random_joke"
            data = await self.request_json(URL)
            embed = discord.Embed(color=self.bot.color)
            embed.description = f"**`Setup:`** {data['setup']}\n**`Punchline:`** ||{data['punchline']}||"
            embed.set_footer(text=self.bot.config.FOOTER, icon_url=self.bot.user.avatar_url)

        elif _type == EventType.nsfw:
            URL = "https://api.ksoft.si/images/random-nsfw"
            data = await self.request_json(URL, headers={"Authorization": self.bot.config.KSOFT_TOKEN})

            embed = discord.Embed(color=self.bot.color, url=data["source"], title=data["title"])
            embed.set_image(url=data["image_url"])
            embed.set_footer(text="👍 {} | 💬 {}".format(data["upvotes"], data["comments"]))

        elif _type == EventType.advice:
            res = await self.bot.session.get("https://api.adviceslip.com/advice", headers={"Accept": "application/json"})
            data = await res.json(content_type="text/html")

            embed = discord.Embed(color=self.bot.color, title=f"{data['slip']['advice']}")
            embed.set_footer(text=self.bot.config.FOOTER, icon_url=self.bot.user.avatar_url)

        elif _type == EventType.poem:
            URL = "https://www.poemist.com/api/v1/randompoems"
            data = await self.request_json(URL)
            if data[0]["content"] is None:
                return

            if not len(data[0]["content"]) > 2000:
                poem = data[0]["content"]
            else:
                post = await self.bot.binclient.post(data[0]["content"])
                poem = post.url

            embed = discord.Embed(color=self.bot.color, title=f"Title: {data[0]['title']}", description=poem)
            embed.set_author(name=f"Author: {data[0]['poet']['name']}", url=data[0]["poet"]["url"])

            embed.set_footer(text=self.bot.config.FOOTER, icon_url=self.bot.user.avatar_url)

        else:
            return print("Unhandled Type...", _type)

        if len(records):
            for record in records:
                webhook = Webhook.from_url(record.webhook, adapter=AsyncWebhookAdapter(self.bot.session))
                self.bot.loop.create_task(deliver_webhook(webhook, embed, _type, self.bot.user.avatar_url))

    @tasks.loop(seconds=60)
    async def autoevent_dispatcher(self):
        current_time = datetime.now(tz=IST)
        records = await Autoevent.all().filter(webhook__isnull=False, send_time__lte=current_time, toggle=True)
        if not len(records):
            return

        for key, group in itertools.groupby(records, key=lambda rec: rec.type):
            self.bot.loop.create_task(self.handle_event(key, list(group)))

        to_update = [record.id for record in records]  # apparently we can't use a generator here :c
        # now , can tortoise-orm do this?
        await self.bot.db.execute(
            "UPDATE autoevents set send_time = autoevents.send_time + autoevents.interval * interval '1 minute' where autoevents.id = any($1::bigint[])",
            to_update,
        )

    @autoevent_dispatcher.before_loop
    async def before_autoevent_dispatcher(self):
        await self.bot.wait_until_ready()
