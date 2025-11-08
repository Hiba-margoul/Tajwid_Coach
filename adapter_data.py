import json


with open('quran-modified32.json', 'r', encoding='utf-8') as f:
    surahs = json.load(f)

baqara_index = None
for i, surah in enumerate(surahs):
    if surah['number'] == 32:
        baqara_index = i
        break

if baqara_index is None:
    print(" Sourate Al-Imran non trouvée!")
    exit()


ayahs = surahs[baqara_index]['ayahs']



# Incrémenter tous les ayahs suivants
for i in range(0, len(ayahs)):
        
    ayahs[i]['numberInSurah'] = i + 1
    ayahs[i]['number'] = str(i + 1)

# Mettre à jour la sourate Al-Baqara
surahs[baqara_index]['ayahs'] = ayahs

# Sauvegarder le Quran complet modifié
with open('quran-modified33.json', 'w', encoding='utf-8') as f:
    json.dump(surahs, f, ensure_ascii=False, indent=2)

print(f"✓ Réorganisation terminée!")
print(f"✓ Sourate Al-Baqara: {len(ayahs)} ayahs")
print(f"✓ Ayah 1: {ayahs[0]['text']}")
print(f"✓ Ayah 2: {ayahs[1]['text']}")
print(f"✓ Dernier ayah (286): ...{ayahs[-1]['text']}")
print(f"✓ Fichier sauvegardé: quran-modified.json")