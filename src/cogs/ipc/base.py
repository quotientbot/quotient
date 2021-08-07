from core import Cog


class IpcCog(Cog):
    positive = {"ok": True, "result": {}, "error": None}

    @staticmethod
    def deny_request(reason):
        return {"ok": False, "result": {}, "error": reason}

    @property
    def not_guild(self):
        return self.deny_request("Quotient have been removed from the server. Kindly add it back and try again.")

    @property
    def not_member(self):
        return self.deny_request("You actually need to be in the server to use dashboard.")

    @property
    def not_manage_guild(self):
        return self.deny_request("You need Manage Server permissions to use dashboard.")

    @staticmethod
    def check_if_mod(role):
        _list = [
            k
            for k, v in dict(role.permissions).items()
            if v is True
            and k
            in ("manage_channels", "manage_guild", "manage_messages", "manage_roles", "administrator", "manage_emojis")
        ]
        if _list:
            return _list

        else:
            return True
