def deny_request(reason):
    return {"ok": False, "result": {}, "error": reason}


positive = {"ok": True, "result": {}, "error": None}


def not_guild(self):
    return self.deny_request("Quotient have been removed from the server. Kindly add it back and try again.")
