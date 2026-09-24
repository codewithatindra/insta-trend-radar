"""Starter seed hashtags per niche. Pass your own with --hashtags or in config.yaml.

Keep the list short: the Instagram API lets one account query at most 30 unique
hashtags in a rolling 7-day window.
"""

PRESETS: dict[str, list[str]] = {
    "fashion": ["fashion", "ootd", "streetstyle", "outfitinspo", "indianfashion"],
    "cricket": ["cricket", "teamindia", "ipl", "bcci", "indiancricket"],
    "bollywood": ["bollywood", "tollywood", "kollywood", "desimemes", "filmy"],
    "festivals": ["diwali", "navratri", "durgapuja", "chhathpuja", "festivevibes"],
    "startups": ["startupindia", "indianstartup", "founder", "d2c", "sharktankindia"],
    "finance": ["stockmarketindia", "nifty", "sensex", "personalfinance", "upi"],
    "travel": ["travel", "travelgram", "wanderlust", "incredibleindia", "solotravel"],
    "fitness": ["fitness", "gymmotivation", "homeworkout", "fitindia", "yoga"],
    "food": ["foodie", "foodporn", "indianfood", "streetfood", "homecooking"],
    "tech": ["tech", "gadgets", "ai", "startup", "coding"],
    "beauty": ["makeup", "skincare", "beautytips", "grwm", "indianbeauty"],
}


def seeds_for(niche: str, extra: list[str] | None = None) -> list[str]:
    tags = list(PRESETS.get(niche.lower(), [niche.lower().replace(" ", "")]))
    for t in extra or []:
        t = t.lstrip("#").lower()
        if t and t not in tags:
            tags.append(t)
    return tags[:30]


# Words used to match India Pulse topics (Google/YouTube) to a niche. Lowercase substrings,
# English + common Hindi/Hinglish. Add your own with india_keywords in config.yaml.
KEYWORDS: dict[str, list[str]] = {
    "cricket": ["cricket", "ipl", "bcci", "t20", "odi", "test match", "kohli", "rohit", "bumrah",
                "cricbuzz", "espncricinfo", "wicket", "क्रिकेट"],
    "bollywood": ["bollywood", "tollywood", "kollywood", "movie", "film", "trailer", "box office",
                  "ott", "netflix", "prime video", "song", "फिल्म", "entertainment", "review"],
    "festivals": ["diwali", "navratri", "durga", "chhath", "holi", "eid", "ganesh", "dussehra",
                  "raksha", "onam", "pongal", "karwa", "puja", "त्योहार", "दिवाली"],
    "startups": ["startup", "founder", "funding", "ipo", "unicorn", "d2c", "shark tank", "layoff",
                 "zepto", "swiggy", "zomato", "flipkart", "ola", "paytm"],
    "finance": ["sensex", "nifty", "bse", "nse", "ipo", "rbi", "gst", "upi", "gold price", "stock",
                "share price", "income tax", "mutual fund", "शेयर"],
    "travel": ["travel", "flight", "airline", "indigo", "air india", "irctc", "train", "railway",
               "tatkal", "airport", "visa", "tourism", "hotel", "fastag", "यात्रा"],
    "food": ["food", "recipe", "restaurant", "swiggy", "zomato", "chef", "biryani", "street food"],
    "fashion": ["fashion", "saree", "lehenga", "outfit", "style", "myntra", "ajio", "met gala"],
    "beauty": ["beauty", "skincare", "makeup", "nykaa", "hair", "lipstick"],
    "fitness": ["fitness", "gym", "yoga", "workout", "marathon", "diet", "health"],
    "tech": ["iphone", "apple", "samsung", "android", "ai", "chatgpt", "jio", "airtel", "5g",
             "launch", "smartphone", "science technology", "gaming"],
    "news": ["news politics", "weather", "mausam", "rain", "cyclone", "election", "मौसम", "बारिश"],
}


def keywords_for(niche: str, extra: list[str] | None = None) -> list[str]:
    words = list(KEYWORDS.get(niche.lower(), [niche.lower()]))
    return words + [w.lower() for w in extra or [] if w]
