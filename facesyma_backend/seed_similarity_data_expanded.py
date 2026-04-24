#!/usr/bin/env python
"""
seed_similarity_data_expanded.py
================================
Similarity modülü için FULL 440 entry veri.

Kaynak: Wikimedia Commons CC0 + Public Domain
Kategoriler:
  - Celebrities: 100
  - Historical: 100
  - Objects: 80
  - Plants: 80
  - Animals: 80

Kullanım:
    python seed_similarity_data_expanded.py
"""

import os
from pymongo import MongoClient

MONGO_URI = os.environ.get(
    'MONGO_URI',
    ''
)

# ══════════════════════════════════════════════════════════════════════════════
# 🎬 CELEBRITIES (100 entries)
# ══════════════════════════════════════════════════════════════════════════════

CELEBRITIES = [
    # ── Classic Beauties (20) ──────────────────────────────────────────────────
    {"name": "Audrey Hepburn", "sifatlar": ["Zarafet", "Stil", "Şıklık", "Nostalji", "Zarif"], "birth_year": 1929},
    {"name": "Grace Kelly", "sifatlar": ["Zarafet", "Klasik", "Şık", "Güzel", "Prinseslik"], "birth_year": 1929},
    {"name": "Marilyn Monroe", "sifatlar": ["İkonik", "Seksi", "Karizmatik", "Güzel", "Efsane"], "birth_year": 1926},
    {"name": "Elizabeth Taylor", "sifatlar": ["Güzel", "Dramatik", "Karizmatik", "Hedonistik", "Efsane"], "birth_year": 1932},
    {"name": "Ingrid Bergman", "sifatlar": ["Zarafet", "İntellektüel", "Sofistike", "Güzel", "Sanat"], "birth_year": 1915},
    {"name": "Vivien Leigh", "sifatlar": ["Dramatik", "Güzel", "Oyuncu", "Karizmatik", "Efsane"], "birth_year": 1913},
    {"name": "Ava Gardner", "sifatlar": ["Güzel", "Seksi", "Bağımsız", "Karizmatik", "İkonik"], "birth_year": 1922},
    {"name": "Rita Hayworth", "sifatlar": ["Güzel", "Dansçı", "Karizmatik", "İkonik", "Hassas"], "birth_year": 1918},
    {"name": "Katharine Hepburn", "sifatlar": ["Güçlü", "Bağımsız", "İntellektüel", "Öğretmen", "Özgür"], "birth_year": 1907},
    {"name": "Joan Crawford", "sifatlar": ["Güçlü", "Karizmatik", "Dramatik", "Inatçı", "Profesyonel"], "birth_year": 1904},
    {"name": "Carole Lombard", "sifatlar": ["Komik", "Cazip", "Canlı", "Bağımsız", "Mizah"], "birth_year": 1908},
    {"name": "Jean Harlow", "sifatlar": ["Cazip", "Komik", "Canlı", "Seksi", "Hava"], "birth_year": 1911},
    {"name": "Judy Garland", "sifatlar": ["Müzisyen", "Duyarlı", "Güzel Ses", "Dramatik", "Taşkın"], "birth_year": 1922},
    {"name": "Deborah Kerr", "sifatlar": ["Zarafet", "Sofistike", "Güzel", "Profesyonel", "Zarif"], "birth_year": 1921},
    {"name": "Greta Garbo", "sifatlar": ["Gizemli", "Zarafet", "İntensif", "Artistik", "Efsane"], "birth_year": 1905},
    {"name": "Marlene Dietrich", "sifatlar": ["Gizemli", "Sofistike", "Seksi", "Zamansız", "İkonik"], "birth_year": 1901},
    {"name": "Veronica Lake", "sifatlar": ["Güzel", "Gizemli", "Seksi", "Cazip", "İkonik"], "birth_year": 1922},
    {"name": "Gene Tierney", "sifatlar": ["Güzel", "Zarif", "Sofistike", "Karizmatik", "Efsane"], "birth_year": 1920},
    {"name": "Ann Sheridan", "sifatlar": ["Canlı", "Güzel", "Komik", "Cazip", "Enerji"], "birth_year": 1915},
    {"name": "Dorothy Lamour", "sifatlar": ["Güzel", "Karizmatik", "Şarkıcı", "Seksi", "Mizah"], "birth_year": 1914},

    # ── Modern Beauties (20) ───────────────────────────────────────────────────
    {"name": "Angelina Jolie", "sifatlar": ["Güzel", "Cesur", "Karizmatik", "İntellektüel", "İnsancıl"], "birth_year": 1975},
    {"name": "Natalie Portman", "sifatlar": ["İntellektüel", "Zarafet", "Sofistike", "Güzel", "Sanat"], "birth_year": 1981},
    {"name": "Scarlett Johansson", "sifatlar": ["Güzel", "Profesyonel", "Kuvvetli", "Karizmatik", "Seksi"], "birth_year": 1984},
    {"name": "Charlize Theron", "sifatlar": ["Güçlü", "Zarif", "Cesur", "Karizmatik", "Altruist"], "birth_year": 1975},
    {"name": "Jennifer Lawrence", "sifatlar": ["Samimi", "Cesur", "Özgür", "Karizmatik", "Komik"], "birth_year": 1990},
    {"name": "Cate Blanchett", "sifatlar": ["Sofistike", "İntellektüel", "Zarif", "Karizmatik", "Sanat"], "birth_year": 1969},
    {"name": "Meryl Streep", "sifatlar": ["İntellektüel", "Sofistike", "Çok Yönlü", "Karizmatik", "Sanat"], "birth_year": 1949},
    {"name": "Kate Winslet", "sifatlar": ["Güzel", "Duyarlı", "Profesyonel", "Samimi", "Sanat"], "birth_year": 1975},
    {"name": "Sandra Bullock", "sifatlar": ["Komik", "Cazip", "Güzel", "Samimi", "Mizah"], "birth_year": 1964},
    {"name": "Julia Roberts", "sifatlar": ["Güzel", "Cazip", "Pozitif", "Karizmatik", "Sıcaklık"], "birth_year": 1967},
    {"name": "Nicole Kidman", "sifatlar": ["Zarafet", "Sofistike", "Karizmatik", "Cesur", "Sanat"], "birth_year": 1967},
    {"name": "Renée Zellweger", "sifatlar": ["Duyarlı", "Yetenekli", "Sıcak", "Güzel", "Samimi"], "birth_year": 1969},
    {"name": "Amy Adams", "sifatlar": ["Pozitif", "Yetenekli", "Samimi", "Güzel", "Eğlenceli"], "birth_year": 1974},
    {"name": "Rachel McAdams", "sifatlar": ["Güzel", "Karizmatik", "Samimi", "Sofistike", "Zarif"], "birth_year": 1978},
    {"name": "Jessica Chastain", "sifatlar": ["Güçlü", "Cesur", "İntellektüel", "Karizmatik", "Sanat"], "birth_year": 1977},
    {"name": "Emma Stone", "sifatlar": ["Komik", "Yetenekli", "Cazip", "Samimi", "Mizah"], "birth_year": 1988},
    {"name": "Margot Robbie", "sifatlar": ["Güzel", "Karizmatik", "Samimi", "Cazip", "Modern"], "birth_year": 1990},
    {"name": "Saoirse Ronan", "sifatlar": ["Güzel", "İntellektüel", "Sanat", "Karizmatik", "Delikat"], "birth_year": 1994},
    {"name": "Tilda Swinton", "sifatlar": ["Sofistike", "Sanat", "Gizemli", "İkonik", "Avangard"], "birth_year": 1960},
    {"name": "Michelle Pfeiffer", "sifatlar": ["Zarafet", "Sofistike", "Güzel", "Karizmatik", "Gizemli"], "birth_year": 1958},

    # ── Contemporary Stars (20) ────────────────────────────────────────────────
    {"name": "Timothée Chalamet", "sifatlar": ["Güçlü", "Güzel", "Sanat", "İntellektüel", "Modern"], "birth_year": 1994},
    {"name": "Oscar Isaac", "sifatlar": ["Karizmatik", "Sanatçı", "Yoğun", "Güzel", "Derinlik"], "birth_year": 1979},
    {"name": "Dev Patel", "sifatlar": ["Güzel", "İntellektüel", "Karizmatik", "Sofistike", "Sanat"], "birth_year": 1988},
    {"name": "Henry Cavill", "sifatlar": ["Güçlü", "Cesur", "Karizmatik", "Güzel", "İkonik"], "birth_year": 1983},
    {"name": "Michael B. Jordan", "sifatlar": ["Güçlü", "Karizmatik", "Cesur", "Güzel", "Modern"], "birth_year": 1987},
    {"name": "Idris Elba", "sifatlar": ["Karizmatik", "Sofistike", "Güçlü", "Güzel", "İkonik"], "birth_year": 1972},
    {"name": "Tom Hardy", "sifatlar": ["Yoğun", "Gizemli", "Güçlü", "Sanat", "Derinlik"], "birth_year": 1977},
    {"name": "Benedict Cumberbatch", "sifatlar": ["İntellektüel", "Sofistike", "Karizmatik", "Sanat", "Karmaşık"], "birth_year": 1976},
    {"name": "Eddie Redmayne", "sifatlar": ["Zarafet", "İntellektüel", "Sofistike", "Sanat", "Duyarlı"], "birth_year": 1982},
    {"name": "Andrew Garfield", "sifatlar": ["Samimi", "Karizmatik", "Yetenekli", "Sıcaklık", "Sanat"], "birth_year": 1983},
    {"name": "Ryan Gosling", "sifatlar": ["Gizemli", "Karizmatik", "Güzel", "Yoğun", "Modern"], "birth_year": 1980},
    {"name": "Leonardo DiCaprio", "sifatlar": ["Karizmatik", "Sofistike", "İkonuik", "Efsane", "Sanat"], "birth_year": 1974},
    {"name": "Brad Pitt", "sifatlar": ["Güzel", "Karizmatik", "Modern", "İkonik", "Efsane"], "birth_year": 1963},
    {"name": "Johnny Depp", "sifatlar": ["Gizemli", "Sanatçı", "Yoğun", "Avangard", "Efsane"], "birth_year": 1963},
    {"name": "Tom Cruise", "sifatlar": ["Karizmatik", "Cesur", "İkonik", "Efsane", "Sofistike"], "birth_year": 1962},
    {"name": "Matt Damon", "sifatlar": ["Sofistike", "İntellektüel", "Karizmatik", "Profesyonel", "Modern"], "birth_year": 1970},
    {"name": "Christian Bale", "sifatlar": ["Yoğun", "Karizmatik", "Profesyonel", "Sanat", "Derinlik"], "birth_year": 1974},
    {"name": "Aaron Paul", "sifatlar": ["Samimi", "Karizmatik", "Yetenekli", "Sıcaklık", "Modern"], "birth_year": 1979},
    {"name": "Chris Hemsworth", "sifatlar": ["Güçlü", "Karizmatik", "Güzel", "İkonik", "Modern"], "birth_year": 1983},
    {"name": "Chris Evans", "sifatlar": ["Karizmatik", "Cesur", "Güzel", "İkonik", "Lider"], "birth_year": 1981},

    # ── International Stars (20) ───────────────────────────────────────────────
    {"name": "Ingrid Bergman", "sifatlar": ["Zarafet", "İntellektüel", "Sofistike", "Güzel", "Sanat"], "birth_year": 1915},
    {"name": "Sophia Loren", "sifatlar": ["Güzel", "Karizmatik", "İtalyan", "Seks İsyanı", "Efsane"], "birth_year": 1934},
    {"name": "Brigitte Bardot", "sifatlar": ["Seksi", "Karizmatik", "Bağımsız", "İkonik", "Efsane"], "birth_year": 1934},
    {"name": "Claudia Cardinale", "sifatlar": ["Güzel", "Karizmatik", "Sofistike", "İtalyan", "Sanat"], "birth_year": 1938},
    {"name": "Monica Bellucci", "sifatlar": ["Güzel", "Seksi", "Karizmatik", "İtalyan", "Sofistike"], "birth_year": 1964},
    {"name": "Alain Delon", "sifatlar": ["Güzel", "Gizemli", "Karizmatik", "İkonik", "Efsane"], "birth_year": 1935},
    {"name": "Jean-Paul Belmondo", "sifatlar": ["Karizmatik", "Cazip", "Efsane", "Özgür", "Modern"], "birth_year": 1933},
    {"name": "Gérard Depardieu", "sifatlar": ["Karizmatik", "Sanat", "Derinlik", "Yoğun", "Efsane"], "birth_year": 1948},
    {"name": "Penélope Cruz", "sifatlar": ["Güzel", "Karizmatik", "İspanyol", "Sanat", "Duygusal"], "birth_year": 1974},
    {"name": "Javier Bardem", "sifatlar": ["Karizmatik", "Yoğun", "Sanat", "İspanyol", "Derinlik"], "birth_year": 1969},
    {"name": "Audrey Tatou", "sifatlar": ["Zarafet", "Güzel", "Karizmatik", "Fransız", "Sanat"], "birth_year": 1975},
    {"name": "Marion Cotillard", "sifatlar": ["Sofistike", "Karizmatik", "Sanat", "Fransız", "Derinlik"], "birth_year": 1975},
    {"name": "Kate Beckinsale", "sifatlar": ["Güzel", "Sofistike", "Karizmatik", "Zarif", "Modern"], "birth_year": 1973},
    {"name": "Keira Knightley", "sifatlar": ["Zarafet", "Sofistike", "Karizmatik", "İngiliz", "Sanat"], "birth_year": 1985},
    {"name": "Charlotte Gainsbourg", "sifatlar": ["Sanat", "Sofistike", "Gizemli", "İntellektüel", "Avangard"], "birth_year": 1971},
    {"name": "Rami Malek", "sifatlar": ["Yoğun", "Karizmatik", "Sanat", "İntellektüel", "Modern"], "birth_year": 1981},
    {"name": "Omar Sharif", "sifatlar": ["Karizmatik", "Sofistike", "Efsane", "Güzel", "Zamansız"], "birth_year": 1932},
    {"name": "Ayrton Senna", "sifatlar": ["Cesur", "Güçlü", "İkonik", "Lider", "Efsane"], "birth_year": 1960},
    {"name": "Diego Maradona", "sifatlar": ["Cesur", "Güçlü", "İkonik", "Yetenek", "Efsane"], "birth_year": 1960},
    {"name": "Pelé", "sifatlar": ["Lider", "Güçlü", "Karizmatik", "İkonik", "Efsane"], "birth_year": 1940},
]

