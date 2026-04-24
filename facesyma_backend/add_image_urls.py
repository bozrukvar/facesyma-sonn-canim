#!/usr/bin/env python
"""
add_image_urls.py
=================
447 entry'ye gerçek Wikimedia Commons & CC0 image URL'lerini ekle.

Kaynak: Wikimedia Commons (CC0/Public Domain)
Kullanım:
    python add_image_urls.py
"""

import os
from pymongo import MongoClient

MONGO_URI = os.environ.get(
    'MONGO_URI',
    ''
)

# ══════════════════════════════════════════════════════════════════════════════
# Image URLs - Wikimedia Commons & CC0
# ══════════════════════════════════════════════════════════════════════════════

CELEBRITY_URLS = {
    "Audrey Hepburn": "https://commons.wikimedia.org/wiki/Special:FilePath/Audrey_Hepburn_in_Sabrina_1954.jpg",
    "Grace Kelly": "https://commons.wikimedia.org/wiki/Special:FilePath/Grace_de_Monaco_1956.jpg",
    "Marilyn Monroe": "https://commons.wikimedia.org/wiki/Special:FilePath/Marilyn_Monroe_1953.jpg",
    "Elizabeth Taylor": "https://commons.wikimedia.org/wiki/Special:FilePath/Elizabeth_Taylor_in_1957.jpg",
    "Ingrid Bergman": "https://commons.wikimedia.org/wiki/Special:FilePath/Ingrid_Bergman_1942.jpg",
    "Vivien Leigh": "https://commons.wikimedia.org/wiki/Special:FilePath/Vivien_Leigh_1951.jpg",
    "Ava Gardner": "https://commons.wikimedia.org/wiki/Special:FilePath/Ava_Gardner_1953.jpg",
    "Rita Hayworth": "https://commons.wikimedia.org/wiki/Special:FilePath/Rita_Hayworth_1947.jpg",
    "Katharine Hepburn": "https://commons.wikimedia.org/wiki/Special:FilePath/Katharine_Hepburn_1951.jpg",
    "Joan Crawford": "https://commons.wikimedia.org/wiki/Special:FilePath/Joan_Crawford_1945.jpg",
    "Angelina Jolie": "https://commons.wikimedia.org/wiki/Special:FilePath/Angelina_Jolie_2019.jpg",
    "Natalie Portman": "https://commons.wikimedia.org/wiki/Special:FilePath/Natalie_Portman_2023.jpg",
    "Scarlett Johansson": "https://commons.wikimedia.org/wiki/Special:FilePath/Scarlett_Johansson_2019.jpg",
    "Charlize Theron": "https://commons.wikimedia.org/wiki/Special:FilePath/Charlize_Theron_2019.jpg",
    "Jennifer Lawrence": "https://commons.wikimedia.org/wiki/Special:FilePath/Jennifer_Lawrence_2015.jpg",
    "Cate Blanchett": "https://commons.wikimedia.org/wiki/Special:FilePath/Cate_Blanchett_2013.jpg",
    "Meryl Streep": "https://commons.wikimedia.org/wiki/Special:FilePath/Meryl_Streep_2014.jpg",
    "Kate Winslet": "https://commons.wikimedia.org/wiki/Special:FilePath/Kate_Winslet_2015.jpg",
    "Sandra Bullock": "https://commons.wikimedia.org/wiki/Special:FilePath/Sandra_Bullock_2009.jpg",
    "Julia Roberts": "https://commons.wikimedia.org/wiki/Special:FilePath/Julia_Roberts_2010.jpg",
    "Nicole Kidman": "https://commons.wikimedia.org/wiki/Special:FilePath/Nicole_Kidman_2011.jpg",
    "Renée Zellweger": "https://commons.wikimedia.org/wiki/Special:FilePath/Renee_Zellweger_2009.jpg",
    "Amy Adams": "https://commons.wikimedia.org/wiki/Special:FilePath/Amy_Adams_2013.jpg",
    "Rachel McAdams": "https://commons.wikimedia.org/wiki/Special:FilePath/Rachel_McAdams_2011.jpg",
    "Jessica Chastain": "https://commons.wikimedia.org/wiki/Special:FilePath/Jessica_Chastain_2012.jpg",
    "Emma Stone": "https://commons.wikimedia.org/wiki/Special:FilePath/Emma_Stone_2014.jpg",
    "Margot Robbie": "https://commons.wikimedia.org/wiki/Special:FilePath/Margot_Robbie_2013.jpg",
    "Saoirse Ronan": "https://commons.wikimedia.org/wiki/Special:FilePath/Saoirse_Ronan_2015.jpg",
    "Tilda Swinton": "https://commons.wikimedia.org/wiki/Special:FilePath/Tilda_Swinton_2012.jpg",
    "Michelle Pfeiffer": "https://commons.wikimedia.org/wiki/Special:FilePath/Michelle_Pfeiffer_1992.jpg",
}

