from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from quotient.core import Quotient

import asyncio

import websockets
from discord.ext import commands


class WebSocketClient(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.ws_url = "ws://quotient:6000/ws"

        self.websocket: websockets.WebSocketClientProtocol = None
        self.max_retries = 5
        self.retry_count = 0
        self.backoff = 1

        self.connect_ws_task = self.bot.loop.create_task(self.connect_ws())

    async def connect_ws(self):
        while True:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    self.websocket = websocket
                    self.bot.logger.info(f"Connected to WebSocket server at {self.ws_url}")
                    self.retry_count = 0
                    self.backoff = 1
                    await self.receive_messages()
            except Exception as e:
                self.bot.logger.error(f"Failed to connect to WebSocket server: {e}")
                self.retry_count += 1
                if self.retry_count >= self.max_retries:
                    self.bot.logger.error("Max retries reached, stopping reconnection attempts.")
                    break
                self.bot.logger.info(f"Retrying connection in {self.backoff} seconds...")
                await asyncio.sleep(self.backoff)
                self.backoff = min(self.backoff * 2, 60)  # Exponential backoff up to 60 seconds

    async def receive_messages(self):
        try:
            async for message in self.websocket:
                self.bot.logger.info(f"Received message: {message}")
        except websockets.exceptions.ConnectionClosed as e:
            self.bot.logger.warning(f"WebSocket connection closed: {e}")
        except Exception as e:
            self.bot.logger.error(f"WebSocket error: {e}")
        finally:
            self.websocket = None
            self.bot.logger.info("WebSocket connection lost, attempting to reconnect...")
            self.connect_ws_task = self.bot.loop.create_task(self.connect_ws())

    def cog_unload(self):
        if self.connect_ws_task:
            self.connect_ws_task.cancel()


async def setup(bot: Quotient):
    await bot.add_cog(WebSocketClient(bot))