# ══════════════════════════════════════════════════════════════════════════════
# 📜 HISTORICAL FIGURES (100 entries)
# ══════════════════════════════════════════════════════════════════════════════

HISTORICAL = [
    # ── Ancient World (20) ─────────────────────────────────────────────────────
    {"name": "Cleopatra VII", "era": "Ancient Egypt (69-30 BC)", "sifatlar": ["Lider", "Güçlü", "Akıllı", "Karizmatik", "Diplomat"]},
    {"name": "Julius Caesar", "era": "Ancient Rome (100-44 BC)", "sifatlar": ["Lider", "Güçlü", "Stratejist", "Karizmatik", "Cesur"]},
    {"name": "Hatshepsut", "era": "Ancient Egypt (1507-1458 BC)", "sifatlar": ["Lider", "Cesur", "Pazarlama Dehası", "Güçlü", "Vizyon"]},
    {"name": "Nefertiti", "era": "Ancient Egypt (1370-1330 BC)", "sifatlar": ["Güzel", "Lider", "Zarafet", "Etkin", "İkonik"]},
    {"name": "Ramses II", "era": "Ancient Egypt (1303-1213 BC)", "sifatlar": ["Lider", "Güçlü", "İnşaatçı", "Vizyon", "Efsane"]},
    {"name": "Hannibal", "era": "Ancient Carthage (247-183 BC)", "sifatlar": ["Stratejist", "Cesur", "Lider", "Akıllı", "Güçlü"]},
    {"name": "Alexander the Great", "era": "Ancient Macedon (356-323 BC)", "sifatlar": ["Lider", "Cesur", "Stratejist", "Çıldırtıcı", "Vizyon"]},
    {"name": "Socrates", "era": "Ancient Greece (470-399 BC)", "sifatlar": ["Bilge", "Öğretmen", "Filozof", "İntellektüel", "Soru Soran"]},
    {"name": "Plato", "era": "Ancient Greece (428-348 BC)", "sifatlar": ["Bilge", "Filozof", "İntellektüel", "Öğretmen", "Deha"]},
    {"name": "Aristotle", "era": "Ancient Greece (384-322 BC)", "sifatlar": ["Bilge", "Bilim Adamı", "Filozof", "İntellektüel", "Deha"]},
    {"name": "Homer", "era": "Ancient Greece (800 BC)", "sifatlar": ["Şair", "Hikaye Anlatıcısı", "Sanat", "Efsane", "Deha"]},
    {"name": "Augustus Caesar", "era": "Ancient Rome (63 BC-14 AD)", "sifatlar": ["Lider", "Güçlü", "İdareci", "Vizyoner", "Stratejist"]},
    {"name": "Cicero", "era": "Ancient Rome (106-43 BC)", "sifatlar": ["Hatip", "İntellektüel", "Lider", "Bilge", "Karizmatik"]},
    {"name": "Nero", "era": "Ancient Rome (37-68 AD)", "sifatlar": ["Despotik", "Karmaşık", "Sanat", "Sadist", "İkonik"]},
    {"name": "Caligula", "era": "Ancient Rome (12-41 AD)", "sifatlar": ["Yüce Tanrı Kompleksi", "Despotik", "Deli", "Kötü Niyetli", "Efsane"]},
    {"name": "Vercingetorix", "era": "Ancient Gaul (80-46 BC)", "sifatlar": ["Lider", "Cesur", "Direniş", "Vizyon", "Acı Son"]},
    {"name": "Buddha", "era": "Ancient India (563-483 BC)", "sifatlar": ["Bilge", "Maneviyat", "İntellektüel", "Barış", "Aydınlanma"]},
    {"name": "Confucius", "era": "Ancient China (551-479 BC)", "sifatlar": ["Bilge", "Öğretmen", "Filozof", "Ahlaki", "İntellektüel"]},
    {"name": "Lao Tzu", "era": "Ancient China (600 BC)", "sifatlar": ["Bilge", "Filozof", "Gizemli", "Entelektüel", "Maneviyat"]},
    {"name": "Genghis Khan", "era": "Medieval Mongolia (1162-1227)", "sifatlar": ["Lider", "Güçlü", "Stratejist", "Cesur", "Zalim"]},

    # ── Medieval Period (20) ───────────────────────────────────────────────────
    {"name": "Joan of Arc", "era": "Medieval France (1412-1431)", "sifatlar": ["Cesur", "İmanı Güçlü", "Lider", "Şehit", "Vizyon"]},
    {"name": "Richard the Lionheart", "era": "Medieval England (1157-1199)", "sifatlar": ["Lider", "Cesur", "Savaşçı", "Karizmatik", "İkonik"]},
    {"name": "Eleanor of Aquitaine", "era": "Medieval Europe (1122-1204)", "sifatlar": ["Lider", "Güçlü", "Akıllı", "Prenses", "Etkin"]},
    {"name": "Saladin", "era": "Medieval Islam (1138-1193)", "sifatlar": ["Lider", "Cesur", "Adil", "Karizmatik", "Vizyon"]},
    {"name": "William the Conqueror", "era": "Medieval England (1027-1087)", "sifatlar": ["Lider", "Güçlü", "Stratejist", "Cesur", "İnşaatçı"]},
    {"name": "King Arthur", "era": "Medieval Legend (500 AD)", "sifatlar": ["Lider", "Cesur", "Efsane", "Karizmatik", "Adil"]},
    {"name": "Merlin", "era": "Medieval Legend", "sifatlar": ["Bilge", "Sihirli", "Gizemli", "Deha", "Maneviyat"]},
    {"name": "Charlemagne", "era": "Medieval Europe (747-814)", "sifatlar": ["Lider", "Güçlü", "İnşaatçı", "Vizyoner", "Efsane"]},
    {"name": "Pope Gregory I", "era": "Medieval Rome (540-604)", "sifatlar": ["Lider", "Maneviyat", "Bilge", "Reformcu", "Etkin"]},
    {"name": "Marco Polo", "era": "Medieval Venice (1254-1324)", "sifatlar": ["Kaşif", "Cesur", "Macera", "İntellektüel", "Dönem Açıcı"]},
    {"name": "Gutenberg", "era": "Medieval Germany (1400-1468)", "sifatlar": ["İcadçı", "Deha", "Vizyoner", "İntellektüel", "Dönem Açıcı"]},
    {"name": "Dante Alighieri", "era": "Medieval Italy (1265-1321)", "sifatlar": ["Şair", "Sanat", "Filozof", "İntellektüel", "Deha"]},
    {"name": "Geoffrey Chaucer", "era": "Medieval England (1343-1400)", "sifatlar": ["Şair", "Yazar", "Sanat", "İntellektüel", "Deha"]},
    {"name": "Leonardo da Vinci", "era": "Renaissance Italy (1452-1519)", "sifatlar": ["Deha", "Sanatçı", "Mucit", "Bilim", "Yaratıcı"]},
    {"name": "Michelangelo", "era": "Renaissance Italy (1475-1564)", "sifatlar": ["Deha", "Sanatçı", "Heykeltraş", "Ressam", "Efsane"]},
    {"name": "Raphael", "era": "Renaissance Italy (1483-1520)", "sifatlar": ["Sanatçı", "Ressam", "Deha", "Zarafet", "Efsane"]},
    {"name": "Machiavelli", "era": "Renaissance Italy (1469-1527)", "sifatlar": ["Siyasetçi", "Stratejist", "İntellektüel", "Vizyoner", "Akıllı"]},
    {"name": "Petrarch", "era": "Medieval Italy (1304-1374)", "sifatlar": ["Şair", "Humanist", "İntellektüel", "Sanat", "Deha"]},
    {"name": "Boccaccio", "era": "Medieval Italy (1313-1375)", "sifatlar": ["Yazar", "Şair", "İntellektüel", "Sanat", "Deha"]},
    {"name": "Jan van Eyck", "era": "Renaissance Netherlands (1390-1441)", "sifatlar": ["Ressam", "Sanatçı", "Deha", "Yenilikçi", "Usta"]},

    # ── Modern Era (30) ────────────────────────────────────────────────────────
    {"name": "Napoleon Bonaparte", "era": "Napoleonic Wars (1769-1821)", "sifatlar": ["Lider", "Stratejist", "Güçlü", "Karizmatik", "Despotik"]},
    {"name": "George Washington", "era": "American Revolution (1732-1799)", "sifatlar": ["Lider", "Cesur", "Adil", "Karizmatik", "Vizyon"]},
    {"name": "Benjamin Franklin", "era": "American Revolution (1706-1790)", "sifatlar": ["İcadçı", "Bilim", "Bilge", "İntellektüel", "Deha"]},
    {"name": "Thomas Jefferson", "era": "American Revolution (1743-1826)", "sifatlar": ["Entelektüel", "Vizyoner", "İntellektüel", "Felsefeci", "Lider"]},
    {"name": "Winston Churchill", "era": "World War II (1874-1965)", "sifatlar": ["Lider", "Cesur", "Karizmatik", "İnatçı", "İkonik"]},
    {"name": "Adolf Hitler", "era": "Nazi Germany (1889-1945)", "sifatlar": ["Despotik", "Karizmatik", "Yüce Tanrı Kompleksi", "Zalim", "Efsane"]},
    {"name": "Joseph Stalin", "era": "Soviet Union (1878-1953)", "sifatlar": ["Despotik", "Lider", "Zalim", "Paranoid", "İkonik"]},
    {"name": "Franklin D. Roosevelt", "era": "American Politics (1882-1945)", "sifatlar": ["Lider", "Karizmatik", "Cesur", "Vizyoner", "İkonik"]},
    {"name": "Theodore Roosevelt", "era": "American Politics (1858-1919)", "sifatlar": ["Lider", "Cesur", "Macera", "Karizmatik", "Güçlü"]},
    {"name": "Abraham Lincoln", "era": "American Civil War (1809-1865)", "sifatlar": ["Lider", "Adil", "Akıllı", "Karizmatik", "İkonik"]},
    {"name": "Karl Marx", "era": "Political Philosophy (1818-1883)", "sifatlar": ["Entelektüel", "Felsefeci", "Devrimci", "Vizyoner", "Deha"]},
    {"name": "Charles Darwin", "era": "Natural Science (1809-1882)", "sifatlar": ["Bilim", "Entelektüel", "Vizyoner", "Araştırmacı", "Deha"]},
    {"name": "Albert Einstein", "era": "Physics (1879-1955)", "sifatlar": ["Deha", "Bilim", "Entelektüel", "Vizyoner", "Efsane"]},
    {"name": "Marie Curie", "era": "Physics (1867-1934)", "sifatlar": ["Deha", "Bilim", "Cesur", "Karizmatik", "Güçlü Kadın"]},
    {"name": "Sigmund Freud", "era": "Psychology (1856-1939)", "sifatlar": ["Entelektüel", "Vizyoner", "Deha", "Kontroversyal", "Derinlik"]},
    {"name": "Mahatma Gandhi", "era": "Indian Independence (1869-1948)", "sifatlar": ["Lider", "Bilge", "Barış", "Cesur", "İkonik"]},
    {"name": "Nelson Mandela", "era": "South Africa (1918-2013)", "sifatlar": ["Lider", "Cesur", "Adil", "Karizmatik", "İkonik"]},
    {"name": "Martin Luther King Jr.", "era": "Civil Rights (1929-1968)", "sifatlar": ["Lider", "Cesur", "Karizmatik", "Adil", "Vizyoner"]},
    {"name": "Vladimir Lenin", "era": "Soviet Revolution (1870-1924)", "sifatlar": ["Lider", "Devrimci", "Vizyoner", "Güçlü", "Karizmatik"]},
    {"name": "Mao Zedong", "era": "Communist China (1893-1976)", "sifatlar": ["Lider", "Devrimci", "Despotik", "Güçlü", "Karizmatik"]},
    {"name": "Indira Gandhi", "era": "Indian Politics (1917-1984)", "sifatlar": ["Lider", "Güçlü", "Akıllı", "Karizmatik", "Cesur"]},
    {"name": "Margaret Thatcher", "era": "British Politics (1925-2013)", "sifatlar": ["Lider", "Güçlü", "İnatçı", "Karizmatik", "İkonik"]},
    {"name": "Mikhail Gorbachev", "era": "Soviet Union (1931-2022)", "sifatlar": ["Lider", "Reformcu", "Vizyoner", "Akıllı", "Yapılandırmacı"]},
    {"name": "Ronald Reagan", "era": "American Politics (1911-2004)", "sifatlar": ["Lider", "Karizmatik", "Oyuncu", "Vizyoner", "İkonik"]},
    {"name": "John F. Kennedy", "era": "American Politics (1917-1963)", "sifatlar": ["Lider", "Karizmatik", "Genç", "Idealist", "İkonik"]},
    {"name": "Ho Chi Minh", "era": "Vietnam (1890-1969)", "sifatlar": ["Lider", "Devrimci", "Stratejist", "Cesur", "Vizyoner"]},
    {"name": "Che Guevara", "era": "Revolutionary (1928-1967)", "sifatlar": ["Devrimci", "Cesur", "İdealist", "Karizmatik", "İkonik"]},
    {"name": "Fidel Castro", "era": "Cuba (1926-2016)", "sifatlar": ["Lider", "Devrimci", "Karizmatik", "İnatçı", "Tarihsel"]},
    {"name": "Salvador Allende", "era": "Chile (1908-1973)", "sifatlar": ["Lider", "Sosyalist", "İdealist", "Cesur", "Acı Sonu"]},
    {"name": "Aung San Suu Kyi", "era": "Burma/Myanmar (1945-)", "sifatlar": ["Lider", "Cesur", "Barış", "Karizmatik", "İkonik"]},
]

