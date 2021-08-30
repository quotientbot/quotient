# @Cog.listener(name="on_message")
# async def on_ssverify_message(self, message: discord.Message):
#     if not message.guild or message.author.bot:
#         return

#     if not message.channel.id in self.bot.ssverify_channels:
#         return

#     verify = await SSVerify.get_or_none(msg_channel_id=message.channel.id)

#     if not verify:
#         return self.bot.ssverify_channels.discard(message.channel.id)

#     if not verify.sstoggle:
#         return

#     delete_after = verify.delete_after if verify.delete_after else None

#     if verify.mod_role_id in (role.id for role in message.author.roles):
#         return

#     records = await verify.data.filter(author_id=message.author.id)
#     approved = sum(1 for i in records if i.status == SSStatus.approved)
#     disapproved = sum(1 for i in records if i.status == SSStatus.disapproved)

#     if delete_after:
#         self.bot.loop.create_task(delete_denied_message(message, delete_after))

#     if approved >= verify.required_ss:
#         return await message.reply(
#             delete_after=delete_after,
#             embed=discord.Embed(
#                 color=discord.Color.green(),
#                 description=(
#                     f"**Your entry has already been confirmed, Kindly do not post more screenshots/messages here.**\n"
#                     f"`Message:` {verify.success_message}"
#                 ),
#             ),
#         )
#     attachments = [i for i in message.attachments if i.content_type in ("image/png", "image/jpeg", "image/jpg")]
#     if not attachments:
#         return await message.reply(
#             delete_after=delete_after,
#             embed=discord.Embed(
#                 color=discord.Color.red(),
#                 description=(
#                     f"Kindly send a valid screenshot {verify.ss_type.value} to send for verification.\n"
#                     "**Your history:**\n"
#                     f"\n- `{approved}` approved screenshots."
#                     f"\n- `{disapproved}` disapproved screenshots."
#                     f"\n\nYou need a total of {verify.required_ss} approved screenshots."
#                 ),
#             ),
#         )
#     ctx = await self.bot.get_context(message)

#     url = IPC_BASE + "/image/verify"
#     headers = {"Content-Type": "application/json"}

#     count = len(attachments)
#     for attachment in attachments:
#         payload = json.dumps({"type": verify.ss_type.name, "name": verify.channel_name, "url": attachment.proxy_url})

#         res = await self.bot.session.post(url=url, headers=headers, data=payload)
#         res = await res.json()

#         status = SSStatus.disapproved
#         if not res.get("ok"):

#             _error = res.get("error")
#             if VerifyImageError(_error) == VerifyImageError.Invalid:
#                 await message.reply(
#                     f"This doesn't seem to be a valid screenshot.\n"
#                     "\nYou need a screenshot of the following account:\n"
#                     f"<{verify.channel_link}>",
#                     delete_after=delete_after,
#                 )

#             elif VerifyImageError(_error) == VerifyImageError.NotSame:
#                 await message.reply(
#                     f"This screenshot doesn't belong to **{verify.channel_name}**\n\n"
#                     "You need a screenshot of the following account:\n"
#                     f"<{verify.channel_link}>",
#                     delete_after=delete_after,
#                 )

#             elif VerifyImageError(_error) == VerifyImageError.NoFollow:
#                 await message.reply(
#                     f"You need to send a screenshot where you have actually followed/subscribed **{verify.channel_name}**",
#                     delete_after=delete_after,
#                 )

#         else:
#             hashes = [i.hash for i in await verify.data.all()]
#             if not hashes:
#                 status = SSStatus.approved

#             elif (current_hash := res.get("hash")) in hashes:
#                 await message.reply("You cannot copy/repeat same screenshots.", delete_after=delete_after)

#             else:
#                 url = IPC_BASE + "/image/match"
#                 payload = json.dumps({"hash": current_hash, "iterable": hashes, "distance": "5"})

#                 newres = await self.bot.session.post(url=url, headers=headers, data=payload)

#                 newres = await newres.json()
#                 if newres.get("matches"):
#                     await message.reply(
#                         "Your screenshot seem to be a duplicate of previously posted images.",
#                         delete_after=delete_after,
#                     )

#                 else:
#                     status = SSStatus.approved

#         slot = await SSData.create(
#             author_id=message.author.id,
#             channel_id=message.channel.id,
#             message_id=message.id,
#             hash=res.get("hash"),
#             status=status,
#         )
#         await verify.data.add(slot)

#         if count > 1 and slot.status == SSStatus.approved:
#             await message.reply(f"{emote.check} | {attachment.filename} Verified.", delete_after=delete_after)

#     records = await verify.data.filter(author_id=message.author.id)
#     approved = sum(1 for i in records if i.status == SSStatus.approved)
#     disapproved = sum(1 for i in records if i.status == SSStatus.disapproved)

#     if approved >= verify.required_ss:
#         try:
#             await message.author.add_roles(discord.Object(id=verify.role_id))
#         except:
#             pass

#         return await message.reply(
#             embed=discord.Embed(
#                 color=discord.Color.green(),
#                 description=(
#                     f"Your entry has been confirmed, You don't need to post more screenshots/messages here.\n"
#                     f"{'**Message:** '+verify.success_message}"
#                 ),
#                 delete_after=delete_after,
#             )
#         )
#     return await message.reply(
#         delete_after=delete_after,
#         embed=discord.Embed(
#             color=self.bot.color,
#             description=(
#                 f"**Your history:**\n"
#                 f"\n- `{approved}` approved screenshots."
#                 f"\n- `{disapproved}` disapproved screenshots."
#                 f"\n\nYou need a total of {verify.required_ss} approved screenshots."
#             ),
#         ),
#     )
