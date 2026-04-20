"""Leaderboard models"""

class LeaderboardFilter:
    """Filter for leaderboard queries"""
    def __init__(self, category=None, period=None, country=None):
        self.category = category
        self.period = period
        self.country = country
