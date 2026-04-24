"""Challenge models"""
from typing import Optional

CHALLENGE_TYPES = [
    'weekly_ranking',
    'daily_duel',
    'community_goal',
    'streak_challenge'
]


class Challenge:
    """Challenge model"""
    def __init__(self, challenge_id, challenge_type, name):
        self.challenge_id = challenge_id
        self.challenge_type = challenge_type
        self.name = name


class ChallengeMembership:
    """User's participation in a challenge"""
    def __init__(self, user_id, challenge_id, score):
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.score = score


class CreateChallengeRequest:
    """Request to create a challenge"""
    def __init__(
        self,
        challenge_type: str,
        name: str,
        description: Optional[str] = None,
        duration_days: int = 7,
        max_participants: Optional[int] = None
    ):
        self.challenge_type = challenge_type
        self.name = name
        self.description = description
        self.duration_days = duration_days
        self.max_participants = max_participants


class JoinChallengeRequest:
    """Request to join a challenge"""
    def __init__(self, user_id: int, challenge_id: str):
        self.user_id = user_id
        self.challenge_id = challenge_id


class UpdateScoreRequest:
    """Request to update challenge score"""
    def __init__(
        self,
        user_id: int,
        challenge_id: str,
        score_delta: int
    ):
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.score_delta = score_delta


class CancelChallengeRequest:
    """Request to cancel/exit a challenge"""
    def __init__(self, user_id: int, challenge_id: str):
        self.user_id = user_id
        self.challenge_id = challenge_id
