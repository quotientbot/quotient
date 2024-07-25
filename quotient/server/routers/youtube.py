import hashlib
import hmac
import logging
import os
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from models import YtNotification

router = APIRouter()
logger = logging.getLogger(os.getenv("INSTANCE_TYPE"))


@router.get("/notification/{record}")
async def verify_subscription(request: Request, record: YtNotification = Depends(YtNotification.get_record)):

    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    verify_token = request.query_params.get("hub.verify_token")

    # Check verify token if necessary
    if mode and challenge and verify_token == os.getenv("YT_SUBSCRIBE_REQ_TOKEN"):
        return Response(content=challenge, media_type="text/plain")

    return Response(content="Verification Failed", status_code=400)


@router.post("/notification/{record}")
async def handle_notification(request: Request, record: YtNotification = Depends(YtNotification.get_record)):

    signature = request.headers.get("X-Hub-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Signature is Missing")

    body = await request.body()
    secret = os.getenv("YT_NOTIFICATION_TOKEN")

    if not secret:
        raise HTTPException(status_code=500, detail="Internal Server Error, YT Secret is Missing.")

    # Compute the expected signature
    expected_signature = hmac.new(secret.encode(), body, hashlib.sha1).hexdigest()

    # Compare the received signature with the expected one
    if not hmac.compare_digest(signature.split("=")[1], expected_signature):
        raise HTTPException(status_code=400, detail="Invalid Signature")

    # Process the notification
    feed = ET.fromstring(body)
    entries = feed.findall("{http://www.w3.org/2005/Atom}entry")

    for entry in entries:
        title = entry.find("{http://www.w3.org/2005/Atom}title").text
        link = entry.find("{http://www.w3.org/2005/Atom}link").attrib["href"]

        video_id = link.split("v=")[-1]  # Extracting video ID from the link
        published = entry.find("{http://www.w3.org/2005/Atom}published").text
        updated = entry.find("{http://www.w3.org/2005/Atom}updated").text

        author = entry.find("{http://www.w3.org/2005/Atom}author")
        author_name = author.find("{http://www.w3.org/2005/Atom}name").text
        author_uri = author.find("{http://www.w3.org/2005/Atom}uri").text

        channel_id = author_uri.split("/")[-1]  # Extracting channel ID from the author URI

        description = (
            entry.find("{http://www.w3.org/2005/Atom}summary").text
            if entry.find("{http://www.w3.org/2005/Atom}summary") is not None
            else ""
        )

        video_details = await YtNotification.get_video_by_id(video_id)
        logger.debug(f"Retrived details of video: {video_id} => {video_details}")
        if not video_details:
            return

        video_published_at = datetime.fromisoformat(video_details["snippet"]["publishedAt"])
        if not (datetime.now(UTC) - video_published_at) <= timedelta(minutes=1):
            logger.debug(f"Video: {video_id} is old, Returning")
            return  # The is probably an old video , which was edited just now.

        yt_element = {
            "title": title,
            "url": link,
            "video_id": video_id,
            "published": published,
            "updated": updated,
            "author_name": author_name,
            "author_uri": author_uri,
            "channel_id": channel_id,
            "description": description,
            "video_type": "regular" if video_details["snippet"]["liveBroadcastContent"] == "none" else "live",
        }

        await record.send_notification(author_name, title, link)

    return Response(content="Notification received", status_code=200)
