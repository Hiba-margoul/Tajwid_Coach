import re
import unicodedata
import json

# ============================================================================
# CLASSE DE DÉTECTION TĀJWĪD
# ============================================================================

class CompleteTajweedAnalyzer:
    def __init__(self):
        self.solar_letters = "تثدذرزسشصضطظلن"
        self.rules_patterns = self._create_patterns()

    # -------------------- Normalisation & utilitaires -----------------------
    def _normalize(self, text):
        return unicodedata.normalize("NFC", text)

    def is_letter(self, char):
        return not unicodedata.category(char).startswith('M')

    # -------------------- Définition des patterns --------------------------
    def _create_patterns(self):
        return {
            # Nūn Sākinah & Tanwīn
            'ikhfa': [r'ن[ًٌٍْۡ][تثجدفقك]', r'ن[ًٌٍْۡ][سشصضطظ]', r'[ًٌٍ][تثجدفقكسشصضطظ]'],
            'idgham_ghunnah': [r'ن[ًٌٍْۡ][يومن]', r'[ًٌٍ][يومن]'],
            'idgham_bila_ghunnah': [r'ن[ًٌٍْۡ][رل]', r'[ًٌٍ][رل]'],
            'iqlab': [r'ن[ًٌٍْۡ]ب', r'[ًٌٍ]ب', r'نۢب'],
            'izhar': [r'ن[ًٌٍْۡ][ءهعحغخ]', r'[ًٌٍ][ءهعحغخ]'],

            # Mīm Sākinah
            'ikhfa_shafawi': [r'م[ْۡ]ب'],
            'idgham_mithlayn': [r'م[ْۡ]م'],
            'izhar_shafawi': [r'م[ْۡ][^مب]'],

            # Madd
            'madd_muttasil': [r'[اويٰ][ٓ]?ء', r'[اويٰ]ء'],
            'madd_munfasil': [r'[اويٰ]\s+[أإؤئء]'],
            'madd_lazim': [r'[اويٰ][ّ]', r'[اويٰ][ْۡ][^\s]'],
            'madd_arid': [r'[اويٰ][ْۡ]\s'],
            'madd_silah': [r'[َُِ]ه[ۥۦ]'],

            # Lam Sakinah
            'lam_shamsiyya': [rf'(?:ٱ?ل)([{self.solar_letters}])'],
            'lam_qamariyya': [rf'(?:ٱ?ل)([^{self.solar_letters}\s])'],

            # Qalqala
            'qalqala_kubra': [r'[قطبجد][ۡ]\s'],
            'qalqala_sughra': [r'[قطبجد][ۡ][^\s]'],

            # Ghunnah
            'ghunnah': [r'[نم][ّ]', r'[نم][ْۡ][نم]'],

            # Sakt
            'sakt': [r'ۜ'],

            # Tafkhim/Tarqiq
            'tafkhim': [r'[ظطضصغخ][َُ]', r'[ا][ْۡ]?[ظطضصغخ]'],
            'tarqiq': [r'[ظطضصغخ][ِ]']
        }

    def get_category(self, rule):
        categories = {
            'ikhfa': 'nun_tanween', 'idgham_ghunnah': 'nun_tanween',
            'idgham_bila_ghunnah': 'nun_tanween', 'iqlab': 'nun_tanween',
            'izhar': 'nun_tanween',
            'ikhfa_shafawi': 'meem_sakinah', 'idgham_mithlayn': 'meem_sakinah',
            'izhar_shafawi': 'meem_sakinah',
            'madd_muttasil': 'madd', 'madd_munfasil': 'madd', 'madd_lazim': 'madd',
            'madd_arid': 'madd', 'madd_silah': 'madd',
            'lam_shamsiyya': 'lam_sakinah', 'lam_qamariyya': 'lam_sakinah',
            'qalqala_kubra': 'qalqala', 'qalqala_sughra': 'qalqala',
            'ghunnah': 'ghunnah', 'sakt': 'sakt',
            'tafkhim': 'quality', 'tarqiq': 'quality'
        }
        return categories.get(rule, 'other')

    # -------------------- Détecteurs individuels --------------------------
    def detect_nun_sakinah(self, text, pos):
        letter = text[pos]
        next_letter = text[pos+1] if pos+1 < len(text) else ""
        for rule in ['ikhfa','idgham_ghunnah','idgham_bila_ghunnah','iqlab','izhar']:
            for pat in self.rules_patterns[rule]:
                if re.match(pat, text[pos:pos+2]):
                    return rule
        return None

    def detect_meem_sakinah(self, text, pos):
        letter = text[pos]
        next_letter = text[pos+1] if pos+1 < len(text) else ""
        for rule in ['ikhfa_shafawi','idgham_mithlayn','izhar_shafawi']:
            for pat in self.rules_patterns[rule]:
                if re.match(pat, text[pos:pos+2]):
                    return rule
        return None

    def detect_lam_sakinah(self, letter, next_letter):
        for rule in ['lam_shamsiyya','lam_qamariyya']:
            for pat in self.rules_patterns[rule]:
                if re.match(pat, letter + next_letter):
                    return rule
        return None

    def detect_madd(self, text, pos):
        letter = text[pos]
        for rule in ['madd_muttasil','madd_munfasil','madd_lazim','madd_arid','madd_silah']:
            for pat in self.rules_patterns[rule]:
                if re.match(pat, text[pos:pos+2]):
                    return rule
        return None

    def detect_qalqala(self, letter, next_letter):
        for rule in ['qalqala_kubra','qalqala_sughra']:
            for pat in self.rules_patterns[rule]:
                if re.match(pat, letter + next_letter):
                    return rule
        return None

    def detect_ghunnah(self, letter, next_letter):
        for pat in self.rules_patterns['ghunnah']:
            if re.match(pat, letter + next_letter):
                return 'ghunnah'
        return None

    def detect_sakt(self, letter):
        for pat in self.rules_patterns['sakt']:
            if re.match(pat, letter):
                return 'sakt'
        return None

    def detect_quality(self, letter, next_letter):
        for rule in ['tafkhim','tarqiq']:
            for pat in self.rules_patterns[rule]:
                if re.match(pat, letter + next_letter):
                    return rule
        return None

    # -------------------- Pipeline complet --------------------------
    def process_verse(self, verse):
        verse = self._normalize(verse)
        result = []

        for i, letter in enumerate(verse):
            next_letter = verse[i+1] if i+1 < len(verse) else ""
            rule_candidate = None

            # Appliquer tous les détecteurs dans l'ordre correct
            try:
                rule_candidate = self.detect_nun_sakinah(verse, i)
                if not rule_candidate:
                    rule_candidate = self.detect_meem_sakinah(verse, i)
                if not rule_candidate:
                    rule_candidate = self.detect_lam_sakinah(letter, next_letter)
                if not rule_candidate:
                    rule_candidate = self.detect_madd(verse, i)
                if not rule_candidate:
                    rule_candidate = self.detect_qalqala(letter, next_letter)
                if not rule_candidate:
                    rule_candidate = self.detect_ghunnah(letter, next_letter)
                if not rule_candidate:
                    rule_candidate = self.detect_sakt(letter)
                if not rule_candidate:
                    rule_candidate = self.detect_quality(letter, next_letter)
            except Exception as e:
                print(f"Erreur à la position {i}: {e}")

            result.append({
                "position": i,
                "letter": letter,
                "rule": rule_candidate,
                "category": self.get_category(rule_candidate),
                "context": verse[max(0,i-3):i+4]
            })

        return result

    # -------------------- Statistiques --------------------------
    def summarize(self, verse):
        rules = self.process_verse(verse)
        rule_counts, category_counts = {}, {}
        for r in rules:
            if r["rule"]:
                rule_counts[r["rule"]] = rule_counts.get(r["rule"], 0) + 1
                category_counts[r["category"]] = category_counts.get(r["category"], 0) + 1

        return {
            "verse": verse,
            "summary": {
                "total_rules": sum(rule_counts.values()),
                "rule_density": sum(rule_counts.values()) / len(verse),
                "by_category": category_counts
            },
            "detailed_rules": rules,
            "complex_segments": self.find_complex_segments(rules)
        }

    def find_complex_segments(self, rules, min_rules=2):
        segments, current = [], []
        for r in rules:
            if r["rule"]:
                current.append(r)
            else:
                if len(current) >= min_rules:
                    segments.append({
                        "start": current[0]["position"],
                        "end": current[-1]["position"],
                        "letters": ''.join([c["letter"] for c in current]),
                        "rules": [c["rule"] for c in current]
                    })
                current = []
        if len(current) >= min_rules:
            segments.append({
                "start": current[0]["position"],
                "end": current[-1]["position"],
                "letters": ''.join([c["letter"] for c in current]),
                "rules": [c["rule"] for c in current]
            })
        return segments


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    analyzer = CompleteTajweedAnalyzer()
    verse = "إِنَّ اللَّهَ اصْطَفَى آدَمَ وَنُوحًا وَآلَ إِبْرَاهِيمَ وَآلَ مُوسَى وَآلَ عِيسَى"
    result = analyzer.summarize(verse)
    print(json.dumps(result, ensure_ascii=False, indent=4))
