"""
admin_api/utils/partnerships_indexes.py
========================================
MongoDB index tanımları — partnerships koleksiyonu.

Çalıştırma: python manage.py shell -c "from admin_api.utils.partnerships_indexes import create_partnerships_indexes; create_partnerships_indexes()"
"""
import logging

log = logging.getLogger(__name__)


def create_partnerships_indexes():
    from admin_api.utils.mongo import get_db
    db = get_db()
    col = db['partnerships']

    # Davet kodu benzersiz olmalı (sadece pending kayıtlar için unique)
    col.create_index('invite_code', unique=False, sparse=True,
                     name='invite_code_idx')

    # Kullanıcı A'nın ortaklıklarını status'a göre hızlı bul
    col.create_index([('user_a_id', 1), ('status', 1)],
                     name='user_a_status_idx')

    # Kullanıcı B'nin ortaklıklarını status'a göre hızlı bul
    col.create_index([('user_b_id', 1), ('status', 1)],
                     name='user_b_status_idx')

    # Aktif/bekleyen ortaklıkları tarihe göre sıralı getir
    col.create_index([('status', 1), ('created_at', -1)],
                     name='status_date_idx')

    log.info('partnerships indexes created')
    return True


if __name__ == '__main__':
    create_partnerships_indexes()
    print('Done')