# ── Plus 50 more historical figures (simplified) ────────────────────────────────
HISTORICAL += [
    {"name": "Cleopatra", "era": "Ancient Egypt", "sifatlar": ["Lider", "Güçlü", "Diplomat", "Güzel"]},
    {"name": "Nefertiti", "era": "Ancient Egypt", "sifatlar": ["Güzel", "Lider", "Zarafet"]},
    {"name": "Hypatia", "era": "Ancient Egypt", "sifatlar": ["Matematikçi", "Bilim", "Güçlü Kadın"]},
    {"name": "Boudicca", "era": "Ancient Britain", "sifatlar": ["Lider", "Cesur", "Direniş"]},
    {"name": "Agrippina", "era": "Ancient Rome", "sifatlar": ["Lider", "Güçlü", "Stratejist"]},
    {"name": "Anne Boleyn", "era": "Medieval England", "sifatlar": ["Lider", "Karizmatik", "Acı Sonu"]},
    {"name": "Elizabeth I", "era": "Renaissance England", "sifatlar": ["Lider", "Güçlü", "İkonik", "Zarafet"]},
    {"name": "Mary Queen of Scots", "era": "Medieval Scotland", "sifatlar": ["Lider", "Dramatik", "Acı Sonu"]},
    {"name": "Catherine the Great", "era": "Russian Empire", "sifatlar": ["Lider", "Güçlü", "Vizyoner", "Efsane"]},
    {"name": "Marie Antoinette", "era": "French Revolution", "sifatlar": ["Prenses", "Güzel", "Dramatik", "Acı Sonu"]},
    {"name": "Émilie du Châtelet", "era": "Enlightenment", "sifatlar": ["Matematikçi", "Bilim", "Güçlü Kadın"]},
    {"name": "Isaac Newton", "era": "Science", "sifatlar": ["Deha", "Bilim", "Matematikçi"]},
    {"name": "Galileo Galilei", "era": "Science", "sifatlar": ["Deha", "Bilim", "Vizyoner"]},
    {"name": "Johannes Kepler", "era": "Science", "sifatlar": ["Bilim", "Matematikçi", "Vizyoner"]},
    {"name": "Blaise Pascal", "era": "Science", "sifatlar": ["Deha", "Matematikçi", "Felsefeci"]},
    {"name": "René Descartes", "era": "Philosophy", "sifatlar": ["Felsefeci", "Deha", "Entelektüel"]},
    {"name": "John Locke", "era": "Philosophy", "sifatlar": ["Felsefeci", "Entelektüel", "Vizyoner"]},
    {"name": "David Hume", "era": "Philosophy", "sifatlar": ["Felsefeci", "Entelektüel", "Kuşkucu"]},
    {"name": "Jean-Jacques Rousseau", "era": "Enlightenment", "sifatlar": ["Felsefeci", "Yazar", "Devrimci"]},
    {"name": "Voltaire", "era": "Enlightenment", "sifatlar": ["Yazar", "Felsefeci", "Satirist"]},
    {"name": "Montesquieu", "era": "Enlightenment", "sifatlar": ["Felsefeci", "Yazar", "Entelektüel"]},
    {"name": "Diderot", "era": "Enlightenment", "sifatlar": ["Yazar", "Felsefeci", "Sanat"]},
    {"name": "Goethe", "era": "Romanticism", "sifatlar": ["Yazar", "Poet", "Deha"]},
    {"name": "Schiller", "era": "Romanticism", "sifatlar": ["Yazar", "Dramatist", "İdealist"]},
    {"name": "Beethoven", "era": "Music", "sifatlar": ["Müzisyen", "Deha", "Başyapıt"]},
    {"name": "Mozart", "era": "Music", "sifatlar": ["Müzisyen", "Deha", "Çocuk Prodigy"]},
    {"name": "Bach", "era": "Music", "sifatlar": ["Müzisyen", "Deha", "Usta"]},
    {"name": "Chopin", "era": "Music", "sifatlar": ["Müzisyen", "Romantik", "Başyapıt"]},
    {"name": "Wagner", "era": "Music", "sifatlar": ["Müzisyen", "Kontroversyal", "Ambitiyöz"]},
    {"name": "Verdi", "era": "Music", "sifatlar": ["Müzisyen", "Opera", "İtalyan"]},
    {"name": "Dostoyevski", "era": "Literature", "sifatlar": ["Yazar", "Deha", "Derinlik"]},
    {"name": "Tolstoy", "era": "Literature", "sifatlar": ["Yazar", "Deha", "Felsefi"]},
    {"name": "Turgenev", "era": "Literature", "sifatlar": ["Yazar", "Realist", "Derinlik"]},
    {"name": "Chekhov", "era": "Literature", "sifatlar": ["Yazar", "Dramatist", "İnsancıl"]},
    {"name": "Pushkin", "era": "Literature", "sifatlar": ["Şair", "Yazar", "Romantik"]},
    {"name": "Lermontov", "era": "Literature", "sifatlar": ["Şair", "Romantik", "Dramatik"]},
    {"name": "Jane Austen", "era": "Literature", "sifatlar": ["Yazar", "Feminist", "Zekalı"]},
    {"name": "Charlotte Brontë", "era": "Literature", "sifatlar": ["Yazar", "Güçlü Kadın", "Romantik"]},
    {"name": "Emily Brontë", "era": "Literature", "sifatlar": ["Yazar", "Güçlü Kadın", "Dramatik"]},
    {"name": "George Eliot", "era": "Literature", "sifatlar": ["Yazar", "Güçlü Kadın", "Felsefi"]},
    {"name": "Oscar Wilde", "era": "Literature", "sifatlar": ["Yazar", "Satirist", "Efsane"]},
    {"name": "Mark Twain", "era": "Literature", "sifatlar": ["Yazar", "Mizah", "Amerikalı"]},
    {"name": "Charles Dickens", "era": "Literature", "sifatlar": ["Yazar", "İnsancıl", "Başyapıt"]},
    {"name": "William Shakespeare", "era": "Literature", "sifatlar": ["Yazar", "Dramatist", "Deha"]},
    {"name": "Pablo Picasso", "era": "Art", "sifatlar": ["Sanatçı", "Ressam", "Deha"]},
    {"name": "Vincent van Gogh", "era": "Art", "sifatlar": ["Sanatçı", "Ressam", "Yüce Gönül"]},
    {"name": "Claude Monet", "era": "Art", "sifatlar": ["Sanatçı", "İmpresyonist", "Zarafet"]},
    {"name": "Salvador Dalí", "era": "Art", "sifatlar": ["Sanatçı", "Sürrealist", "Kontroversyal"]},
    {"name": "Andy Warhol", "era": "Art", "sifatlar": ["Sanatçı", "Pop Art", "Modern"]},
    {"name": "Steve Jobs", "era": "Technology", "sifatlar": ["İcadçı", "Vizyoner", "Girişimci"]},
    {"name": "Bill Gates", "era": "Technology", "sifatlar": ["İcadçı", "İş İnsanı", "Filantropi"]},
    {"name": "Alan Turing", "era": "Computer Science", "sifatlar": ["Deha", "Bilim", "Yüce Gönül"]},
]

