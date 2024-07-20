from lib import TICK

PRO_FEATURES = [
    "Access to `Quotient Pro` bot.",
    "Unlimited Scrims.",
    "Unlimited Tournaments.",
    "Custom Reactions for Regs.",
    "Smart SSverification.",
    "Cancel-Claim Panel.",
    "Unlimited AutoPurge Channels.",
    "Premium Role + more...",
]


def get_pro_features_formatted() -> str:
    return "\n".join([f"{TICK} {feature}" for feature in PRO_FEATURES])


# Free Tier Limits
AUTOPURGE_LIMIT = 2
SCRIMS_LIMIT = 2
TOURNEY_LIMIT = 1
SLOTM_PANEL = 1
TAGCHECK_LIMIT = 1
