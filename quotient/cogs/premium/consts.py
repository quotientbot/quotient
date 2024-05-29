from lib import TICK

PRO_FEATURES = [
    "Access to `Quotient Pro` bot.",
    "Unlimited Scrims.",
    "Unlimited Tournaments.",
    "Custom Reactions for Regs.",
    "Smart SSverification.",
    "Cancel-Claim Panel.",
    "Premium Role + more...",
]


def get_pro_features_formatted() -> str:
    return "\n".join([f"{TICK} {feature}" for feature in PRO_FEATURES])
