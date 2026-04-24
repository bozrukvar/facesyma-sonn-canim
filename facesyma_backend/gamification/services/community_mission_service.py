"""Community mission service"""


class CommunityMissionService:
    """Service for managing community missions"""
    def get_active_missions(self):
        return []
    
    def join_mission(self, user_id, mission_id):
        return {'user_id': user_id, 'mission_id': mission_id}
    
    def contribute_to_mission(self, user_id, mission_id, amount):
        return {'user_id': user_id, 'mission_id': mission_id, 'contributed': amount}


class MissionError(Exception):
    pass


class MissionNotFoundError(MissionError):
    pass


class MissionTypeNotFoundError(MissionError):
    pass


class UserAlreadyJoinedError(MissionError):
    pass
