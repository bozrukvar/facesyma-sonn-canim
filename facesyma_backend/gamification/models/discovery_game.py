"""Discovery game models."""


class DiscoveryGameType:
    __slots__ = (
        "game_type_id", "name_en", "name_tr",
        "description_en", "description_tr",
        "game_mode", "duration_seconds",
        "coin_reward_win", "coin_reward_play",
        "learning_focus",
    )

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


DISCOVERY_GAME_TYPES = {
    "trait_discovery": DiscoveryGameType(
        game_type_id="trait_discovery",
        name_en="Trait Discovery",
        name_tr="Sıfat Keşfi",
        description_en="Discover which personality traits match your face",
        description_tr="Yüzüne hangi kişilik sıfatlarının uyduğunu keşfet",
        game_mode="trait_discovery",
        duration_seconds=60,
        coin_reward_win=30,
        coin_reward_play=10,
        learning_focus="personality",
    ),
    "sifat_learning": DiscoveryGameType(
        game_type_id="sifat_learning",
        name_en="Sıfat Learning",
        name_tr="Sıfat Öğrenme",
        description_en="Learn what personality traits mean through examples",
        description_tr="Kişilik sıfatlarının ne anlama geldiğini öğren",
        game_mode="sifat_learning",
        duration_seconds=90,
        coin_reward_win=20,
        coin_reward_play=8,
        learning_focus="vocabulary",
    ),
    "face_quiz": DiscoveryGameType(
        game_type_id="face_quiz",
        name_en="Face Quiz",
        name_tr="Yüz Testi",
        description_en="Match faces to personality traits",
        description_tr="Yüzleri kişilik sıfatlarıyla eşleştir",
        game_mode="face_quiz",
        duration_seconds=120,
        coin_reward_win=40,
        coin_reward_play=12,
        learning_focus="recognition",
    ),
}
