class _Sentinel(object):
    def __repr__(self) -> str:
        return "<MISSING>"

MISSING = _Sentinel()