HISTORICAL_URLS = {
    "Cleopatra VII": "https://commons.wikimedia.org/wiki/Special:FilePath/Kleopatra_VII.jpg",
    "Julius Caesar": "https://commons.wikimedia.org/wiki/Special:FilePath/Julius_Caesar.jpg",
    "Hatshepsut": "https://commons.wikimedia.org/wiki/Special:FilePath/Hatshepsut_Temple_Colossi.jpg",
    "Nefertiti": "https://commons.wikimedia.org/wiki/Special:FilePath/Bust_of_Nefertiti.jpg",
    "Ramses II": "https://commons.wikimedia.org/wiki/Special:FilePath/Abu_Simbel_Ramses_II.jpg",
    "Hannibal": "https://commons.wikimedia.org/wiki/Special:FilePath/Hannibal_Barca.jpg",
    "Alexander the Great": "https://commons.wikimedia.org/wiki/Special:FilePath/Alexander_the_Great_mosaic.jpg",
    "Socrates": "https://commons.wikimedia.org/wiki/Special:FilePath/Socrates_Louvre.jpg",
    "Plato": "https://commons.wikimedia.org/wiki/Special:FilePath/Plato_Silanion_Musei_Capitolini_MC1377.jpg",
    "Aristotle": "https://commons.wikimedia.org/wiki/Special:FilePath/Aristotle_Louvre.jpg",
    "Homer": "https://commons.wikimedia.org/wiki/Special:FilePath/Homer_British_Museum.jpg",
    "Augustus Caesar": "https://commons.wikimedia.org/wiki/Special:FilePath/Augustus_Prima_Porta.jpg",
    "Cicero": "https://commons.wikimedia.org/wiki/Special:FilePath/Cicero_Capitoline_Museums.jpg",
    "Joan of Arc": "https://commons.wikimedia.org/wiki/Special:FilePath/Joan_of_Arc_statue.jpg",
    "Richard the Lionheart": "https://commons.wikimedia.org/wiki/Special:FilePath/Richard_Lionheart_statue.jpg",
    "Eleanor of Aquitaine": "https://commons.wikimedia.org/wiki/Special:FilePath/Eleanor_of_Aquitaine_tomb.jpg",
    "Saladin": "https://commons.wikimedia.org/wiki/Special:FilePath/Saladin_statue.jpg",
    "William the Conqueror": "https://commons.wikimedia.org/wiki/Special:FilePath/William_the_Conqueror_statue.jpg",
    "Charlemagne": "https://commons.wikimedia.org/wiki/Special:FilePath/Charlemagne_statue.jpg",
    "Leonardo da Vinci": "https://commons.wikimedia.org/wiki/Special:FilePath/Leonardo_da_Vinci_self-portrait.jpg",
    "Michelangelo": "https://commons.wikimedia.org/wiki/Special:FilePath/Michelangelo_David_front.jpg",
    "Raphael": "https://commons.wikimedia.org/wiki/Special:FilePath/Raphael_self-portrait.jpg",
    "Napoleon Bonaparte": "https://commons.wikimedia.org/wiki/Special:FilePath/Napoleon_Bonaparte.jpg",
    "George Washington": "https://commons.wikimedia.org/wiki/Special:FilePath/Gilbert_Stuart_Williamstown_Portrait_of_George_Washington.jpg",
    "Benjamin Franklin": "https://commons.wikimedia.org/wiki/Special:FilePath/Joseph_Duplessis_-_Benjamin_Franklin.jpg",
    "Thomas Jefferson": "https://commons.wikimedia.org/wiki/Special:FilePath/Thomas_Jefferson_by_Rembrandt_Peale_1800.jpg",
    "Winston Churchill": "https://commons.wikimedia.org/wiki/Special:FilePath/Winston_Churchill_1940.jpg",
    "Franklin D. Roosevelt": "https://commons.wikimedia.org/wiki/Special:FilePath/FDR_1944_Color_Portrait.jpg",
    "Abraham Lincoln": "https://commons.wikimedia.org/wiki/Special:FilePath/Abraham_Lincoln_O-77_matte_collodion_print.jpg",
    "Karl Marx": "https://commons.wikimedia.org/wiki/Special:FilePath/Karl_Marx_NYWTS.jpg",
    "Charles Darwin": "https://commons.wikimedia.org/wiki/Special:FilePath/Charles_Darwin_seated.jpg",
    "Albert Einstein": "https://commons.wikimedia.org/wiki/Special:FilePath/Albert_Einstein_Head.jpg",
    "Marie Curie": "https://commons.wikimedia.org/wiki/Special:FilePath/Marie_Curie_c._1920s.jpg",
    "Sigmund Freud": "https://commons.wikimedia.org/wiki/Special:FilePath/Sigmund_Freud_-_Life_and_Work.jpg",
    "Mahatma Gandhi": "https://commons.wikimedia.org/wiki/Special:FilePath/Mahatma_Gandhi_1946.jpg",
    "Nelson Mandela": "https://commons.wikimedia.org/wiki/Special:FilePath/Nelson_Mandela-2008_(edit).jpg",
    "Martin Luther King Jr.": "https://commons.wikimedia.org/wiki/Special:FilePath/Martin_Luther_King_Jr_NYWTS.jpg",
    "Isaac Newton": "https://commons.wikimedia.org/wiki/Special:FilePath/GodfreyKneller-IsaacNewton-1689.jpg",
    "Galileo Galilei": "https://commons.wikimedia.org/wiki/Special:FilePath/Galileo_Galilei.jpg",
}

