"""Starter seed hashtags per niche. Pass your own with --hashtags or in config.yaml.

Keep the list short: the Instagram API lets one account query at most 30 unique
hashtags in a rolling 7-day window.
"""

PRESETS: dict[str, list[str]] = {
    "fashion": ["fashion", "ootd", "streetstyle", "outfitinspo", "indianfashion"],
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
