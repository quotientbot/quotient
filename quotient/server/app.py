import hashlib
import os

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from lib import get_current_time
from models import Guild, PremiumPlan, PremiumTxn, User

fastapi_app = FastAPI()
template = Jinja2Templates(directory="quotient/server/templates")


def create_hash(txnId: str, amount: str, productInfo: str, firstName: str, email: str):
    # sha512(key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5||||||salt)

    return hashlib.sha512(
        f"{os.getenv('PAYU_MERCHANT_KEY')}|{txnId}|{amount}|{productInfo}|{firstName}|{email}|||||||||||{os.getenv('PAYU_PAYMENT_SALT')}".encode(
            "utf-8"
        )
    ).hexdigest()


@fastapi_app.get("/")
async def get_premium(request: Request, txnId: str):
    record = await PremiumTxn.get_or_none(txnid=txnId)
    user = await User.get(pk=record.user_id)

    if not record:
        return {"error": "Invalid Transaction ID"}

    if record.completed_at:
        return {"error": "Transaction already completed"}

    plan = await PremiumPlan.get(pk=record.plan_id)

    payu_hash = create_hash(txnId, plan.price, "premium", record.user_id, user.email_id)

    data = {
        "key": os.getenv("PAYU_MERCHANT_KEY"),
        "txnid": txnId,
        "amount": plan.price,
        "productinfo": "premium",
        "firstname": record.user_id,
        "email": user.email_id,
        "surl": f"{os.getenv('PAYU_SUCCESS_URL')}{txnId}",
        "furl": f"{os.getenv('PAYU_FAILED_URL')}{txnId}",
        "phone": user.phone_number,
        "action": os.getenv("PAYU_PAYMENT_LINK"),
        "hash": payu_hash,
    }

    return template.TemplateResponse("payu.html", {"request": request, "posted": data})


@fastapi_app.post("/premium_success")
async def premium_success(request: Request, txnId: str):

    try:
        form = await request.form()
    except:
        return {"error": "Invalid Request."}

    if not "payu" in request.headers.get("origin"):
        return {"error": "Invalid Request Origin."}

    if not form.get("status") == "success":
        return {"error": f"Transaction Status: {form.get('status')}"}

    record = await PremiumTxn.get_or_none(txnid=txnId)
    if not record:
        return {"error": "Transaction Id is invalid."}

    if record.completed_at:
        return {"error": "Transaction is already complete."}

    await PremiumTxn.get(txnid=txnId).update(
        raw_data=dict(form), completed_at=get_current_time()
    )
    u, b = await User.get_or_create(user_id=record.user_id)
    plan = await PremiumPlan.get(pk=record.plan_id)

    from core.bot import BOT_INSTANCE

    BOT_INSTANCE.dispatch("premium_purchase", record.txnid)

    guild = await Guild.get(pk=record.guild_id)
    end_time = (
        guild.premium_end_time + plan.duration
        if guild.is_premium
        else get_current_time() + plan.duration
    )
    await Guild.get(pk=guild.pk).update(
        is_premium=True, premium_end_time=end_time, made_premium_by=u.user_id
    )

    return {"success": "Transaction was successful. Please return to discord App."}


@fastapi_app.post("/premium_failed")
async def premium_failed(request: Request, txnId: str):
    try:
        form = await request.form()
    except:
        return {"error": "Invalid Request."}

    if not "payu" in request.headers.get("origin"):
        return {"error": "Invalid Request Origin."}

    await PremiumTxn.get(txnid=txnId).update(
        completed_at=get_current_time(), raw_data=dict(form)
    )

    return {"error": "Transaction Cancelled."}
