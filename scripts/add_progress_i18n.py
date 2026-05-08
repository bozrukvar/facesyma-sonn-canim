"""Add features.progress + features.progress_desc after features.diet_desc in all 18 language blocks."""
import pathlib

path = pathlib.Path(__file__).parent.parent / 'facesyma_mobile/src/utils/i18n.ts'
content = path.read_text(encoding='utf-8')

inserts = [
    (
        "    'features.diet_desc': 'Kişiselleştirilmiş öğünler',",
        "    'features.progress': 'İlerleme',\n"
        "    'features.progress_desc': 'Testlerdeki gelişimini görüntüle',"
    ),
    (
        "    'features.diet_desc': 'Personalized meals',",
        "    'features.progress': 'My Progress',\n"
        "    'features.progress_desc': 'View your growth across tests',"
    ),
    (
        "    'features.diet_desc': 'Personalisierte Mahlzeiten',",
        "    'features.progress': 'Mein Fortschritt',\n"
        "    'features.progress_desc': 'Fortschritt über Tests verfolgen',"
    ),
    (
        "    'features.diet_desc': 'Персонализированное питание',",
        "    'features.progress': 'Мой прогресс',\n"
        "    'features.progress_desc': 'Отслеживай рост по тестам',"
    ),
    (
        "    'features.diet_desc': 'وجبات مخصصة',",
        "    'features.progress': 'تقدمي',\n"
        "    'features.progress_desc': 'تتبع نموك عبر الاختبارات',"
    ),
    (
        "    'features.diet_desc': 'Comidas personalizadas',",
        "    'features.progress': 'Mi Progreso',\n"
        "    'features.progress_desc': 'Ver crecimiento en los tests',"
    ),
    (
        "    'features.diet_desc': '개인화된 식사',",
        "    'features.progress': '내 진행',\n"
        "    'features.progress_desc': '테스트 성장 확인',"
    ),
    (
        "    'features.diet_desc': 'パーソナライズ食事',",
        "    'features.progress': '私の進捗',\n"
        "    'features.progress_desc': 'テストの成長を確認',"
    ),
    (
        "    'features.diet_desc': '个性化饮食',",
        "    'features.progress': '我的进度',\n"
        "    'features.progress_desc': '查看测试中的成长',"
    ),
    (
        "    'features.diet_desc': 'व्यक्तिगत भोजन',",
        "    'features.progress': 'मेरी प्रगति',\n"
        "    'features.progress_desc': 'टेस्ट में विकास देखें',"
    ),
    (
        "    'features.diet_desc': 'Repas personnalisés',",
        "    'features.progress': 'Ma Progression',\n"
        "    'features.progress_desc': 'Suivez votre croissance aux tests',"
    ),
    (
        "    'features.diet_desc': 'Refeições personalizadas',",
        "    'features.progress': 'Meu Progresso',\n"
        "    'features.progress_desc': 'Ver crescimento nos testes',"
    ),
    (
        "    'features.diet_desc': 'ব্যক্তিগত খাবার',",
        "    'features.progress': 'আমার অগ্রগতি',\n"
        "    'features.progress_desc': 'টেস্টে প্রবৃদ্ধি দেখুন',"
    ),
    (
        "    'features.diet_desc': 'Makanan yang dipersonalisasi',",
        "    'features.progress': 'Kemajuan Saya',\n"
        "    'features.progress_desc': 'Lihat pertumbuhan di tes',"
    ),
    (
        "    'features.diet_desc': 'ذاتی کھانا',",
        "    'features.progress': 'میری ترقی',\n"
        "    'features.progress_desc': 'ٹیسٹ میں ترقی دیکھیں',"
    ),
    (
        "    'features.diet_desc': 'Pasti personalizzati',",
        "    'features.progress': 'Il Mio Progresso',\n"
        "    'features.progress_desc': 'Visualizza crescita nei test',"
    ),
    (
        "    'features.diet_desc': 'Bữa ăn cá nhân hóa',",
        "    'features.progress': 'Tiến Độ Của Tôi',\n"
        "    'features.progress_desc': 'Xem tăng trưởng qua bài test',"
    ),
    (
        "    'features.diet_desc': 'Spersonalizowane posiłki',",
        "    'features.progress': 'Mój Postęp',\n"
        "    'features.progress_desc': 'Śledź wzrost w testach',"
    ),
]

count = 0
for anchor, insertion in inserts:
    if anchor in content:
        # Check if already inserted
        pos = content.index(anchor)
        nearby = content[pos:pos+300]
        if "'features.progress'" not in nearby:
            content = content.replace(anchor, anchor + '\n' + insertion, 1)
            count += 1
        else:
            print(f'Already exists near: {anchor[:50]}')
    else:
        print(f'NOT FOUND: {anchor[:70]}')

path.write_text(content, encoding='utf-8')
print(f'Done: {count}/18 languages updated')
