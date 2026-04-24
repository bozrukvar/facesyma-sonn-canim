#!/usr/bin/env python
"""
Smart translation using pre-built translation tables
Fast, offline, no external dependencies
"""

from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent

# Pre-built translations for all 17 languages
TRANSLATIONS = {
    'tr': {  # Turkish
        '🎮 Gamification Phase 2 — Monitoring Dashboard': '🎮 Oyunlaştırma Faz 2 — İzleme Panosu',
        'Loading...': 'Yükleniyor...',
        'Healthy': 'Sağlıklı',
        'Degraded': 'Bozulmuş',
        'Error': 'Hata',
        'Last updated: %s': 'Son güncelleme: %s',
        '↻ Refresh Now': '↻ Şimdi Yenile',
        'Auto-refresh (5s)': 'Otomatik Yenileme (5s)',
        '📦 Cache Performance': '📦 Hiş Performansı',
        'Hit Rate': 'Hit Oranı',
        'Total Queries': 'Toplam Sorgular',
        'Memory Used': 'Kullanılan Bellek',
        '⚡ Leaderboard Performance': '⚡ Lider Tablosu Performansı',
        'Average Query Time': 'Ortalama Sorgu Süresi',
        'P95 Latency': 'P95 Gecikmesi',
        '📡 WebSocket Connections': '📡 WebSocket Bağlantıları',
        'Current Connections': 'Mevcut Bağlantılar',
        'Connections (Last Hour)': 'Bağlantılar (Son Saat)',
        'Peak Today': 'Bugünün Zirvesi',
        '📊 Trend Analysis': '📊 Trend Analizi',
        'Latest Snapshot Age': 'En Son Anlık Görüntü Yaşı',
        'Retention Policy': 'Saklama İlkesi',
        '🏥 System Health': '🏥 Sistem Sağlığı',
        'Status': 'Durum',
        'Components': 'Bileşenler',
        '📈 Query Performance Trend': '📈 Sorgu Performansı Trendi',
        'Average': 'Ortalama',
        'Min': 'Min',
        'Max': 'Maks',
        'Leaderboard Type': 'Lider Tablosu Türü',
        'Snapshots': 'Anlık Görüntüler',
        'Type': 'Tür',
        'Queries': 'Sorgular',
        'Avg Time': 'Ort. Süre',
        'Coins': 'Madeni Paralar',
        'Badges': 'Rozetler',
        'Rank': 'Sıra',
        'Username': 'Kullanıcı Adı',
        'Meals Completed': 'Tamamlanan Öğünler',
        'Challenges Won': 'Kazanılan Zorluklar',
        'Accuracy': 'Doğruluk',
        'Your Rank': 'Sizin Sıranız',
        'Rank Change': 'Sıra Değişimi',
        'Coins Gained': 'Kazanılan Madeni Paralar',
        'Badges Unlocked': 'Açılan Rozetler',
        'Global Leaderboard': 'Küresel Lider Tablosu',
        'Trait-Based Leaderboard': 'Özellik Tabanlı Lider Tablosu',
        'Community Leaderboard': 'Topluluk Lider Tablosu',
        'User Trend': 'Kullanıcı Trendi',
        'Trending Users': 'Trend Olan Kullanıcılar',
        'Leaderboard Statistics': 'Lider Tablosu İstatistikleri',
        'Most Improved': 'En İyileşen',
        'Most Active': 'En Aktif',
        'Ascending': 'Yükseliş',
        'Stable': 'Durağan',
        'Descending': 'İniş',
        '%d days tracked': '%d gün izlendi',
        '%d snapshots': '%d anlık görüntü',
        'Redis': 'Redis',
        'MongoDB': 'MongoDB',
        'Scheduler': 'Zamanlayıcı',
        'Running': 'Çalışıyor',
        'Stopped': 'Durduruldu',
        'Unknown': 'Bilinmiyor',
        'Unavailable': 'Kullanılamaz',
        'Coins awarded': 'Madeni paralar verildi',
        'Badge unlocked': 'Rozet açıldı',
        'Mission completed': 'Görev tamamlandı',
        'Cache cleared': 'Önbellek temizlendi',
        'Cache invalidation failed (non-critical): %s': 'Önbellek geçersiz kılma başarısız (kritik olmayan): %s',
        'Connected to %s leaderboard': '%s lider tablosuna bağlandı',
        'Failed to connect': 'Bağlanılamadı',
        'Disconnected from leaderboard': 'Lider tablosundan bağlantı kesildi',
        'Leaderboard updated, please refresh': 'Lider tablosu güncellendi, lütfen yenileyin',
        '%s moved from rank %d to rank %d': '%s, sıra %d\'den sıra %d\'ye taşındı',
        'Keep-alive ping confirmed': 'Canlı tutma ping\'i onaylandı',
        'Subscribed to leaderboard updates': 'Lider tablosu güncellemeleri\'ne abone olundu',
        'Unsubscribed from leaderboard updates': 'Lider tablosu güncellemeleri\'nden abonelikten çıkıldı',
        'Internal server error': 'İç sunucu hatası',
        'Invalid parameter: %s': 'Geçersiz parametre: %s',
        'Not found': 'Bulunamadı',
        'Unauthorized': 'Yetkisiz',
        'Forbidden': 'Yasak',
        'No trend data found for user %d': 'Kullanıcı %d için trend verisi bulunamadı',
        'Leaderboard error: %s': 'Lider tablosu hatası: %s',
        'Cache error: %s': 'Önbellek hatası: %s',
        'Database error: %s': 'Veritabanı hatası: %s',
        'WebSocket error: %s': 'WebSocket hatası: %s',
        'Invalid JSON in request body': 'İstek gövdesinde geçersiz JSON',
    },
    'es': {  # Spanish
        '🎮 Gamification Phase 2 — Monitoring Dashboard': '🎮 Gamificación Fase 2 — Panel de Monitoreo',
        'Loading...': 'Cargando...',
        'Healthy': 'Saludable',
        'Degraded': 'Degradado',
        'Error': 'Error',
        'Last updated: %s': 'Última actualización: %s',
        '↻ Refresh Now': '↻ Actualizar Ahora',
        'Auto-refresh (5s)': 'Actualizar Automáticamente (5s)',
        '📦 Cache Performance': '📦 Rendimiento de Caché',
        'Hit Rate': 'Tasa de Acierto',
        'Total Queries': 'Consultas Totales',
        'Memory Used': 'Memoria Utilizada',
        '⚡ Leaderboard Performance': '⚡ Rendimiento del Tablero',
        'Average Query Time': 'Tiempo Promedio de Consulta',
        'P95 Latency': 'Latencia P95',
        '📡 WebSocket Connections': '📡 Conexiones WebSocket',
        'Current Connections': 'Conexiones Actuales',
        'Connections (Last Hour)': 'Conexiones (Última Hora)',
        'Peak Today': 'Pico de Hoy',
        '📊 Trend Analysis': '📊 Análisis de Tendencias',
        'Latest Snapshot Age': 'Antigüedad de la Última Instantánea',
        'Retention Policy': 'Política de Retención',
        '🏥 System Health': '🏥 Salud del Sistema',
        'Status': 'Estado',
        'Components': 'Componentes',
        '📈 Query Performance Trend': '📈 Tendencia de Rendimiento de Consultas',
        'Average': 'Promedio',
        'Min': 'Mín',
        'Max': 'Máx',
        'Leaderboard Type': 'Tipo de Tablero',
        'Snapshots': 'Instantáneas',
        'Type': 'Tipo',
        'Queries': 'Consultas',
        'Avg Time': 'Tiempo Promedio',
        'Coins': 'Monedas',
        'Badges': 'Insignias',
        'Rank': 'Rango',
        'Username': 'Nombre de Usuario',
        'Meals Completed': 'Comidas Completadas',
        'Challenges Won': 'Desafíos Ganados',
        'Accuracy': 'Precisión',
        'Your Rank': 'Tu Rango',
        'Rank Change': 'Cambio de Rango',
        'Coins Gained': 'Monedas Ganadas',
        'Badges Unlocked': 'Insignias Desbloqueadas',
        'Global Leaderboard': 'Tablero Global',
        'Trait-Based Leaderboard': 'Tablero Basado en Características',
        'Community Leaderboard': 'Tablero Comunitario',
        'User Trend': 'Tendencia de Usuario',
        'Trending Users': 'Usuarios en Tendencia',
        'Leaderboard Statistics': 'Estadísticas del Tablero',
        'Most Improved': 'Más Mejorado',
        'Most Active': 'Más Activo',
        'Ascending': 'Ascendente',
        'Stable': 'Estable',
        'Descending': 'Descendente',
        '%d days tracked': '%d días rastreados',
        '%d snapshots': '%d instantáneas',
        'Redis': 'Redis',
        'MongoDB': 'MongoDB',
        'Scheduler': 'Programador',
        'Running': 'Ejecutándose',
        'Stopped': 'Detenido',
        'Unknown': 'Desconocido',
        'Unavailable': 'No Disponible',
        'Coins awarded': 'Monedas otorgadas',
        'Badge unlocked': 'Insignia desbloqueada',
        'Mission completed': 'Misión completada',
        'Cache cleared': 'Caché borrado',
        'Connected to %s leaderboard': 'Conectado al tablero %s',
        'Failed to connect': 'Fallo al conectar',
        'Leaderboard updated, please refresh': 'Tablero actualizado, por favor actualice',
    },
    'de': {  # German
        '🎮 Gamification Phase 2 — Monitoring Dashboard': '🎮 Gamification Phase 2 — Überwachungs-Dashboard',
        'Loading...': 'Wird geladen...',
        'Healthy': 'Gesund',
        'Degraded': 'Beeinträchtigt',
        'Error': 'Fehler',
        'Last updated: %s': 'Zuletzt aktualisiert: %s',
        '↻ Refresh Now': '↻ Jetzt Aktualisieren',
        'Auto-refresh (5s)': 'Automatische Aktualisierung (5s)',
        '📦 Cache Performance': '📦 Cache-Leistung',
        'Hit Rate': 'Trefferquote',
        'Total Queries': 'Gesamtabfragen',
        'Memory Used': 'Speicherverwendung',
        '⚡ Leaderboard Performance': '⚡ Ranglisten-Leistung',
        'Average Query Time': 'Durchschnittliche Abfragezeit',
        'P95 Latency': 'P95-Latenz',
        '📡 WebSocket Connections': '📡 WebSocket-Verbindungen',
        'Current Connections': 'Aktuelle Verbindungen',
        'Peak Today': 'Spitzenwert Heute',
        '🏥 System Health': '🏥 Systemgesundheit',
        'Status': 'Status',
        'Components': 'Komponenten',
        '📈 Query Performance Trend': '📈 Abfrageleistungs-Trend',
        'Average': 'Durchschnitt',
        'Leaderboard Type': 'Ranglistentyp',
        'Snapshots': 'Schnappschüsse',
        'Avg Time': 'Durchschn. Zeit',
        'Coins': 'Münzen',
        'Badges': 'Abzeichen',
        'Rank': 'Rang',
        'Username': 'Benutzername',
        'Challenges Won': 'Herausforderungen Gewonnen',
        'Accuracy': 'Genauigkeit',
        'Most Improved': 'Meiste Verbesserung',
        'Most Active': 'Am Aktivsten',
        'Ascending': 'Aufsteigend',
        'Stable': 'Stabil',
        'Descending': 'Absteigend',
    },
    'fr': {  # French
        '🎮 Gamification Phase 2 — Monitoring Dashboard': '🎮 Gamification Phase 2 — Tableau de Bord de Surveillance',
        'Loading...': 'Chargement...',
        'Healthy': 'Sain',
        'Degraded': 'Dégradé',
        'Error': 'Erreur',
        'Last updated: %s': 'Dernière mise à jour: %s',
        '↻ Refresh Now': '↻ Actualiser Maintenant',
        'Auto-refresh (5s)': 'Actualisation Automatique (5s)',
        '📦 Cache Performance': '📦 Performance du Cache',
        'Hit Rate': 'Taux de Succès',
        'Total Queries': 'Requêtes Totales',
        'Memory Used': 'Mémoire Utilisée',
        '⚡ Leaderboard Performance': '⚡ Performance du Classement',
        'Average Query Time': 'Temps Moyen de Requête',
        'P95 Latency': 'Latence P95',
        '📡 WebSocket Connections': '📡 Connexions WebSocket',
        'Current Connections': 'Connexions Actuelles',
        'Peak Today': 'Pic Aujourd\'hui',
        '🏥 System Health': '🏥 Santé du Système',
        'Status': 'Statut',
        '📈 Query Performance Trend': '📈 Tendance des Performances de Requête',
        'Coins': 'Pièces',
        'Badges': 'Badges',
        'Rank': 'Rang',
        'Username': 'Nom d\'Utilisateur',
        'Most Improved': 'Le Plus Amélioré',
        'Most Active': 'Le Plus Actif',
    },
    'ja': {  # Japanese
        '🎮 Gamification Phase 2 — Monitoring Dashboard': '🎮 ゲーム化フェーズ 2 — 監視ダッシュボード',
        'Loading...': '読み込み中...',
        'Healthy': '健康',
        'Degraded': '低下',
        'Error': 'エラー',
        'Last updated: %s': '最後に更新: %s',
        '↻ Refresh Now': '↻ 今すぐ更新',
        'Auto-refresh (5s)': '自動更新 (5秒)',
        '📦 Cache Performance': '📦 キャッシュ性能',
        'Hit Rate': 'ヒット率',
        'Total Queries': '総クエリ',
        'Memory Used': 'メモリ使用量',
        '⚡ Leaderboard Performance': '⚡ リーダーボード性能',
        'Average Query Time': '平均クエリ時間',
        'P95 Latency': 'P95レイテンシ',
        '📡 WebSocket Connections': '📡 WebSocket接続',
        'Current Connections': '現在の接続',
        'Peak Today': '本日のピーク',
        '🏥 System Health': '🏥 システムヘルス',
        'Status': 'ステータス',
        'Coins': 'コイン',
        'Rank': 'ランク',
        'Username': 'ユーザー名',
        'Accuracy': '精度',
    },
    'zh-hans': {  # Simplified Chinese
        '🎮 Gamification Phase 2 — Monitoring Dashboard': '🎮 游戏化第二阶段 — 监控仪表板',
        'Loading...': '加载中...',
        'Healthy': '健康',
        'Degraded': '降级',
        'Error': '错误',
        'Last updated: %s': '最后更新：%s',
        '↻ Refresh Now': '↻ 立即刷新',
        'Auto-refresh (5s)': '自动刷新 (5秒)',
        '📦 Cache Performance': '📦 缓存性能',
        'Hit Rate': '命中率',
        'Total Queries': '总查询数',
        'Memory Used': '内存使用',
        '⚡ Leaderboard Performance': '⚡ 排行榜性能',
        'Average Query Time': '平均查询时间',
        'P95 Latency': 'P95延迟',
        '📡 WebSocket Connections': '📡 WebSocket连接',
        'Current Connections': '当前连接',
        'Peak Today': '今日峰值',
        '🏥 System Health': '🏥 系统健康',
        'Status': '状态',
        'Coins': '硬币',
        'Rank': '排名',
        'Username': '用户名',
    },
    'zh-hant': {  # Traditional Chinese
        '🎮 Gamification Phase 2 — Monitoring Dashboard': '🎮 遊戲化第二階段 — 監控儀表板',
        'Loading...': '載入中...',
        'Healthy': '健康',
        'Error': '錯誤',
        'Last updated: %s': '最後更新：%s',
        '📦 Cache Performance': '📦 快取效能',
        'Hit Rate': '命中率',
        'Coins': '硬幣',
        'Rank': '排名',
        'Username': '使用者名稱',
    },
    'ko': {  # Korean
        '🎮 Gamification Phase 2 — Monitoring Dashboard': '🎮 게임화 페이즈 2 — 모니터링 대시보드',
        'Loading...': '로드 중...',
        'Healthy': '정상',
        'Error': '오류',
        'Last updated: %s': '마지막 업데이트: %s',
        '📦 Cache Performance': '📦 캐시 성능',
        'Hit Rate': '히트율',
        'Coins': '동전',
        'Rank': '순위',
        'Username': '사용자명',
    },
    'pt': {  # Portuguese
        '🎮 Gamification Phase 2 — Monitoring Dashboard': '🎮 Gamificação Fase 2 — Painel de Monitoramento',
        'Loading...': 'Carregando...',
        'Healthy': 'Saudável',
        'Error': 'Erro',
        'Last updated: %s': 'Última atualização: %s',
        '📦 Cache Performance': '📦 Desempenho de Cache',
        'Hit Rate': 'Taxa de Acerto',
        'Coins': 'Moedas',
        'Rank': 'Rank',
        'Username': 'Nome de Usuário',
    },
    'ru': {  # Russian
        '🎮 Gamification Phase 2 — Monitoring Dashboard': '🎮 Геймификация Этап 2 — Панель мониторинга',
        'Loading...': 'Загрузка...',
        'Healthy': 'Здоров',
        'Error': 'Ошибка',
        'Last updated: %s': 'Последнее обновление: %s',
        '📦 Cache Performance': '📦 Производительность кэша',
        'Hit Rate': 'Коэффициент попадания',
        'Coins': 'Монеты',
        'Rank': 'Ранг',
        'Username': 'Имя пользователя',
    },
    'ar': {  # Arabic
        'Loading...': 'جارٍ التحميل...',
        'Error': 'خطأ',
        'Status': 'الحالة',
        'Coins': 'العملات',
        'Rank': 'الرتبة',
    },
    'he': {  # Hebrew
        'Loading...': 'טעינה...',
        'Error': 'שגיאה',
        'Status': 'סטטוס',
        'Coins': 'מטבעות',
        'Rank': 'דירוג',
    },
    'hi': {  # Hindi
        'Loading...': 'लोड हो रहा है...',
        'Error': 'त्रुटि',
        'Status': 'स्थिति',
        'Coins': 'सिक्के',
        'Rank': 'रैंक',
    },
    'vi': {  # Vietnamese
        'Loading...': 'Đang tải...',
        'Error': 'Lỗi',
        'Status': 'Trạng thái',
        'Coins': 'Xu',
        'Rank': 'Hạng',
    },
    'it': {  # Italian
        'Loading...': 'Caricamento...',
        'Error': 'Errore',
        'Status': 'Stato',
        'Coins': 'Monete',
        'Rank': 'Rango',
    },
    'pl': {  # Polish
        'Loading...': 'Ładowanie...',
        'Error': 'Błąd',
        'Status': 'Status',
        'Coins': 'Monety',
        'Rank': 'Ranga',
    },
    'th': {  # Thai
        'Loading...': 'กำลังโหลด...',
        'Error': 'ข้อผิดพลาด',
        'Status': 'สถานะ',
        'Coins': 'เหรียญ',
        'Rank': 'อันดับ',
    },
}


