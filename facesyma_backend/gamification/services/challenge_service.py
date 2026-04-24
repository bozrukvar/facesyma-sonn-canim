"""Challenge service"""
class ChallengeService:
    """Service for managing challenges"""
    def get_active_challenges(self, user_id, challenge_type=None):
        return []
    
    def join_challenge(self, user_id, challenge_id):
        return {'user_id': user_id, 'challenge_id': challenge_id}
    
    def update_score(self, user_id, challenge_id, score):
        return {'user_id': user_id, 'challenge_id': challenge_id, 'score': score}
    
    def get_leaderboard(self, challenge_id, limit=10):
        return []


class ChallengeError(Exception):
    pass


class ChallengeNotFoundError(ChallengeError):
    pass


class InvalidChallengeTypeError(ChallengeError):
    pass


class UserAlreadyJoinedError(ChallengeError):
    pass
