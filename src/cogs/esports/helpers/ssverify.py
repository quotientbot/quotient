# async def verify_image(record: SSVerify, group: Tuple):

#     img, cropped = group

#     _hash = str(await get_image_hash(img))

#     if _match := await record.find_hash(str(_hash)):
#         return VerifyResult(f"Already posted by {getattr(_match.author,'mention','Unknown')}.")

#     clean_text = ""

#     for _ in cropped:
#         clean_text += await get_image_string(img)

#     _text = clean_text.lower().replace(" ", "")

#     name = record.channel_name.lower().replace(" ", "")

#     if record.ss_type == SSType.yt:

#         if not any(_ in _text for _ in ("subscribe", "videos")):
#             return VerifyResult("Not a valid youtube screenshot.")

#         elif not name in _text:
#             return VerifyResult(f"Screenshot must belong to [`{record.channel_name}`]({record.channel_link}) channel.")

#         elif "SUBSCRIBE " in clean_text:
#             return VerifyResult(f"You must subscribe [`{record.channel_name}`]({record.channel_link}) to get verified.")

#     elif record.ss_type == SSType.insta:
#         if not "followers" in _text:
#             return VerifyResult("Not a valid instagram screenshot.")

#         elif not name in _text:
#             return VerifyResult(f"Screenshot must belong to [`{record.channel_name}`]({record.channel_link}) page.")

#         elif "Follow " in clean_text:
#             return VerifyResult("You must follow the page to get verified.")

#     return VerifyResult("Verified Successfully!", True, _hash)
