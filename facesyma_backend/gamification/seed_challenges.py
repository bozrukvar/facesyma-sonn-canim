"""Seed initial active challenges into MongoDB.
Run inside the backend container:
  python -m gamification.seed_challenges
"""
import os
import random
import string
from datetime import datetime, timedelta

import pymongo

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/facesyma')
_client = pymongo.MongoClient(MONGO_URI)
_db = _client.get_default_database()


def _gen_id():
    return 'ch_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


SEED_CHALLENGES = [
    {
        'type_id': 'golden_ratio_race',
        'title_tr': 'Altın Oran Yarışması',
        'title_en': 'Golden Ratio Race',
        'description_tr': 'Yüz analizinde en yüksek altın oran skoruna ulaş — 3 günlük rekabet!',
        'description_en': 'Achieve the highest golden ratio score in face analysis — 3-day competition!',
        'coin_reward': 80,
        'max_participants': 50,
        'duration_minutes': 4320,
        'emoji': '✨',
    },
    {
        'type_id': 'mirror_champion',
        'title_tr': 'Ayna Şampiyonu',
        'title_en': 'Mirror Champion',
        'description_tr': 'Bugün en çok yüz analizi yapan kazan!',
        'description_en': 'Who can complete the most face analyses today?',
        'coin_reward': 50,
        'max_participants': 100,
        'duration_minutes': 1440,
        'emoji': '🪞',
    },
    {
        'type_id': 'community_builder',
        'title_tr': 'Topluluk Büyütücüsü',
        'title_en': 'Community Builder',
        'description_tr': '2 gün içinde en çok topluluğa katıl, ağını genişlet!',
        'description_en': 'Join the most communities in 2 days and grow your network!',
        'coin_reward': 60,
        'max_participants': 50,
        'duration_minutes': 2880,
        'emoji': '🏘️',
    },
    {
        'type_id': 'trait_streak',
        'title_tr': 'Sıfat Serisi',
        'title_en': 'Trait Streak',
        'description_tr': 'Bu hafta günlük quest\'i art arda en çok tamamlayan kazanır!',
        'description_en': 'Complete daily quests consecutively this week to win!',
        'coin_reward': 120,
        'max_participants': 200,
        'duration_minutes': 10080,
        'emoji': '🔥',
    },
    {
        'type_id': 'coach_student',
        'title_tr': 'Koç Öğrencisi',
        'title_en': 'Coach Student',
        'description_tr': 'AI koçunla en çok etkileşime gir — içgörüler madeni para kazandırır!',
        'description_en': 'Engage your AI coach the most — every insight earns you coins!',
        'coin_reward': 70,
        'max_participants': 50,
        'duration_minutes': 2880,
        'emoji': '🧠',
    },
    {
        'type_id': 'accuracy_duel',
        'title_tr': 'Doğruluk Düellosu',
        'title_en': 'Accuracy Duel',
        'description_tr': 'Keşif oyunu sorularını en doğru yanıtlayan 12 saatte şampiyon!',
        'description_en': 'Answer discovery game questions with the highest accuracy in 12 hours!',
        'coin_reward': 60,
        'max_participants': 50,
        'duration_minutes': 720,
        'emoji': '🎯',
    },
    {
        'type_id': 'compatibility_hunter',
        'title_tr': 'Uyumluluk Avcısı',
        'title_en': 'Compatibility Hunter',
        'description_tr': 'Topluluklar üzerinden en yüksek uyumluluk skoru ile peer bağlantısı kur!',
        'description_en': 'Form the highest-scoring peer connections through communities!',
        'coin_reward': 90,
        'max_participants': 30,
        'duration_minutes': 4320,
        'emoji': '💫',
    },
    {
        'type_id': 'trait_dominance',
        'title_tr': 'Sıfat Hakimiyeti',
        'title_en': 'Trait Dominance',
        'description_tr': 'En güçlü kişilik sıfatınla öne çık — 3 günlük kişilik savaşı!',
        'description_en': 'Dominate with your strongest personality trait — 3-day battle!',
        'coin_reward': 75,
        'max_participants': 50,
        'duration_minutes': 4320,
        'emoji': '⚡',
    },
    {
        'type_id': 'badge_race',
        'title_tr': 'Rozet Yarışı',
        'title_en': 'Badge Race',
        'description_tr': 'Bu hafta en çok rozet kazanan zirveye çıkar!',
        'description_en': 'Earn the most badges this week and reach the top!',
        'coin_reward': 100,
        'max_participants': 100,
        'duration_minutes': 10080,
        'emoji': '🎖️',
    },
    {
        'type_id': 'meal_selection',
        'title_tr': 'Dünya Mutfağı Yarışması',
        'title_en': 'World Cuisine Challenge',
        'description_tr': 'Bugün en çok farklı ülke yemeği seçen kazanır!',
        'description_en': 'Select the most world meals today and win!',
        'coin_reward': 50,
        'max_participants': 100,
        'duration_minutes': 1440,
        'emoji': '🌍',
    },
]


def seed():
    col = _db['social_challenges']
    now = datetime.utcnow()

    inserted = 0
    skipped = 0
    for ch in SEED_CHALLENGES:
        # Don't duplicate — check by type_id + system flag
        existing = col.find_one({'type_id': ch['type_id'], 'is_system': True, 'status': 'active'})
        if existing:
            skipped += 1
            continue

        duration = ch['duration_minutes']
        end = now + timedelta(minutes=duration)
        challenge_id = _gen_id()

        col.insert_one({
            'challenge_id': challenge_id,
            'type_id': ch['type_id'],
            'title': ch['title_tr'],
            'title_en': ch['title_en'],
            'description': ch['description_tr'],
            'description_en': ch['description_en'],
            'emoji': ch['emoji'],
            'coin_reward': ch['coin_reward'],
            'max_participants': ch['max_participants'],
            'visibility': 'public',
            'leaderboard_mode': 'score',
            'is_handicapped': False,
            'is_system': True,
            'status': 'active',
            'creator_id': 0,
            'participants': [],
            'start_time': now.isoformat(),
            'end_time': end.isoformat(),
            'created_at': now.isoformat(),
        })
        inserted += 1
        print(f"  ✓ {ch['emoji']} {ch['title_tr']} ({ch['type_id']}) — bitiş: {end.strftime('%d/%m %H:%M')}")

    print(f"\nTamamlandı: {inserted} eklendi, {skipped} zaten vardı.")


if __name__ == '__main__':
    print('Facesyma challenge seed başlıyor...\n')
    seed()