def translate_po_file(po_file_path, lang_code):
    """Translate .po file using pre-built dictionary"""
    if lang_code not in TRANSLATIONS:
        print(f"  ⚠️  No translation dictionary for {lang_code}")
        return 0

    translations = TRANSLATIONS[lang_code]

    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse and translate each msgid
    lines = content.split('\n')
    _n_lines = len(lines)
    result_lines = []
    _append = result_lines.append
    i = 0
    translated_count = 0

    while i < _n_lines:
        line = lines[i]
        _lsw = line.startswith

        # Look for msgid lines (skip header)
        if _lsw('msgid "') and not _lsw('msgid ""'):
            # Extract the English string
            msgid_content = line[7:-1]

            # Handle multiline msgid
            _append(line)
            i += 1
            while i < _n_lines and lines[i].startswith('"') and not lines[i].startswith('msgstr'):
                _li = lines[i]
                msgid_content += _li[1:-1]
                _append(_li)
                i += 1

            # Look up translation
            translated = translations.get(msgid_content, None)

            # Add msgstr line
            if i < _n_lines and lines[i].startswith('msgstr'):
                if translated:
                    _append(f'msgstr "{translated}"')
                    translated_count += 1
                else:
                    _append(lines[i])
                i += 1
            else:
                if translated:
                    _append(f'msgstr "{translated}"')
                    translated_count += 1
        else:
            _append(line)
            i += 1

    # Write back
    new_content = '\n'.join(result_lines)
    with open(po_file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return translated_count


def main():
    """Translate all .po files using pre-built translations"""
    locale_dir = BASE_DIR / 'locale'

    languages = [
        ('tr', 'Türkçe'),
        ('de', 'Deutsch'),
        ('fr', 'Français'),
        ('es', 'Español'),
        ('it', 'Italiano'),
        ('pt', 'Português'),
        ('pl', 'Polski'),
        ('ru', 'Русский'),
        ('ja', '日本語'),
        ('zh-hans', '简体中文'),
        ('zh-hant', '繁體中文'),
        ('ko', '한국어'),
        ('ar', 'العربية'),
        ('he', 'עברית'),
        ('hi', 'हिन्दी'),
        ('vi', 'Tiếng Việt'),
        ('th', 'ไทย'),
    ]

    print('\n🌍 Translating to 17 languages...\n')

    translated_langs = 0
    total_translations = 0

    for code, name in languages:
        po_file = locale_dir / code / 'LC_MESSAGES' / 'django.po'

        if po_file.exists():
            print(f'  📝 {name:15} ({code:8})', end=' ... ')
            try:
                count = translate_po_file(po_file, code)
                translated_langs += 1
                total_translations += count
                print(f'✅ {count:2} translations')
            except Exception as e:
                print(f'⚠️  {e}')

    print(f'\n✅ Translation complete!')
    print(f'   {translated_langs} languages translated')
    print(f'   {total_translations} total strings translated')

    print(f'\n🔨 Compiling to .mo files...\n')
    import subprocess
    result = subprocess.run(['python', 'compile_messages.py'], cwd=BASE_DIR)

    if result.returncode == 0:
        print(f'\n🎉 All done! All 17 languages ready to test.')
        print(f'\nTest examples:')
        print(f'  curl -H "Accept-Language: tr" http://localhost:8000/api/v1/admin/gamification-dashboard/')
        print(f'  curl -H "Accept-Language: es" http://localhost:8000/api/v1/admin/gamification-dashboard/')
        print(f'  curl -H "Accept-Language: ja" http://localhost:8000/api/v1/admin/gamification-dashboard/')


if __name__ == '__main__':
    main()
