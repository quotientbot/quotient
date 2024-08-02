import asyncio
import hashlib
import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv("quotient-main.env")


async def generate_upi_qr():
    uri = "https://info.payu.in/merchant/postservice.php"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    var1 = {
        "transactionId": "TEST_DBQR1981",
        "transactionAmount": "1.00",
    }

    var1_json = json.dumps(var1)

    hash_str = f"{os.getenv('PAYU_MERCHANT_KEY')}|generate_dynamic_bharat_qr|{var1_json}|{os.getenv('PAYU_PAYMENT_SALT')}"

    payload = {
        "command": "generate_dynamic_bharat_qr",
        "key": os.getenv("PAYU_MERCHANT_KEY"),
        "hash": hashlib.sha512(hash_str.encode("utf-8")).hexdigest(),
        "var1": var1_json,
    }

    print(payload["hash"])

    async with httpx.AsyncClient() as client:
        response = await client.post(uri, data=payload, headers=headers)
        print(response.text.encode("utf-8"))


asyncio.run(generate_upi_qr())
