"""Badge service"""

class BadgeService:
    """Service for managing badges"""
    def get_user_badges(self, user_id):
        return []
    def award_badge(self, user_id, badge_id):
        return {'user_id': user_id, 'badge_id': badge_id}

class BadgeError(Exception):
    pass

class BadgeNotFoundError(BadgeError):
    pass