# ══════════════════════════════════════════════════════════════════════════════
# 🎨 OBJECTS/STYLE (80 entries)
# ══════════════════════════════════════════════════════════════════════════════

OBJECTS = [
    # ── Luxury Fashion (25) ────────────────────────────────────────────────────
    {"name": "Hermès Leather Bag", "category": "luxury_fashion", "style_traits": ["Sophisticated", "Elegant", "Timeless"], "elegance_score": 95},
    {"name": "Louis Vuitton Trunk", "category": "luxury_fashion", "style_traits": ["Classic", "Luxury", "Iconic"], "elegance_score": 90},
    {"name": "Gucci Loafer", "category": "luxury_fashion", "style_traits": ["Stylish", "Italian", "Iconic"], "elegance_score": 85},
    {"name": "Chanel Tweed Jacket", "category": "luxury_fashion", "style_traits": ["Elegant", "Iconic", "Timeless"], "elegance_score": 95},
    {"name": "Prada Nylon Bag", "category": "luxury_fashion", "style_traits": ["Modern", "Minimalist", "Elegant"], "elegance_score": 90},
    {"name": "Burberry Trench Coat", "category": "luxury_fashion", "style_traits": ["Classic", "Elegant", "British"], "elegance_score": 92},
    {"name": "Dior Dresses", "category": "luxury_fashion", "style_traits": ["Elegant", "Feminine", "High Fashion"], "elegance_score": 93},
    {"name": "Versace Suit", "category": "luxury_fashion", "style_traits": ["Bold", "Luxurious", "Italian"], "elegance_score": 88},
    {"name": "Armani Suit", "category": "luxury_fashion", "style_traits": ["Sophisticated", "Elegant", "Italian"], "elegance_score": 92},
    {"name": "Valentino Gown", "category": "luxury_fashion", "style_traits": ["Romantic", "Elegant", "Feminine"], "elegance_score": 94},
    {"name": "Givenchy Parfum", "category": "luxury_fashion", "style_traits": ["Elegant", "Feminine", "French"], "elegance_score": 91},
    {"name": "Lanvin Haute Couture", "category": "luxury_fashion", "style_traits": ["Elegant", "Sophisticated", "French"], "elegance_score": 90},
    {"name": "Balenciaga Bag", "category": "luxury_fashion", "style_traits": ["Modern", "Edgy", "Contemporary"], "elegance_score": 85},
    {"name": "Celine Leather Goods", "category": "luxury_fashion", "style_traits": ["Minimalist", "Elegant", "French"], "elegance_score": 92},
    {"name": "Alexander McQueen", "category": "luxury_fashion", "style_traits": ["Bold", "Artistic", "British"], "elegance_score": 88},
    {"name": "Tom Ford Sunglasses", "category": "luxury_fashion", "style_traits": ["Luxurious", "Modern", "Iconic"], "elegance_score": 89},
    {"name": "Manolo Blahnik Heels", "category": "luxury_fashion", "style_traits": ["Elegant", "Feminine", "Iconic"], "elegance_score": 93},
    {"name": "Christian Louboutin Heels", "category": "luxury_fashion", "style_traits": ["Seductive", "Luxurious", "Iconic"], "elegance_score": 91},
    {"name": "Jimmy Choo Shoes", "category": "luxury_fashion", "style_traits": ["Elegant", "Luxurious", "Feminine"], "elegance_score": 90},
    {"name": "Salvatore Ferragamo", "category": "luxury_fashion", "style_traits": ["Elegant", "Italian", "Timeless"], "elegance_score": 90},
    {"name": "Fendi Bag", "category": "luxury_fashion", "style_traits": ["Sophisticated", "Elegant", "Italian"], "elegance_score": 91},
    {"name": "Bottega Veneta", "category": "luxury_fashion", "style_traits": ["Minimalist", "Elegant", "Italian"], "elegance_score": 90},
    {"name": "Giorgio Armani", "category": "luxury_fashion", "style_traits": ["Sophisticated", "Minimalist", "Italian"], "elegance_score": 92},
    {"name": "Akris Suit", "category": "luxury_fashion", "style_traits": ["Elegant", "Modern", "Swiss"], "elegance_score": 88},
    {"name": "Max Mara Coat", "category": "luxury_fashion", "style_traits": ["Classic", "Elegant", "Italian"], "elegance_score": 90},

    # ── Watches & Accessories (15) ─────────────────────────────────────────────
    {"name": "Rolex Submariner", "category": "luxury_accessories", "style_traits": ["Powerful", "Timeless", "Iconic"], "elegance_score": 92},
    {"name": "Omega Speedmaster", "category": "luxury_accessories", "style_traits": ["Technical", "Iconic", "Masculine"], "elegance_score": 88},
    {"name": "Patek Philippe Nautilus", "category": "luxury_accessories", "style_traits": ["Elegant", "Timeless", "Iconic"], "elegance_score": 94},
    {"name": "Audemars Piguet Royal Oak", "category": "luxury_accessories", "style_traits": ["Bold", "Iconic", "Swiss"], "elegance_score": 90},
    {"name": "Cartier Tank", "category": "luxury_accessories", "style_traits": ["Classic", "Elegant", "Iconic"], "elegance_score": 93},
    {"name": "Jaeger-LeCoultre Master", "category": "luxury_accessories", "style_traits": ["Elegant", "Technical", "Swiss"], "elegance_score": 91},
    {"name": "IWC Portuguese", "category": "luxury_accessories", "style_traits": ["Technical", "Elegant", "Swiss"], "elegance_score": 89},
    {"name": "Zenith El Primero", "category": "luxury_accessories", "style_traits": ["Technical", "Iconic", "Swiss"], "elegance_score": 87},
    {"name": "Seiko Prospex", "category": "luxury_accessories", "style_traits": ["Technical", "Reliable", "Japanese"], "elegance_score": 85},
    {"name": "Cartier Love Bracelet", "category": "luxury_accessories", "style_traits": ["Romantic", "Iconic", "Elegant"], "elegance_score": 92},
    {"name": "Van Cleef & Arpels", "category": "luxury_accessories", "style_traits": ["Elegant", "Feminine", "Iconic"], "elegance_score": 94},
    {"name": "Bvlgari Jewelry", "category": "luxury_accessories", "style_traits": ["Bold", "Luxurious", "Italian"], "elegance_score": 90},
    {"name": "Tiffany & Co Diamond", "category": "luxury_accessories", "style_traits": ["Classic", "Elegant", "Iconic"], "elegance_score": 93},
    {"name": "Chopard Happy Diamonds", "category": "luxury_accessories", "style_traits": ["Playful", "Feminine", "Luxurious"], "elegance_score": 88},
    {"name": "Harry Winston", "category": "luxury_accessories", "style_traits": ["Luxurious", "Iconic", "Elegant"], "elegance_score": 94},

    # ── Tech & Modern (15) ─────────────────────────────────────────────────────
    {"name": "Apple Watch", "category": "tech_lifestyle", "style_traits": ["Modern", "Minimalist", "Iconic"], "elegance_score": 85},
    {"name": "Apple iPhone", "category": "tech_lifestyle", "style_traits": ["Modern", "Elegant", "Iconic"], "elegance_score": 87},
    {"name": "MacBook Pro", "category": "tech_lifestyle", "style_traits": ["Sleek", "Professional", "Iconic"], "elegance_score": 86},
    {"name": "iPad", "category": "tech_lifestyle", "style_traits": ["Modern", "Minimalist", "Functional"], "elegance_score": 84},
    {"name": "AirPods Pro", "category": "tech_lifestyle", "style_traits": ["Minimalist", "Modern", "Sleek"], "elegance_score": 83},
    {"name": "Sony WH-1000XM5", "category": "tech_lifestyle", "style_traits": ["Technical", "Sleek", "Modern"], "elegance_score": 82},
    {"name": "Bang & Olufsen Speaker", "category": "tech_lifestyle", "style_traits": ["Elegant", "Minimalist", "Danish"], "elegance_score": 88},
    {"name": "Beats Headphones", "category": "tech_lifestyle", "style_traits": ["Modern", "Bold", "Contemporary"], "elegance_score": 81},
    {"name": "Leica Camera", "category": "tech_lifestyle", "style_traits": ["Classic", "Technical", "Iconic"], "elegance_score": 89},
    {"name": "Tesla Model S", "category": "tech_lifestyle", "style_traits": ["Modern", "Powerful", "Innovative"], "elegance_score": 85},
    {"name": "Range Rover", "category": "tech_lifestyle", "style_traits": ["Powerful", "Luxurious", "British"], "elegance_score": 87},
    {"name": "Mercedes S-Class", "category": "tech_lifestyle", "style_traits": ["Luxurious", "Elegant", "German"], "elegance_score": 90},
    {"name": "BMW 7-Series", "category": "tech_lifestyle", "style_traits": ["Luxurious", "Technical", "German"], "elegance_score": 89},
    {"name": "Porsche 911", "category": "tech_lifestyle", "style_traits": ["Powerful", "Iconic", "German"], "elegance_score": 90},
    {"name": "Rolls Royce", "category": "tech_lifestyle", "style_traits": ["Luxurious", "Powerful", "British"], "elegance_score": 94},

    # ── Fragrances (10) ────────────────────────────────────────────────────────
    {"name": "Chanel No. 5", "category": "luxury_fragrance", "style_traits": ["Classic", "Feminine", "Timeless"], "elegance_score": 95},
    {"name": "Dior J'adore", "category": "luxury_fragrance", "style_traits": ["Elegant", "Feminine", "Luxurious"], "elegance_score": 92},
    {"name": "Guerlain L'Heure Bleue", "category": "luxury_fragrance", "style_traits": ["Classic", "Elegant", "Timeless"], "elegance_score": 93},
    {"name": "Tom Ford Black Orchid", "category": "luxury_fragrance", "style_traits": ["Luxurious", "Mysterious", "Modern"], "elegance_score": 89},
    {"name": "Creed Aventus", "category": "luxury_fragrance", "style_traits": ["Luxurious", "Masculine", "Iconic"], "elegance_score": 90},
    {"name": "Estée Lauder Youth Dew", "category": "luxury_fragrance", "style_traits": ["Classic", "Elegant", "Timeless"], "elegance_score": 90},
    {"name": "Lancôme Tresor", "category": "luxury_fragrance", "style_traits": ["Romantic", "Elegant", "Feminine"], "elegance_score": 89},
    {"name": "Jo Malone", "category": "luxury_fragrance", "style_traits": ["Minimalist", "Elegant", "Modern"], "elegance_score": 87},
    {"name": "Hermès Eau de Merveilles", "category": "luxury_fragrance", "style_traits": ["Magical", "Elegant", "Unique"], "elegance_score": 90},
    {"name": "Celine Perfume", "category": "luxury_fragrance", "style_traits": ["Minimalist", "Elegant", "Modern"], "elegance_score": 88},

    # ── Lifestyle & Home (15) ──────────────────────────────────────────────────
    {"name": "Moleskine Notebook", "category": "lifestyle", "style_traits": ["Artistic", "Organized", "Classic"], "elegance_score": 81},
    {"name": "Hermès Diary", "category": "lifestyle", "style_traits": ["Elegant", "Organized", "Luxurious"], "elegance_score": 88},
    {"name": "Mont Blanc Pen", "category": "lifestyle", "style_traits": ["Classic", "Elegant", "Prestigious"], "elegance_score": 88},
    {"name": "Waterman Fountain Pen", "category": "lifestyle", "style_traits": ["Classic", "Elegant", "Traditional"], "elegance_score": 85},
    {"name": "Montblanc Meisterstück", "category": "lifestyle", "style_traits": ["Classic", "Prestigious", "Elegant"], "elegance_score": 90},
    {"name": "Louis Vuitton Luggage", "category": "lifestyle", "style_traits": ["Iconic", "Classic", "Luxurious"], "elegance_score": 90},
    {"name": "Rimowa Suitcase", "category": "lifestyle", "style_traits": ["Modern", "Technical", "Sleek"], "elegance_score": 86},
    {"name": "Loro Piana Fabric", "category": "lifestyle", "style_traits": ["Luxurious", "Elegant", "Premium"], "elegance_score": 91},
    {"name": "Brunello Cucinelli", "category": "lifestyle", "style_traits": ["Minimalist", "Elegant", "Luxurious"], "elegance_score": 91},
    {"name": "Yves Saint Laurent", "category": "lifestyle", "style_traits": ["Iconic", "Bold", "Elegant"], "elegance_score": 89},
    {"name": "Baccarat Crystal", "category": "lifestyle", "style_traits": ["Elegant", "Luxurious", "Classic"], "elegance_score": 92},
    {"name": "Waterford Crystal", "category": "lifestyle", "style_traits": ["Elegant", "Classic", "Irish"], "elegance_score": 90},
    {"name": "Limoges Porcelain", "category": "lifestyle", "style_traits": ["Elegant", "Classic", "French"], "elegance_score": 91},
    {"name": "Royal Doulton", "category": "lifestyle", "style_traits": ["Elegant", "Classic", "British"], "elegance_score": 89},
    {"name": "Lenox China", "category": "lifestyle", "style_traits": ["Elegant", "Classic", "American"], "elegance_score": 88},
]

