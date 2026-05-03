"""Challenge models."""
from typing import Optional


class ChallengeType:
    __slots__ = (
        "type_id", "name_en", "name_tr",
        "description_en", "description_tr",
        "category", "duration_minutes",
        "coin_reward_base", "leaderboard_metric",
    )

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


CHALLENGE_TYPES = {
    "meal_selection": ChallengeType(
        type_id="meal_selection",
        name_en="Meal Selection Challenge",
        name_tr="Yemek Seçim Yarışması",
        description_en="Select the most meals in a day",
        description_tr="Bir gün içinde en çok yemek seç",
        category="social",
        duration_minutes=1440,
        coin_reward_base=50,
        leaderboard_metric="meals_selected",
    ),
    "badge_race": ChallengeType(
        type_id="badge_race",
        name_en="Badge Race",
        name_tr="Rozet Yarışı",
        description_en="Earn the most badges in a week",
        description_tr="Bir haftada en çok rozet kazan",
        category="achievement",
        duration_minutes=10080,
        coin_reward_base=100,
        leaderboard_metric="badges_earned",
    ),
    "trait_dominance": ChallengeType(
        type_id="trait_dominance",
        name_en="Trait Dominance",
        name_tr="Sıfat Hakimiyeti",
        description_en="Dominate with your strongest personality trait",
        description_tr="En güçlü kişilik sıfatınla öne çık",
        category="personality",
        duration_minutes=4320,
        coin_reward_base=75,
        leaderboard_metric="trait_score",
    ),
    "accuracy_duel": ChallengeType(
        type_id="accuracy_duel",
        name_en="Accuracy Duel",
        name_tr="Doğruluk Düellosu",
        description_en="Answer discovery game questions with most accuracy",
        description_tr="Keşif oyunu sorularını en doğru yanıtla",
        category="knowledge",
        duration_minutes=720,
        coin_reward_base=60,
        leaderboard_metric="accuracy_pct",
    ),
}


class CreateChallengeRequest:
    def __init__(
        self,
        type_id: str = "",
        title: str = "",
        description: str = "",
        visibility: str = "public",
        leaderboard_mode: str = "mixed",
        is_handicapped: bool = False,
        duration_minutes: int = 1440,
    ):
        self.type_id = type_id
        self.title = title
        self.description = description
        self.visibility = visibility
        self.leaderboard_mode = leaderboard_mode
        self.is_handicapped = is_handicapped
        self.duration_minutes = duration_minutes


class JoinChallengeRequest:
    def __init__(self, user_id: int, challenge_id: str):
        self.user_id = user_id
        self.challenge_id = challenge_id


class UpdateScoreRequest:
    def __init__(self, user_id: int, challenge_id: str, score_delta: int):
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.score_delta = score_delta


class CancelChallengeRequest:
    def __init__(self, user_id: int, challenge_id: str):
        self.user_id = user_id
        self.challenge_id = challenge_id
