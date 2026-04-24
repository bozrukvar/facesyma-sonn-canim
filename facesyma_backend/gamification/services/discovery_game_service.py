"""Discovery game service"""


class DiscoveryGameService:
    """Service for discovery games"""
    def get_game_types(self):
        return ['trait_discovery', 'sifat_learning', 'quiz']
    
    def start_session(self, user_id, game_type):
        return {'session_id': 'sess_123', 'user_id': user_id, 'game_type': game_type}
    
    def answer_question(self, session_id, user_id, answer):
        return {'session_id': session_id, 'correct': False, 'score_gained': 0}
    
    def abandon_session(self, session_id, user_id):
        return {'session_id': session_id, 'abandoned': True}


class DiscoveryGameError(Exception):
    pass


class SessionNotFoundError(DiscoveryGameError):
    pass


class GameTypeNotFoundError(DiscoveryGameError):
    pass