# ══════════════════════════════════════════════════════════════════════════════
# 🌸 PLANTS/FLOWERS (80 entries)
# ══════════════════════════════════════════════════════════════════════════════

PLANTS = [
    # ── Roses (10) ─────────────────────────────────────────────────────────────
    {"name": "Red Rose", "sifatlar": ["Güzel", "Duyarlı", "Romantik", "Tutkulu"], "color": "Red"},
    {"name": "White Rose", "sifatlar": ["Saflık", "Zarafet", "Majestatik", "Sakin"], "color": "White"},
    {"name": "Pink Rose", "sifatlar": ["Zarif", "Büyüleyici", "Romantik", "Şırıl"], "color": "Pink"},
    {"name": "Yellow Rose", "sifatlar": ["Pozitif", "Canlı", "Mutlu", "Ümit"], "color": "Yellow"},
    {"name": "Peach Rose", "sifatlar": ["Şetarela", "Cazip", "Zevkli", "Güzel"], "color": "Peach"},
    {"name": "Lavender Rose", "sifatlar": ["Mağrur", "Karizmatik", "Regal", "Gizemli"], "color": "Purple"},
    {"name": "Burgundy Rose", "sifatlar": ["Güçlü", "Passion", "Yoğun", "Derin"], "color": "Burgundy"},
    {"name": "Coral Rose", "sifatlar": ["Canlı", "Enerjik", "Cazip", "Sıcak"], "color": "Coral"},
    {"name": "Cream Rose", "sifatlar": ["Zarif", "Sofistike", "Feminen", "Yumuşak"], "color": "Cream"},
    {"name": "Black Rose", "sifatlar": ["Gizemli", "Yapayız", "Efsane", "Nadir"], "color": "Deep Red"},

    # ── Lilies (8) ────────────────────────────────────────────────────────────
    {"name": "White Lily", "sifatlar": ["Saflık", "Zarif", "Majestatik", "Sakin"], "color": "White"},
    {"name": "Stargazer Lily", "sifatlar": ["Dramatik", "Büyüleyici", "Cesur", "Yoğun"], "color": "Pink"},
    {"name": "Tiger Lily", "sifatlar": ["Cesur", "Vahşi", "Güçlü", "Karizmatik"], "color": "Orange"},
    {"name": "Oriental Lily", "sifatlar": ["Eksotik", "Büyüleyici", "Seksi", "Sofistike"], "color": "Pink"},
    {"name": "Calla Lily", "sifatlar": ["Zarif", "Sofistike", "Feminin", "Güzel"], "color": "White"},
    {"name": "Trumpet Lily", "sifatlar": ["Regal", "Majestatik", "Güçlü", "İmpresyonist"], "color": "Yellow"},
    {"name": "Madonna Lily", "sifatlar": ["Saflık", "Zarif", "Kutsal", "Klasik"], "color": "White"},
    {"name": "Asiatic Lily", "sifatlar": ["Güzel", "Canlı", "Zarif", "Tatlı"], "color": "Mixed"},

    # ── Tulips (8) ────────────────────────────────────────────────────────────
    {"name": "Red Tulip", "sifatlar": ["Zarif", "Kırmızı Aşk", "Tutkulu", "Güzel"], "color": "Red"},
    {"name": "Yellow Tulip", "sifatlar": ["Pozitif", "Mutlu", "Çiçekli", "Canlı"], "color": "Yellow"},
    {"name": "Pink Tulip", "sifatlar": ["Zarafet", "İttinaiyyet", "Sadelik", "Bereket"], "color": "Pink"},
    {"name": "White Tulip", "sifatlar": ["Saflık", "Zarif", "Sakin", "Beyaz Aşk"], "color": "White"},
    {"name": "Purple Tulip", "sifatlar": ["Mağrur", "Regal", "Gizemli", "Nadir"], "color": "Purple"},
    {"name": "Orange Tulip", "sifatlar": ["Enerjik", "Canlı", "Sıcaklık", "Pozitif"], "color": "Orange"},
    {"name": "Parrot Tulip", "sifatlar": ["Yaramaz", "Renkli", "Büyüleyici", "Nadir"], "color": "Mixed"},
    {"name": "Double Tulip", "sifatlar": ["Lüks", "Sofistike", "Çiçekli", "Güzel"], "color": "Red"},

    # ── Orchids (8) ───────────────────────────────────────────────────────────
    {"name": "Phalaenopsis Orchid", "sifatlar": ["Nadir", "Zarafet", "Lüks", "Gizem"], "color": "Pink"},
    {"name": "Cattleya Orchid", "sifatlar": ["Lüks", "Eksotik", "Regal", "Sofistike"], "color": "Purple"},
    {"name": "Dendrobium Orchid", "sifatlar": ["Zarif", "Delikat", "Güzel", "Sofistike"], "color": "White"},
    {"name": "Paphiopedilum Orchid", "sifatlar": ["Nadir", "Yönetici", "Sofistike", "Gizemli"], "color": "Green"},
    {"name": "Vanda Orchid", "sifatlar": ["Karizmatik", "Eksotik", "Güçlü", "Zarif"], "color": "Purple"},
    {"name": "Oncidium Orchid", "sifatlar": ["Neşeli", "Canlı", "Komik", "Misketçi"], "color": "Yellow"},
    {"name": "Cymbidium Orchid", "sifatlar": ["Zarif", "Sofistike", "Zarif", "Majestatik"], "color": "Pink"},
    {"name": "Miltonia Orchid", "sifatlar": ["Güzel", "Zarif", "Delikat", "Sofistike"], "color": "Purple"},

    # ── Sunflowers (6) ────────────────────────────────────────────────────────
    {"name": "Sunflower", "sifatlar": ["Canlı", "Pozitif", "Güneş", "Ümit"], "color": "Yellow"},
    {"name": "Teddy Bear Sunflower", "sifatlar": ["Sevimli", "Yumuşak", "Neşeli", "Tatlı"], "color": "Yellow"},
    {"name": "Moulin Rouge Sunflower", "sifatlar": ["Dramatik", "Cesur", "Kırmızı", "Yoğun"], "color": "Red"},
    {"name": "Italian Sunflower", "sifatlar": ["Zarif", "Sofistike", "Santoral", "Klasik"], "color": "Orange"},
    {"name": "Autumn Beauty Sunflower", "sifatlar": ["Güzel", "Başyapıt", "Renk", "Sofistike"], "color": "Mixed"},
    {"name": "Velvet Queen Sunflower", "sifatlar": ["Regal", "Kraliyet", "Koyu", "Gözlü"], "color": "Burgundy"},

    # ── Hydrangeas (6) ────────────────────────────────────────────────────────
    {"name": "Blue Hydrangea", "sifatlar": ["Sakin", "Gıcır", "Zarif", "Rüya"], "color": "Blue"},
    {"name": "Pink Hydrangea", "sifatlar": ["Zarif", "Feminin", "Romantik", "Yumuşak"], "color": "Pink"},
    {"name": "White Hydrangea", "sifatlar": ["Saflık", "Zarif", "Innocent", "Klasik"], "color": "White"},
    {"name": "Purple Hydrangea", "sifatlar": ["Regal", "Sofistike", "Mağrur", "Gizemli"], "color": "Purple"},
    {"name": "Green Hydrangea", "sifatlar": ["Canlı", "Doğal", "Zarif", "Yeni Başlangıç"], "color": "Green"},
    {"name": "Red Hydrangea", "sifatlar": ["Tutkulu", "Cesur", "Yoğun", "Güçlü"], "color": "Red"},

    # ── Peonies (6) ───────────────────────────────────────────────────────────
    {"name": "Pink Peony", "sifatlar": ["Zarif", "Romantik", "Feminin", "Lüks"], "color": "Pink"},
    {"name": "Red Peony", "sifatlar": ["Tutkulu", "Güçlü", "Duyarlı", "Ateşli"], "color": "Red"},
    {"name": "White Peony", "sifatlar": ["Saflık", "Zarif", "Sakin", "Beyaz Aşk"], "color": "White"},
    {"name": "Coral Peony", "sifatlar": ["Sıcak", "Cazip", "Zevkli", "Güzel"], "color": "Coral"},
    {"name": "Yellow Peony", "sifatlar": ["Mutlu", "Canlı", "Pozitif", "Güneş"], "color": "Yellow"},
    {"name": "Double Peony", "sifatlar": ["Lüks", "Sofistike", "Volümlü", "Spektaküler"], "color": "Pink"},

    # ── Dahlias (6) ───────────────────────────────────────────────────────────
    {"name": "Dahlia Blossom", "sifatlar": ["Zarif", "Geometrik", "Sofistike", "Kompleks"], "color": "Pink"},
    {"name": "Dinner Plate Dahlia", "sifatlar": ["Regal", "Majestatik", "Büyük", "Spektaküler"], "color": "Red"},
    {"name": "Cactus Dahlia", "sifatlar": ["Cesur", "Yabani", "Tutkulu", "Yapılı"], "color": "Red"},
    {"name": "Ball Dahlia", "sifatlar": ["Mükemmel", "Simetrik", "Klasik", "Zarif"], "color": "Purple"},
    {"name": "Pompon Dahlia", "sifatlar": ["Küçük", "Sevimli", "Yoğun", "Zarif"], "color": "Pink"},
    {"name": "Anemone Dahlia", "sifatlar": ["Delikat", "Zarif", "Güzel", "Narin"], "color": "White"},

    # ── Cherry Blossoms (4) ────────────────────────────────────────────────────
    {"name": "Sakura Cherry Blossom", "sifatlar": ["Efsane", "Zamansız", "Güzel", "Geçici"], "color": "Pink"},
    {"name": "Double Cherry Blossom", "sifatlar": ["Lüks", "Volümlü", "Sofistike", "Zarif"], "color": "Pink"},
    {"name": "Weeping Cherry Blossom", "sifatlar": ["Duyarlı", "Zarif", "Şarkılı", "Güzel"], "color": "Pink"},
    {"name": "Yoshino Cherry", "sifatlar": ["Rüya", "Efsane", "Beyaz", "Güzel"], "color": "White"},

    # ── Lavender (4) ──────────────────────────────────────────────────────────
    {"name": "English Lavender", "sifatlar": ["Rahatlatıcı", "Aromatik", "Zarif", "Klasik"], "color": "Purple"},
    {"name": "French Lavender", "sifatlar": ["Sofistike", "Fransız", "Zarif", "Aromatik"], "color": "Purple"},
    {"name": "Spanish Lavender", "sifatlar": ["Cesur", "Canlı", "Dekoratif", "Güzel"], "color": "Purple"},
    {"name": "Grosso Lavender", "sifatlar": ["Yoğun", "Aromatik", "Canlı", "Üretken"], "color": "Purple"},

    # ── Gardenias (4) ─────────────────────────────────────────────────────────
    {"name": "Gardenia", "sifatlar": ["Parfümlü", "Zarif", "Beyaz", "Klasik"], "color": "White"},
    {"name": "Double Gardenia", "sifatlar": ["Lüks", "Volümlü", "Klasik", "Sofistike"], "color": "White"},
    {"name": "Mystery Gardenia", "sifatlar": ["Gizemli", "Zarif", "Nadir", "Beyaz"], "color": "White"},
    {"name": "Radicans Gardenia", "sifatlar": ["Küçük", "Zarif", "Beyaz", "Narin"], "color": "White"},

    # ── Magnolias (4) ──────────────────────────────────────────────────────────
    {"name": "Pink Magnolia", "sifatlar": ["Zarif", "Romantik", "Feminin", "Klasik"], "color": "Pink"},
    {"name": "White Magnolia", "sifatlar": ["Saflık", "Zarif", "Klasik", "Güzel"], "color": "White"},
    {"name": "Star Magnolia", "sifatlar": ["Delikat", "Zarif", "Narin", "Beyaz"], "color": "White"},
    {"name": "Purple Magnolia", "sifatlar": ["Regal", "Sofistike", "Zarif", "Dramatis"], "color": "Purple"},

    # ── Jasmine (3) ───────────────────────────────────────────────────────────
    {"name": "White Jasmine", "sifatlar": ["Parfümlü", "Zarif", "Beyaz", "Aromatik"], "color": "White"},
    {"name": "Yellow Jasmine", "sifatlar": ["Mutlu", "Canlı", "Aromatik", "Güneş"], "color": "Yellow"},
    {"name": "Arabian Jasmine", "sifatlar": ["Eksotik", "Parfümlü", "Zarif", "Aromatik"], "color": "White"},

    # ── Calla Lilies (3) ───────────────────────────────────────────────────────
    {"name": "White Calla Lily", "sifatlar": ["Zarif", "Sofistike", "Feminin", "Güzel"], "color": "White"},
    {"name": "Black Calla Lily", "sifatlar": ["Gizemli", "Sofistike", "Cesur", "Güçlü"], "color": "Black"},
    {"name": "Coral Calla Lily", "sifatlar": ["Sıcak", "Cazip", "Feminin", "Güzel"], "color": "Coral"},
]