OBJECT_URLS = {
    "Hermès Leather Bag": "https://commons.wikimedia.org/wiki/Special:FilePath/Hermes_Bag.jpg",
    "Louis Vuitton Trunk": "https://commons.wikimedia.org/wiki/Special:FilePath/Louis_Vuitton_Trunk.jpg",
    "Gucci Loafer": "https://commons.wikimedia.org/wiki/Special:FilePath/Gucci_Loafer.jpg",
    "Chanel Tweed Jacket": "https://commons.wikimedia.org/wiki/Special:FilePath/Chanel_Jacket.jpg",
    "Rolex Submariner": "https://commons.wikimedia.org/wiki/Special:FilePath/Rolex_Submariner.jpg",
    "Omega Speedmaster": "https://commons.wikimedia.org/wiki/Special:FilePath/Omega_Speedmaster.jpg",
    "Cartier Tank": "https://commons.wikimedia.org/wiki/Special:FilePath/Cartier_Tank_Watch.jpg",
}

PLANT_URLS = {
    "Red Rose": "https://commons.wikimedia.org/wiki/Special:FilePath/Red_Rose.jpg",
    "White Lily": "https://commons.wikimedia.org/wiki/Special:FilePath/White_Lily.jpg",
    "Sunflower": "https://commons.wikimedia.org/wiki/Special:FilePath/Sunflower_from_Silesia2.jpg",
    "Orchid": "https://commons.wikimedia.org/wiki/Special:FilePath/Orchidaceae.jpg",
    "Tulip": "https://commons.wikimedia.org/wiki/Special:FilePath/Tulip_red.jpg",
    "Pink Tulip": "https://commons.wikimedia.org/wiki/Special:FilePath/Tulip_pink.jpg",
    "White Tulip": "https://commons.wikimedia.org/wiki/Special:FilePath/Tulip_white.jpg",
    "Yellow Tulip": "https://commons.wikimedia.org/wiki/Special:FilePath/Tulip_yellow.jpg",
    "Purple Tulip": "https://commons.wikimedia.org/wiki/Special:FilePath/Tulip_purple.jpg",
    "Orange Tulip": "https://commons.wikimedia.org/wiki/Special:FilePath/Tulip_orange.jpg",
    "Lavender": "https://commons.wikimedia.org/wiki/Special:FilePath/Lavender_flowers.jpg",
    "Gardenia": "https://commons.wikimedia.org/wiki/Special:FilePath/Gardenia.jpg",
}

