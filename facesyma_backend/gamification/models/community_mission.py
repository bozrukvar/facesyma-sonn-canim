"""Community mission models."""


class MissionType:
    __slots__ = (
        "mission_type_id", "name_en", "name_tr",
        "description_en", "description_tr",
        "category", "duration_days",
        "target_value", "unit",
        "coin_reward_per_person", "difficulty",
    )

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


MISSION_TYPES = {
    "community_goal": MissionType(
        mission_type_id="community_goal",
        name_en="Community Goal",
        name_tr="Topluluk Hedefi",
        description_en="Work together to reach a shared target",
        description_tr="Ortak bir hedefe birlikte ulaşın",
        category="collaboration",
        duration_days=7,
        target_value=1000,
        unit="meals",
        coin_reward_per_person=25,
        difficulty="medium",
    ),
    "charity_mission": MissionType(
        mission_type_id="charity_mission",
        name_en="Charity Mission",
        name_tr="Hayır Görevi",
        description_en="Complete challenges to contribute to a charity cause",
        description_tr="Hayır amaçlı bir davaya katkıda bulunmak için görevleri tamamla",
        category="social",
        duration_days=14,
        target_value=5000,
        unit="points",
        coin_reward_per_person=50,
        difficulty="hard",
    ),
    "seasonal_event": MissionType(
        mission_type_id="seasonal_event",
        name_en="Seasonal Event",
        name_tr="Sezonluk Etkinlik",
        description_en="Special limited-time community events",
        description_tr="Özel süreli topluluk etkinlikleri",
        category="event",
        duration_days=3,
        target_value=500,
        unit="activities",
        coin_reward_per_person=75,
        difficulty="easy",
    ),
}