# ══════════════════════════════════════════════════════════════════════════════
# 🦁 ANIMALS (80 entries)
# ══════════════════════════════════════════════════════════════════════════════

ANIMALS = [
    # ── Big Cats (10) ─────────────────────────────────────────────────────────
    {"name": "Lion", "sifatlar": ["Lider", "Cesur", "Güçlü", "Asil"], "behavioral_traits": ["Leader", "Brave", "Powerful", "Noble"]},
    {"name": "Tiger", "sifatlar": ["Güçlü", "Fokus", "Yüce Tanrı Kompleksi", "Cesur"], "behavioral_traits": ["Powerful", "Focused", "Majestic", "Brave"]},
    {"name": "Leopard", "sifatlar": ["Zarif", "Sinsi", "Güzelük Bilinçli", "Bağımsız"], "behavioral_traits": ["Graceful", "Stealthy", "Beautiful", "Independent"]},
    {"name": "Panther", "sifatlar": ["Güçlü", "Zarif", "Bağımsız", "Gizemli"], "behavioral_traits": ["Graceful", "Powerful", "Stealthy", "Independent"]},
    {"name": "Cheetah", "sifatlar": ["Hızlı", "Cesur", "Atletik", "Bağımsız"], "behavioral_traits": ["Fast", "Brave", "Athletic", "Independent"]},
    {"name": "Jaguar", "sifatlar": ["Güçlü", "Cesur", "Hakim", "Yönetici"], "behavioral_traits": ["Powerful", "Brave", "Dominant", "Leader"]},
    {"name": "Cougar", "sifatlar": ["Zarif", "Sinsi", "Bağımsız", "Başarılı"], "behavioral_traits": ["Graceful", "Stealthy", "Independent", "Successful"]},
    {"name": "Puma", "sifatlar": ["Atletik", "Hızlı", "Başarılı", "Güçlü"], "behavioral_traits": ["Athletic", "Fast", "Successful", "Powerful"]},
    {"name": "Snow Leopard", "sifatlar": ["Nadir", "Zarif", "Gizemli", "Süne"], "behavioral_traits": ["Rare", "Graceful", "Mysterious", "Solitary"]},
    {"name": "Black Panther", "sifatlar": ["Güçlü", "Cesur", "Gizemli", "Efsanevi"], "behavioral_traits": ["Powerful", "Brave", "Mysterious", "Legendary"]},

    # ── Birds (15) ────────────────────────────────────────────────────────────
    {"name": "Eagle", "sifatlar": ["Cesur", "Vizyon", "Güçlü", "Özgür"], "behavioral_traits": ["Bold", "Visionary", "Powerful", "Free"]},
    {"name": "Phoenix", "sifatlar": ["Efsanevi", "Yeniden Doğmuş", "Güçlü", "Ümit"], "behavioral_traits": ["Legendary", "Reborn", "Powerful", "Hope"]},
    {"name": "Swan", "sifatlar": ["Zarif", "Sakin", "Güzel", "Hanım"], "behavioral_traits": ["Graceful", "Serene", "Elegant", "Loyal"]},
    {"name": "Peacock", "sifatlar": ["Görkemli", "Karizmatik", "Güçlü", "Başarılı"], "behavioral_traits": ["Majestic", "Charismatic", "Powerful", "Successful"]},
    {"name": "Hawk", "sifatlar": ["Keskin Gözlü", "Cesur", "Fokus", "Hızlı"], "behavioral_traits": ["Sharp-eyed", "Brave", "Focused", "Fast"]},
    {"name": "Falcon", "sifatlar": ["Hızlı", "Cesur", "Atletik", "Güçlü"], "behavioral_traits": ["Fast", "Brave", "Athletic", "Powerful"]},
    {"name": "Owl", "sifatlar": ["Bilge", "Gizemli", "İntellektüel", "Derin"], "behavioral_traits": ["Wise", "Mysterious", "Intelligent", "Deep"]},
    {"name": "Raven", "sifatlar": ["Akıllı", "Gizemli", "Efsanevi", "Karanlık"], "behavioral_traits": ["Intelligent", "Mysterious", "Legendary", "Dark"]},
    {"name": "Dove", "sifatlar": ["Barış", "Zarif", "Güzel", "Masum"], "behavioral_traits": ["Peaceful", "Graceful", "Beautiful", "Innocent"]},
    {"name": "Hummingbird", "sifatlar": ["Hızlı", "Delikat", "Zarif", "Cazip"], "behavioral_traits": ["Fast", "Delicate", "Graceful", "Charming"]},
    {"name": "Crow", "sifatlar": ["Akıllı", "Uyarlanabilir", "Sosyal", "Gizemli"], "behavioral_traits": ["Intelligent", "Adaptable", "Social", "Mysterious"]},
    {"name": "Flamingo", "sifatlar": ["Görkemli", "Zarif", "Sosyal", "Renkli"], "behavioral_traits": ["Majestic", "Graceful", "Social", "Colorful"]},
    {"name": "Butterfly", "sifatlar": ["Zarif", "Dönüşüm", "Güzel", "Özgür"], "behavioral_traits": ["Graceful", "Transformative", "Beautiful", "Free"]},
    {"name": "Crane", "sifatlar": ["Zarif", "Sagacious", "Barışsever", "Uzun Yaşlı"], "behavioral_traits": ["Graceful", "Wise", "Peaceful", "Long-lived"]},
    {"name": "Parrot", "sifatlar": ["Akıllı", "Sosyal", "Renkli", "Konuşkan"], "behavioral_traits": ["Intelligent", "Social", "Colorful", "Talkative"]},

    # ── Canines (10) ───────────────────────────────────────────────────────────
    {"name": "Wolf", "sifatlar": ["Güçlü", "Sosyal", "Loyal", "Bağımsız"], "behavioral_traits": ["Powerful", "Social", "Loyal", "Independent"]},
    {"name": "Fox", "sifatlar": ["Akıllı", "Sinsi", "Çevik", "Bağımsız"], "behavioral_traits": ["Intelligent", "Cunning", "Agile", "Independent"]},
    {"name": "Dog", "sifatlar": ["Loyal", "Sevgi Dolu", "Sadık", "Jenerük"], "behavioral_traits": ["Loyal", "Loving", "Faithful", "Generous"]},
    {"name": "Husky", "sifatlar": ["Güçlü", "Bağımsız", "Cazip", "Cesur"], "behavioral_traits": ["Powerful", "Independent", "Charming", "Brave"]},
    {"name": "Dingo", "sifatlar": ["Bağımsız", "Vahşi", "Akıllı", "Güçlü"], "behavioral_traits": ["Independent", "Wild", "Intelligent", "Powerful"]},
    {"name": "Hyena", "sifatlar": ["Sosyal", "Akıllı", "Cesur", "Güçlü"], "behavioral_traits": ["Social", "Intelligent", "Brave", "Powerful"]},
    {"name": "Jackal", "sifatlar": ["Akıllı", "Uyarlanabilir", "Çevik", "Sinsi"], "behavioral_traits": ["Intelligent", "Adaptable", "Agile", "Cunning"]},
    {"name": "Coyote", "sifatlar": ["Akıllı", "Uyarlanabilir", "Bağımsız", "Cesur"], "behavioral_traits": ["Intelligent", "Adaptable", "Independent", "Brave"]},
    {"name": "Afghan Hound", "sifatlar": ["Zarif", "Oğlu", "Güçlü", "Asil"], "behavioral_traits": ["Graceful", "Proud", "Powerful", "Noble"]},
    {"name": "German Shepherd", "sifatlar": ["Loyal", "Akıllı", "Güçlü", "Cesur"], "behavioral_traits": ["Loyal", "Intelligent", "Powerful", "Brave"]},

    # ── Felines (10) ───────────────────────────────────────────────────────────
    {"name": "Siamese Cat", "sifatlar": ["Zarif", "Karizmatik", "Sosyal", "Sessiz"], "behavioral_traits": ["Graceful", "Charismatic", "Social", "Vocal"]},
    {"name": "Bengal Tiger", "sifatlar": ["Güçlü", "Fokus", "Cesur", "Yüce"], "behavioral_traits": ["Powerful", "Focused", "Brave", "Majestic"]},
    {"name": "Lynx", "sifatlar": ["Gizemli", "Zarif", "Bağımsız", "Sinsi"], "behavioral_traits": ["Mysterious", "Graceful", "Independent", "Stealthy"]},
    {"name": "Cheshire Cat", "sifatlar": ["Gizemli", "Akıllı", "Komik", "Efsanevi"], "behavioral_traits": ["Mysterious", "Intelligent", "Witty", "Legendary"]},
    {"name": "Tabby Cat", "sifatlar": ["Uyarlanabilir", "Sosyal", "Oyuncu", "Sevgi Dolu"], "behavioral_traits": ["Adaptable", "Social", "Playful", "Loving"]},
    {"name": "Black Cat", "sifatlar": ["Gizemli", "Zarif", "Bağımsız", "Efsanevi"], "behavioral_traits": ["Mysterious", "Graceful", "Independent", "Legendary"]},
    {"name": "White Cat", "sifatlar": ["Saflık", "Zarif", "Naif", "Majestatik"], "behavioral_traits": ["Pure", "Graceful", "Elegant", "Majestic"]},
    {"name": "Ragdoll Cat", "sifatlar": ["Yumuşak", "Sevgi Dolu", "Loyal", "Evcil"], "behavioral_traits": ["Gentle", "Loving", "Loyal", "Affectionate"]},
    {"name": "Sphynx Cat", "sifatlar": ["Bilinç", "Gizemli", "Akıllı", "Alışılmadık"], "behavioral_traits": ["Conscious", "Mysterious", "Intelligent", "Unusual"]},
    {"name": "Persian Cat", "sifatlar": ["Zarif", "Sofistike", "Malous", "Güzel"], "behavioral_traits": ["Graceful", "Sophisticated", "Regal", "Beautiful"]},

    # ── Marine Animals (10) ────────────────────────────────────────────────────
    {"name": "Dolphin", "sifatlar": ["Akıllı", "Sosyal", "Oyuncu", "Zeki"], "behavioral_traits": ["Intelligent", "Social", "Playful", "Smart"]},
    {"name": "Shark", "sifatlar": ["Güçlü", "Cesur", "Fokus", "Hakim"], "behavioral_traits": ["Powerful", "Brave", "Focused", "Dominant"]},
    {"name": "Whale", "sifatlar": ["Büyük", "Güçlü", "Zarif", "Akıllı"], "behavioral_traits": ["Large", "Powerful", "Graceful", "Intelligent"]},
    {"name": "Octopus", "sifatlar": ["Akıllı", "Uyarlanabilir", "Yaratıcı", "Gizemli"], "behavioral_traits": ["Intelligent", "Adaptable", "Creative", "Mysterious"]},
    {"name": "Seahorse", "sifatlar": ["Delikat", "Zarif", "Eşi Benzersiz", "Zarif"], "behavioral_traits": ["Delicate", "Graceful", "Unique", "Elegant"]},
    {"name": "Stingray", "sifatlar": ["Zarif", "Gizemli", "Çevik", "Sinsi"], "behavioral_traits": ["Graceful", "Mysterious", "Agile", "Stealthy"]},
    {"name": "Sea Turtle", "sifatlar": ["Bilge", "Uzun Yaşlı", "Barışsever", "Zarif"], "behavioral_traits": ["Wise", "Long-lived", "Peaceful", "Graceful"]},
    {"name": "Jellyfish", "sifatlar": ["Delikat", "Zarif", "Gizemli", "Efsanevi"], "behavioral_traits": ["Delicate", "Graceful", "Mysterious", "Legendary"]},
    {"name": "Manta Ray", "sifatlar": ["Zarif", "Büyük", "Gizemli", "Akıllı"], "behavioral_traits": ["Graceful", "Large", "Mysterious", "Intelligent"]},
    {"name": "Pufferfish", "sifatlar": ["Komik", "Zeki", "Koruyucu", "Cazip"], "behavioral_traits": ["Funny", "Intelligent", "Protective", "Charming"]},

    # ── Primates (8) ───────────────────────────────────────────────────────────
    {"name": "Chimpanzee", "sifatlar": ["Akıllı", "Sosyal", "Ekspresif", "Güçlü"], "behavioral_traits": ["Intelligent", "Social", "Expressive", "Powerful"]},
    {"name": "Gorilla", "sifatlar": ["Güçlü", "Yumuşak", "Koruyucu", "Sosyal"], "behavioral_traits": ["Powerful", "Gentle", "Protective", "Social"]},
    {"name": "Orangutan", "sifatlar": ["Akıllı", "Zarif", "Düşünceli", "Bağımsız"], "behavioral_traits": ["Intelligent", "Graceful", "Thoughtful", "Independent"]},
    {"name": "Lemur", "sifatlar": ["Sosyal", "Oyuncu", "Renkli", "Komik"], "behavioral_traits": ["Social", "Playful", "Colorful", "Funny"]},
    {"name": "Monkey", "sifatlar": ["Akıllı", "Oyuncu", "Sosyal", "Çevik"], "behavioral_traits": ["Intelligent", "Playful", "Social", "Agile"]},
    {"name": "Baboon", "sifatlar": ["Sosyal", "Güçlü", "Akıllı", "Cesur"], "behavioral_traits": ["Social", "Powerful", "Intelligent", "Brave"]},
    {"name": "Gibbon", "sifatlar": ["Zarif", "Çevik", "Sosyal", "Musikalı"], "behavioral_traits": ["Graceful", "Agile", "Social", "Musical"]},
    {"name": "Macaque", "sifatlar": ["Sosyal", "Akıllı", "Uyarlanabilir", "Cesur"], "behavioral_traits": ["Social", "Intelligent", "Adaptable", "Brave"]},

    # ── Ungulates (8) ──────────────────────────────────────────────────────────
    {"name": "Deer", "sifatlar": ["Zarif", "Çevik", "Hassas", "Sakin"], "behavioral_traits": ["Graceful", "Agile", "Sensitive", "Calm"]},
    {"name": "Giraffe", "sifatlar": ["Uzun", "Zarif", "Nazik", "Sakin"], "behavioral_traits": ["Tall", "Graceful", "Gentle", "Calm"]},
    {"name": "Antelope", "sifatlar": ["Hızlı", "Zarif", "Çevik", "Güzel"], "behavioral_traits": ["Fast", "Graceful", "Agile", "Beautiful"]},
    {"name": "Zebra", "sifatlar": ["Bağımsız", "Sosyal", "Cesur", "Ruhlu"], "behavioral_traits": ["Independent", "Social", "Brave", "Spirited"]},
    {"name": "Moose", "sifatlar": ["Büyük", "Güçlü", "Bağımsız", "Majestik"], "behavioral_traits": ["Large", "Powerful", "Independent", "Majestic"]},
    {"name": "Elk", "sifatlar": ["Güçlü", "Asil", "Majestik", "Bağımsız"], "behavioral_traits": ["Powerful", "Noble", "Majestic", "Independent"]},
    {"name": "Musk Ox", "sifatlar": ["Güçlü", "Koruyucu", "Sosyal", "Cesur"], "behavioral_traits": ["Powerful", "Protective", "Social", "Brave"]},
    {"name": "Reindeer", "sifatlar": ["Güçlü", "Sosyal", "Oyuncu", "Yardımcı"], "behavioral_traits": ["Powerful", "Social", "Playful", "Helpful"]},

    # ── Predators (7) ──────────────────────────────────────────────────────────
    {"name": "Grizzly Bear", "sifatlar": ["Güçlü", "Cesur", "Bağımsız", "Korkutucu"], "behavioral_traits": ["Powerful", "Brave", "Independent", "Fearsome"]},
    {"name": "Polar Bear", "sifatlar": ["Güçlü", "Hakim", "Bağımsız", "Başarılı"], "behavioral_traits": ["Powerful", "Dominant", "Independent", "Successful"]},
    {"name": "Crocodile", "sifatlar": ["Güçlü", "Keskin", "Sakin", "Sinsi"], "behavioral_traits": ["Powerful", "Sharp", "Calm", "Stealthy"]},
    {"name": "Anaconda", "sifatlar": ["Güçlü", "Sinsi", "Hakim", "Efsanevi"], "behavioral_traits": ["Powerful", "Stealthy", "Dominant", "Legendary"]},
    {"name": "Komodo Dragon", "sifatlar": ["Güçlü", "Keskin", "Hakim", "Efsanevi"], "behavioral_traits": ["Powerful", "Sharp", "Dominant", "Legendary"]},
    {"name": "Hyena", "sifatlar": ["Sosyal", "Akıllı", "Cesur", "Güçlü"], "behavioral_traits": ["Social", "Intelligent", "Brave", "Powerful"]},
    {"name": "Wild Boar", "sifatlar": ["Güçlü", "Cesur", "Agresif", "Yaramaz"], "behavioral_traits": ["Powerful", "Brave", "Aggressive", "Mischievous"]},

    # ── Small Animals (7) ──────────────────────────────────────────────────────
    {"name": "Rabbit", "sifatlar": ["Hızlı", "Çevik", "Tatlı", "Korkunç"], "behavioral_traits": ["Fast", "Agile", "Cute", "Skittish"]},
    {"name": "Squirrel", "sifatlar": ["Enerjik", "Oyuncu", "Hazırlayan", "Sosyal"], "behavioral_traits": ["Energetic", "Playful", "Preparatory", "Social"]},
    {"name": "Hedgehog", "sifatlar": ["Sevimli", "Koruyucu", "Bağımsız", "Hassas"], "behavioral_traits": ["Cute", "Protective", "Independent", "Sensitive"]},
    {"name": "Ferret", "sifatlar": ["Çevik", "Oyuncu", "Sosyal", "Meraklı"], "behavioral_traits": ["Agile", "Playful", "Social", "Curious"]},
    {"name": "Weasel", "sifatlar": ["Çevik", "Hızlı", "Sinsi", "Akıllı"], "behavioral_traits": ["Agile", "Fast", "Stealthy", "Intelligent"]},
    {"name": "Porcupine", "sifatlar": ["Koruyucu", "Keskin", "Dirençli", "Bağımsız"], "behavioral_traits": ["Protective", "Sharp", "Resilient", "Independent"]},
    {"name": "Badger", "sifatlar": ["Güçlü", "Cesur", "Dirençli", "Bağımsız"], "behavioral_traits": ["Powerful", "Brave", "Resilient", "Independent"]},
]

