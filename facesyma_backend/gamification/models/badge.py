"""Badge models."""


class BadgeTier:
    __slots__ = ("tier", "level", "threshold")

    def __init__(self, tier, level, threshold):
        self.tier = tier
        self.level = level
        self.threshold = threshold


class BadgeDefinition:
    __slots__ = (
        "badge_id", "name_en", "name_tr",
        "description_en", "description_tr",
        "game_type", "category",
        "icon_url", "unlock_condition",
        "tiers", "coin_reward_per_tier",
    )

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


def _tiers(thresholds):
    names = ["bronze", "silver", "gold", "platinum"]
    return [BadgeTier(n, i + 1, t) for i, (n, t) in enumerate(zip(names, thresholds))]


BADGE_DEFINITIONS = {
    "meal_adventurous_eater": BadgeDefinition(
        badge_id="meal_adventurous_eater",
        name_en="Adventurous Eater",
        name_tr="Macera Arayıcı Yiyici",
        description_en="Select meals from different countries",
        description_tr="Farklı ülkelerden yemek seç",
        game_type="meal",
        category="exploration",
        icon_url=None,
        unlock_condition="count",
        tiers=_tiers([10, 25, 50, 100]),
        coin_reward_per_tier=10,
    ),
    "challenge_champion": BadgeDefinition(
        badge_id="challenge_champion",
        name_en="Challenge Champion",
        name_tr="Meydan Okuma Şampiyonu",
        description_en="Win social challenges",
        description_tr="Sosyal meydan okumaları kazan",
        game_type="challenge",
        category="competition",
        icon_url=None,
        unlock_condition="wins",
        tiers=_tiers([1, 5, 20, 50]),
        coin_reward_per_tier=20,
    ),
    "discovery_master": BadgeDefinition(
        badge_id="discovery_master",
        name_en="Discovery Master",
        name_tr="Keşif Ustası",
        description_en="Complete discovery game sessions",
        description_tr="Keşif oyunu oturumlarını tamamla",
        game_type="discovery",
        category="knowledge",
        icon_url=None,
        unlock_condition="sessions",
        tiers=_tiers([5, 15, 40, 100]),
        coin_reward_per_tier=15,
    ),
    "streak_keeper": BadgeDefinition(
        badge_id="streak_keeper",
        name_en="Streak Keeper",
        name_tr="Seri Koruyucu",
        description_en="Maintain daily login streaks",
        description_tr="Günlük giriş serilerini koru",
        game_type="coin",
        category="consistency",
        icon_url=None,
        unlock_condition="streak_days",
        tiers=_tiers([7, 14, 30, 100]),
        coin_reward_per_tier=10,
    ),
    "mission_hero": BadgeDefinition(
        badge_id="mission_hero",
        name_en="Mission Hero",
        name_tr="Görev Kahramanı",
        description_en="Contribute to community missions",
        description_tr="Topluluk görevlerine katkıda bulun",
        game_type="mission",
        category="community",
        icon_url=None,
        unlock_condition="contributions",
        tiers=_tiers([3, 10, 30, 75]),
        coin_reward_per_tier=12,
    ),
}
