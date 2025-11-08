import json
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

BASE_URL = "https://surahquran.com/warsh"
BASMALA = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"

async def scrape_quran():
    all_surahs = []
   
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for i in range(1, 115):
            url = f"{BASE_URL}/{i}.html"
            print(f"Visiting: {url}")
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_selector(".quran")
         
            html = await page.evaluate('document.querySelector(".quran").innerHTML')
            soup = BeautifulSoup(html, "html.parser")
            
            # Obtenir le titre
            a_tag = soup.find("a", {"id": "reading"})
            surah_name = a_tag.text.strip() if a_tag else f"Sourate {i}"
            
            # Supprimer le a_tag du soup pour ne pas l'inclure dans le texte
            if a_tag:
                a_tag.decompose()
            
            # Texte complet avec <br> remplacé par espace
            quran_text = soup.get_text().strip()
            print("Quran text:", quran_text)
            
            # Nettoyer le texte (utiliser le même nom de variable)
            texte_nettoye = quran_text.replace('<br>', ' ').strip()
            print("Text nettoye:", texte_nettoye)
            
            # Normaliser les espaces
            texte_nettoye = re.sub(r'\s+', ' ', texte_nettoye)
            
            # Extraire les versets avec regex : texte + (numéro)
            pattern = r'([^()]+)\((\d+)\)'
            matches = re.findall(pattern, texte_nettoye)
            
            ayahs = []
            for text, num in matches:
                if num == "1":
                    ayahs.append({
                        "number": num,
                        "text": BASMALA + " " + text.strip(),
                        "numberInSurah": int(num),
                        "hizb": None,
                        "tomen": None
                    })
                else:
                    ayahs.append({
                        "number": num,
                        "text": text.strip(),
                        "numberInSurah": int(num),
                        "hizb": None,
                        "tomen": None
                    })
            
            all_surahs.append({
                "number": i,
                "name": surah_name,
                "ayahs": ayahs
            })
        
        await browser.close()
    
    # Sauvegarder en JSON final
    with open("quran_warsh_structured.json", "w", encoding="utf-8") as f:
        json.dump(all_surahs, f, ensure_ascii=False, indent=2)
    
    print(" Fichier 'quran_warsh_structured.json' créé avec succès !")

if __name__ == "__main__":
    import asyncio
    asyncio.run(scrape_quran())