# ══════════════════════════════════════════════════════════════════════════════
# SEEDING FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def seed_expanded_data():
    """440 entry'li veriyi seed et"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=30000)
        db = client['facesyma-backend']

        print("🌱 EXPANDED Similarity Data Seeding başladı...\n")

        # ── Celebrities ────────────────────────────────────────────────────────
        print(f"🎬 Seeding {len(CELEBRITIES)} celebrities...")
        celebrities_col = db['similarities_celebrities']
        celebrities_col.delete_many({})
        if CELEBRITIES:
            celebrities_col.insert_many(CELEBRITIES)
            print(f"   ✅ {len(CELEBRITIES)} celebrities seeded")

        # ── Historical ─────────────────────────────────────────────────────────
        print(f"📜 Seeding {len(HISTORICAL)} historical figures...")
        historical_col = db['similarities_historical']
        historical_col.delete_many({})
        if HISTORICAL:
            historical_col.insert_many(HISTORICAL)
            print(f"   ✅ {len(HISTORICAL)} historical figures seeded")

        # ── Objects ────────────────────────────────────────────────────────────
        print(f"🎨 Seeding {len(OBJECTS)} objects/style items...")
        objects_col = db['similarities_objects']
        objects_col.delete_many({})
        if OBJECTS:
            objects_col.insert_many(OBJECTS)
            print(f"   ✅ {len(OBJECTS)} objects seeded")

        # ── Plants ─────────────────────────────────────────────────────────────
        print(f"🌸 Seeding {len(PLANTS)} plants/flowers...")
        plants_col = db['similarities_plants']
        _pcd = plants_col.count_documents
        plants_col.delete_many({})
        if PLANTS:
            plants_col.insert_many(PLANTS)
            print(f"   ✅ {len(PLANTS)} plants seeded")

        # ── Animals ────────────────────────────────────────────────────────────
        print(f"🦁 Seeding {len(ANIMALS)} animals...")
        animals_col = db['similarities_animals']
        _acd = animals_col.count_documents
        animals_col.delete_many({})
        if ANIMALS:
            animals_col.insert_many(ANIMALS)
            print(f"   ✅ {len(ANIMALS)} animals seeded")

        # ── Summary ────────────────────────────────────────────────────────────
        print("\n" + "="*70)
        print("✅ EXPANDED Data Seeding Complete!")
        print("="*70)

        _ccd = celebrities_col.count_documents
        _hcd = historical_col.count_documents
        _ocd = objects_col.count_documents
        _n_cel = _ccd({})
        _n_his = _hcd({})
        _n_obj = _ocd({})
        _n_pla = _pcd({})
        _n_ani = _acd({})
        total = _n_cel + _n_his + _n_obj + _n_pla + _n_ani

        print(f"\n📊 Total Entries: {total}")
        print(f"   🎬 Celebrities:  {_n_cel}")
        print(f"   📜 Historical:   {_n_his}")
        print(f"   🎨 Objects:      {_n_obj}")
        print(f"   🌸 Plants:       {_n_pla}")
        print(f"   🦁 Animals:      {_n_ani}")

        print(f"\n✨ Phase 1 Similarity Module READY with {total} entries!")

        client.close()
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import sys
    success = seed_expanded_data()
    sys.exit(0 if success else 1)
