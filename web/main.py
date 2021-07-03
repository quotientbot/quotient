from discord.ext.ipc import Client
from quart import Quart, request, jsonify


app = Quart(__name__)
web_ipc = Client(secret_key="some-key")


@app.route("/")
async def index():
    member_count = await web_ipc.request("get_member_count", guild_id=746337818388987967)
    return {"hello": "world", "Members": member_count}


@app.route("/scrim/create")
async def create_Scrim():
    payload = request.args.get("payload")
    if not payload:
        return jsonify({"fuck": "you"})

    else:
        res = await web_ipc.request("create_Scrim", payload=payload)
        return res


if __name__ == "__main__":
    app.run(debug=True)
