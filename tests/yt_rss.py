import asyncio

import httpx


async def get_uploads_playlist_id(api_key: str, channel_id: str) -> str:
    url = f"https://www.googleapis.com/youtube/v3/channels" f"?part=contentDetails" f"&id={channel_id}" f"&key={api_key}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        # Extract the uploads playlist ID
        try:
            print("yt_channel playlistss")
            print(data)
            playlist_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            return playlist_id
        except (IndexError, KeyError) as e:
            print(f"Failed to retrieve uploads playlist ID: {e}")
            return None


async def get_youtube_playlist_items(api_key: str, playlist_id: str):
    url = (
        f"https://www.googleapis.com/youtube/v3/playlistItems"
        f"?part=snippet,contentDetails,status"
        f"&playlistId={playlist_id}"
        f"&maxResults=1"
        f"&order=date"
        f"&key={api_key}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()


async def main():
    api_key = ""
    channel_id = ""

    # Get the uploads playlist ID
    playlist_id = await get_uploads_playlist_id(api_key, channel_id)
    if playlist_id:
        print(f"Uploads Playlist ID: {playlist_id}")
        # Get the playlist items
        data = await get_youtube_playlist_items(api_key, playlist_id)
        print(data)
    else:
        print("Failed to get playlist ID")


asyncio.run(main())