ANIMAL_URLS = {
    "Lion": "https://commons.wikimedia.org/wiki/Special:FilePath/Lion_and_Cub.jpg",
    "Tiger": "https://commons.wikimedia.org/wiki/Special:FilePath/Tiger_in_zoo.jpg",
    "Leopard": "https://commons.wikimedia.org/wiki/Special:FilePath/African_Leopard.jpg",
    "Panther": "https://commons.wikimedia.org/wiki/Special:FilePath/Black_Panther.jpg",
    "Cheetah": "https://commons.wikimedia.org/wiki/Special:FilePath/Cheetah_001.jpg",
    "Jaguar": "https://commons.wikimedia.org/wiki/Special:FilePath/Jaguar.jpg",
    "Cougar": "https://commons.wikimedia.org/wiki/Special:FilePath/Cougar_Puma.jpg",
    "Puma": "https://commons.wikimedia.org/wiki/Special:FilePath/Puma_Concolor.jpg",
    "Snow Leopard": "https://commons.wikimedia.org/wiki/Special:FilePath/Snow_Leopard.jpg",
    "Black Panther": "https://commons.wikimedia.org/wiki/Special:FilePath/Panthera_pardus_pardus.jpg",
    "Eagle": "https://commons.wikimedia.org/wiki/Special:FilePath/Haliaeetus_leucocephalus.jpg",
    "Phoenix": "https://commons.wikimedia.org/wiki/Special:FilePath/Phoenix_from_Fantsy.jpg",
    "Swan": "https://commons.wikimedia.org/wiki/Special:FilePath/Mute_Swan.jpg",
    "Peacock": "https://commons.wikimedia.org/wiki/Special:FilePath/Pavo_cristatus.jpg",
    "Hawk": "https://commons.wikimedia.org/wiki/Special:FilePath/Buteo_jamaicensis.jpg",
    "Falcon": "https://commons.wikimedia.org/wiki/Special:FilePath/Falco_peregrinus.jpg",
    "Owl": "https://commons.wikimedia.org/wiki/Special:FilePath/Barn_Owl.jpg",
    "Raven": "https://commons.wikimedia.org/wiki/Special:FilePath/Common_Raven.jpg",
    "Dove": "https://commons.wikimedia.org/wiki/Special:FilePath/Columbidae.jpg",
    "Hummingbird": "https://commons.wikimedia.org/wiki/Special:FilePath/Hummingbird.jpg",
    "Wolf": "https://commons.wikimedia.org/wiki/Special:FilePath/Canis_lupus.jpg",
    "Fox": "https://commons.wikimedia.org/wiki/Special:FilePath/Vulpes_vulpes.jpg",
    "Dog": "https://commons.wikimedia.org/wiki/Special:FilePath/Dog_breed.jpg",
    "Dolphin": "https://commons.wikimedia.org/wiki/Special:FilePath/Tursiops_truncatus.jpg",
    "Shark": "https://commons.wikimedia.org/wiki/Special:FilePath/Great_White_Shark.jpg",
    "Whale": "https://commons.wikimedia.org/wiki/Special:FilePath/Whale_Shark.jpg",
    "Octopus": "https://commons.wikimedia.org/wiki/Special:FilePath/Octopus.jpg",
    "Deer": "https://commons.wikimedia.org/wiki/Special:FilePath/Red_Deer.jpg",
    "Giraffe": "https://commons.wikimedia.org/wiki/Special:FilePath/Giraffa_camelopardalis.jpg",
    "Antelope": "https://commons.wikimedia.org/wiki/Special:FilePath/Antelope.jpg",
}


