import random


def random_greeting_msg() -> str:
    greetings = [
        "Hello, sunshine!",
        "Peek-a-boo!",
        "Howdy-doody!",
        "Ahoy, matey!",
        "Hiya!",
        "What's crackin'?",
        "Howdy, howdy ,howdy!",
        "Yo!",
        "I like your face.",
        "Bonjour!",
        "Yo! You know who this is.",
    ]
    return random.choice(greetings)


def random_thanks_image() -> str:
    msges = (
        "https://cdn.discordapp.com/attachments/877888851241238548/877890130478784532/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877890377426821140/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877890550399918122/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877891011349725194/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877891209421549628/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877891348869550100/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877891767058444359/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877891874671706162/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877892011720572988/unknown.png",
        "https://cdn.discordapp.com/attachments/829953427336593429/878898567509573652/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/881575840578695178/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/881576005498732625/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/881576299137761350/unknown.png",
        "https://cdn.discordapp.com/attachments/851846932593770496/886275684304044142/unknown.png",
    )
    return random.choice(msges)
