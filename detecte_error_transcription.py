import re
import unicodedata
import difflib

# --- Liste complète des diacritiques arabes et coraniques ---
DIACRITIQUES = ''.join([
    '\u0610', '\u0611', '\u0612', '\u0613', '\u0614',
    '\u0615', '\u0616', '\u0617', '\u0618', '\u0619', '\u061A',
    '\u064B', '\u064C', '\u064D', '\u064E', '\u064F',
    '\u0650', '\u0651', '\u0652', '\u0653', '\u0654', '\u0655',
    '\u0656', '\u0657', '\u0658', '\u0659', '\u065A',
    '\u065B', '\u065C', '\u065D', '\u065E', '\u065F',
    '\u0670'
])

# --- Normalisation des hamzas et variantes orthographiques ---
HAMZA_EQUIV = {
    'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا',
    'ؤ': 'و', 'ئ': 'ي',
}

def normaliser_texte(texte, enlever_diacritiques=False):
    """
    Normalise le texte arabe :
    - supprime ou garde les diacritiques selon le paramètre
    - unifie les hamzas (إ، أ، آ...) en leur base
    - supprime espaces et caractères non arabes
    """
    texte_norm = texte
    # Unification des hamzas
    for k, v in HAMZA_EQUIV.items():
        texte_norm = texte_norm.replace(k, v)
    
    # Suppression des diacritiques si demandé
    if enlever_diacritiques:
        texte_norm = re.sub(f"[{DIACRITIQUES}]", "", texte_norm)
    
    # Nettoyage : seulement lettres arabes
    texte_norm = re.sub(r"[^ء-ي ]", "", texte_norm)
    texte_norm = texte_norm.replace(" ", "")
    
    return texte_norm


def extraire_diacritiques(texte):
    """Retourne la liste de tous les diacritiques trouvés dans le texte."""
    return re.findall(f"[{DIACRITIQUES}]", texte)


def comparer_textes_complets(transcription, reference):
    """
    Compare la transcription ASR au texte original du Qurʾān :
    - lettres sans diacritiques
    - diacritiques (ḥarakāt)
    - score global
    """
    # --- Étape 1 : comparaison des lettres (sans diacritiques) ---
    ref_lettres = normaliser_texte(reference, enlever_diacritiques=True)
    trans_lettres = normaliser_texte(transcription, enlever_diacritiques=True)

    seq = difflib.SequenceMatcher(None, ref_lettres, trans_lettres)
    taux_lettres = round(seq.ratio() * 100, 2)

    # --- Étape 2 : comparaison des diacritiques ---
    diac_ref = extraire_diacritiques(reference)
    diac_trans = extraire_diacritiques(transcription)
    n = min(len(diac_ref), len(diac_trans))
    corrects = sum(1 for i in range(n) if diac_ref[i] == diac_trans[i])
    erreurs = len(diac_ref) - corrects
    taux_diacritiques = round((corrects / len(diac_ref) * 100), 2) if diac_ref else 0

    # --- Étape 3 : score global ---
    taux_global = round((taux_lettres * 0.7 + taux_diacritiques * 0.3), 2)

    # --- Rapport détaillé ---
    details = []
    for i in range(n):
        if diac_ref[i] != diac_trans[i]:
            try:
                nom_ref = unicodedata.name(diac_ref[i])
                nom_trans = unicodedata.name(diac_trans[i])
            except ValueError:
                nom_ref = nom_trans = "(nom inconnu)"
            details.append({
                "position": i + 1,
                "diacritique_original": diac_ref[i],
                "nom_original": nom_ref,
                "diacritique_transcrit": diac_trans[i],
                "nom_transcrit": nom_trans
            })
    
    return {
        "Taux lettres (%)": taux_lettres,
        "Taux diacritiques (%)": taux_diacritiques,
        "Score global (%)": taux_global,
        "Diacritiques corrects": corrects,
        "Diacritiques erreurs": erreurs,
        "Total diacritiques": len(diac_ref),
        "Détails erreurs diacritiques": details
    }


# 🧪 Exemple d’utilisation :
texte_original = "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ"
transcription = "انا اعطيناك الكوثر"

resultat = comparer_textes_complets(transcription, texte_original)
for k, v in resultat.items():
    print(f"{k}: {v}")