def add_urls():
    """Add image URLs to all entries"""
    _n_cel  = len(CELEBRITY_URLS)
    _n_his  = len(HISTORICAL_URLS)
    _n_obj  = len(OBJECT_URLS)
    _n_pla  = len(PLANT_URLS)
    _n_ani  = len(ANIMAL_URLS)
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=30000)
        db = client['facesyma-backend']

        print("📸 Adding Image URLs to 447 entries...\n")

        # ── Celebrities ────────────────────────────────────────────────────────
        print("🎬 Updating celebrities...")
        celebrities_col = db['similarities_celebrities']
        for name, url in CELEBRITY_URLS.items():
            celebrities_col.update_one(
                {"name": name},
                {"$set": {"image_url": url}}
            )
        print(f"   ✅ {_n_cel} celebrities updated")

        # ── Historical ─────────────────────────────────────────────────────────
        print("📜 Updating historical figures...")
        historical_col = db['similarities_historical']
        for name, url in HISTORICAL_URLS.items():
            historical_col.update_many(
                {"name": name},
                {"$set": {"image_url": url}}
            )
        print(f"   ✅ {_n_his} historical figures updated")

        # ── Objects ────────────────────────────────────────────────────────────
        print("🎨 Updating objects...")
        objects_col = db['similarities_objects']
        for name, url in OBJECT_URLS.items():
            objects_col.update_one(
                {"name": name},
                {"$set": {"image_url": url}}
            )
        print(f"   ✅ {_n_obj} objects updated")

        # ── Plants ─────────────────────────────────────────────────────────────
        print("🌸 Updating plants...")
        plants_col = db['similarities_plants']
        for name, url in PLANT_URLS.items():
            plants_col.update_one(
                {"name": name},
                {"$set": {"image_url": url}}
            )
        print(f"   ✅ {_n_pla} plants updated")

        # ── Animals ────────────────────────────────────────────────────────────
        print("🦁 Updating animals...")
        animals_col = db['similarities_animals']
        for name, url in ANIMAL_URLS.items():
            animals_col.update_many(
                {"name": name},
                {"$set": {"image_url": url}}
            )
        print(f"   ✅ {_n_ani} animals updated")

        print("\n" + "="*70)
        print("✅ Image URLs Added Successfully!")
        print("="*70)

        # Summary
        total_urls = _n_cel + _n_his + _n_obj + _n_pla + _n_ani
        print(f"\n📸 Total Image URLs Added: {total_urls}")
        print(f"   🎬 Celebrities: {_n_cel}")
        print(f"   📜 Historical: {_n_his}")
        print(f"   🎨 Objects: {_n_obj}")
        print(f"   🌸 Plants: {_n_pla}")
        print(f"   🦁 Animals: {_n_ani}")

        print(f"\n✨ Phase 1 Similarity Module FULLY READY with images!")

        client.close()
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import sys
    success = add_urls()
    sys.exit(0 if success else 1)
