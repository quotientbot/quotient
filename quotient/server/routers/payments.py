import hashlib
import os
from datetime import datetime
from urllib.parse import parse_qs

from discord.utils import format_dt
from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, Request
from fastapi.templating import Jinja2Templates
from humanize import naturaldelta
from pytz import timezone

from quotient.models import Guild, PremiumQueue, PremiumTxn, User

router = APIRouter(prefix="/payment", tags=["payments"])
template = Jinja2Templates(directory="quotient/server/templates")


def create_payu_hash(
    txnid: str,
    amount: float,
    productinfo: str,
    firstname: str,
    email: str,
    status: str = "",
    reverse: bool = False,
):
    """
    Create secure hash for the validation of the payment.
    sha512(key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5||||||salt)
    or in reverse order sha512(salt|status||||||udf5|udf4|udf3|udf2|udf1|email|firstname|productinfo|amount|txnid|key)
    """
    key = os.getenv("PAYU_MERCHANT_KEY")
    salt = os.getenv("PAYU_PAYMENT_SALT")
    amount_str = f"{amount:.2f}"  # Format amount to 2 decimal places

    if reverse:
        # Construct the string to hash in reverse order
        hash_string = f"{salt}|{status}|||||||||||{email}|{firstname}|{productinfo}|{amount_str}|{txnid}|{key}"
    else:
        # Construct the string to hash in normal order
        hash_string = f"{key}|{txnid}|{amount_str}|{productinfo}|{firstname}|{email}|||||||||||{salt}"

    # Create the SHA-512 hash
    return hashlib.sha512(hash_string.encode("utf-8")).hexdigest()


@router.get("/")
async def redirect_to_payment_page(request: Request, txnId: str):
    """
    Validates the transaction ID and redirects to the final payment page.
    """
    record = await PremiumTxn.get_or_none(txnid=txnId)

    if not record:
        return {"error": "Invalid Transaction ID"}

    user = await User.get(pk=record.user_id)

    if record.completed_at:
        return {"error": "Transaction already completed :)"}

    productInfo = f"Quotient Pro - {record.tier.name} {naturaldelta(record.premium_duration)}".strip()

    txn_hash = create_payu_hash(txnId, record.amount, productInfo, str(record.user_id), user.email_id)
    data = {
        "key": os.getenv("PAYU_MERCHANT_KEY"),
        "txnid": txnId,
        "amount": f"{record.amount:.2f}",
        "productinfo": productInfo,
        "firstname": record.user_id,
        "email": user.email_id,
        "surl": f"{os.getenv('PAYU_SUCCESS_URL')}{txnId}",
        "furl": f"{os.getenv('PAYU_FAILED_URL')}{txnId}",
        "phone": "+91-9999999999",  # Dummy Phone Number
        "action": os.getenv("PAYU_PAYMENT_LINK"),
        "hash": txn_hash,
    }

    return template.TemplateResponse("payu.html", {"request": request, "posted": data})


async def add_premium_to_guild(txn_details: PremiumTxn):
    g = await Guild.get(pk=txn_details.guild_id)
    if not g.is_premium:
        g.tier = txn_details.tier
        g.upgraded_by = txn_details.user_id
        g.upgraded_until = txn_details.completed_at + txn_details.premium_duration
        await g.save(update_fields=["tier", "upgraded_by", "upgraded_until"])
        await g.copy_premium_to_pro()

    else:
        q = await PremiumQueue.create(txn=txn_details, guild_id=txn_details.guild_id)
        await q.copy_premium_to_pro()

    g.bot.dispatch("premium_purchase", txn_details)


async def log_txn(txn_details: PremiumTxn):
    t = (
        f"**({txn_details.raw_data['status'][0].title()}) Transaction on Payu!**\n\n"
        f"**User:** <@{txn_details.user_id}> `[{txn_details.user_id}]`\n"
        f"**Guild:** `{txn_details.guild_id}`\n"
        f"**Tier:** `{txn_details.tier.name}`\n"
        f"**Amount:** `{txn_details.amount} ({txn_details.currency.name})`\n"
        f"**Duration:** `{naturaldelta(txn_details.premium_duration)}`\n"
        f"**Completed At:** {format_dt(txn_details.completed_at)}\n"
    )

    await txn_details.bot.logs_webhook.send(t, username="PayU Txn", avatar_url=txn_details.bot.user.display_avatar.url)


@router.post("/hook/status")
async def payu_payment_status_webhook(background_tasks: BackgroundTasks, body: bytes = Body(...)):
    """
    Receives the payment status webhook from PayU and updates the payment transaction accordingly.
    """
    try:
        parsed_body = parse_qs(body.decode("utf-8"))  # Parse the URL-encoded string
    except Exception as e:
        raise HTTPException(status_code=400, detail="Bad Request")

    try:
        txnid = parsed_body["txnid"][0]
        txnhash = parsed_body["hash"][0]
        amount = float(parsed_body["amount"][0])
        productinfo = parsed_body["productinfo"][0]
        firstname = parsed_body["firstname"][0]
        email = parsed_body["email"][0]
        status = parsed_body.get("status", [""])[0]
        addedon = datetime.fromisoformat(parsed_body["addedon"][0])
    except (KeyError, IndexError, ValueError):
        raise HTTPException(status_code=400, detail="Bad Request")

    # Recreate the hash
    recreated_hash = create_payu_hash(txnid, amount, productinfo, firstname, email, status, reverse=True)

    # Verify the hash
    if recreated_hash != txnhash:
        raise HTTPException(status_code=400, detail="Invalid payment hash, transaction couldn't be verified.")

    record = await PremiumTxn.get_or_none(txnid=txnid)
    if not record:
        return {"error": "Invalid Transaction ID"}

    if record.raw_data and record.raw_data.get("status") == ["success"]:  # duplicate webhook
        return {"error": "Transaction already completed."}

    record.completed_at = timezone("Asia/Kolkata").localize(addedon)
    record.raw_data = parsed_body

    background_tasks.add_task(log_txn, record)
    await record.save(update_fields=["completed_at", "raw_data"])

    if not status == "success":
        return {"ok": "Valid but Failed Txn."}

    background_tasks.add_task(add_premium_to_guild, record)

    return {"success": "ok"}


@router.post("/success")
async def premium_success(request: Request, txnId: str):
    try:
        form = await request.form()
    except:
        raise HTTPException(status_code=400, detail="Bad Request")

    if not "payu" in request.headers.get("origin"):
        raise HTTPException(status_code=400, detail="Bad Request")

    return template.TemplateResponse("response.html", {"request": request, "success": True})


@router.post("/failed")
async def premium_failed(request: Request, txnId: str):
    try:
        form = await request.form()
    except:
        raise HTTPException(status_code=400, detail="Bad Request")

    if not "payu" in request.headers.get("origin"):
        raise HTTPException(status_code=400, detail="Bad Request")

    return template.TemplateResponse("response.html", {"request": request, "success": False})
