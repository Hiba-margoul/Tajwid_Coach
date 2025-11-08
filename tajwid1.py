import re
import unicodedata
import json
from typing import List, Dict, Set

class EnhancedTajweedAnalyzer:
    """Analyseur de Tajwid amélioré avec règles étendues"""
    
    def __init__(self):
        self.character_categories = self._initialize_character_categories()
        self.rules = self._initialize_enhanced_rules()
        self.normalization_cache = {}
    
    def _initialize_character_categories(self) -> Dict[str, str]:
        """Catégories de caractères étendues"""
        return {
            'solar_letters': "تثدذرزسشصضطظلن",
            'lunar_letters': "ابجحخعغفقكلمنهويء",
            'huroof_halaq': "ءهعحغخ",
            'huroof_idgham_ghunnah': "يومن",
            'huroof_idgham_bila_ghunnah': "رل",
            'huroof_iqlab': "ب",
            'huroof_ikhfa': "تثجدفقكطظضصشسذز",
            'huroof_qalqala': "قطبجد",
            'huroof_madd': "اوي",
            'huroof_ghunnah': "نم"
        }
    
    def _initialize_enhanced_rules(self) -> Dict[str, List[str]]:
        """Règles étendues avec patterns améliorés"""
        cats = self.character_categories
        
        return {
            # أحكام النون الساكنة والتنوين - محسنة
            'izhar_hulqi': [
                r'ن[ًٌٍْ][ءهعحغخ]',
                r'[ًٌٍ][ءهعحغخ]',
                r'ن[ۡ][ءهعحغخ]'
            ],
            'idgham_ghunnah': [
                r'ن[ًٌٍْ][يومن]',
                r'[ًٌٍ][يومن]',
                r'ن[ۡ][يومن]'
            ],
            'idgham_bila_ghunnah': [
                r'ن[ًٌٍْ][رل]',
                r'[ًٌٍ][رل]',
                r'ن[ۡ][رل]'
            ],
            'iqlab': [
                r'ن[ًٌٍْ]ب',
                r'[ًٌٍ]ب',
                r'ن[ۡ]ب',
                r'نۢب'
            ],
            'ikhfa': [
                r'ن[ًٌٍْ][' + cats['huroof_ikhfa'] + ']',
                r'[ًٌٍ][' + cats['huroof_ikhfa'] + ']',
                r'ن[ۡ][' + cats['huroof_ikhfa'] + ']'
            ],
            
            # أحكام الميم الساكنة - محسنة
            'ikhfa_shafawi': [
                r'م[ْ]ب',
                r'م[ۡ]ب'
            ],
            'idgham_mithlayn': [
                r'م[ْ]م',
                r'م[ۡ]م'
            ],
            'izhar_shafawi': [
                r'م[ْ][^مب]',
                r'م[ۡ][^مب]'
            ],
            
            # أحكام المدود - موسعة
            'madd_tabii': [
                r'[اوي][^ّْۡ\s]',
                r'[اويٰ][^ّْۡ\s]'
            ],
            'madd_muttasil': [
                r'[اوي]ء\w',
                r'[اويٰ]ء\w',
                r'[اوي][ٓ]ء'
            ],
            'madd_munfasil': [
                r'[اوي]\s+[أإؤئء]',
                r'[اويٰ]\s+[أإؤئء]'
            ],
            'madd_lazim': [
                r'[اوي][ّ]',
                r'[اويٰ][ّ]',
                r'[اوي][ْ]\w',
                r'[اويٰ][ْ]\w'
            ],
            'madd_arid': [
                r'[اوي][ْ]\s',
                r'[اويٰ][ْ]\s'
            ],
            
            # أحكام الراء - محسنة
            'tafkhim_ra': [
                r'ر[َُ]',
                r'ر[ْۡ][^ِ]',
                r'ر[َّ][^ِ]'
            ],
            'tarqiq_ra': [
                r'ر[ِ]',
                r'ر[ْۡ][ِ]',
                r'ر[َّ][ِ]'
            ],
            
            # القلقلة - موسعة
            'qalqala': [
                r'[قطبجد][ْ]',
                r'[قطبجد][ۡ]',
                r'[قطبجد][َّ]'
            ],
            
            # الغنة - موسعة
            'ghunnah': [
                r'[نم][ّ]',
                r'[نم][َّ]',
                r'ن[ْ][يومنب]',
                r'ن[ۡ][يومنب]'
            ],
            
            # أحكام خاصة بالهمزات
            'hamzat_wasl': [
                r'ٱ\w+',
                r'ا(?:ست|ن|م|ت|ف|س|ي|ا)\w+'
            ],
            'hamzat_qat': [
                r'[أإ][^\s]'
            ]
        }
    
    def _normalize(self, text: str) -> str:
        """Normalisation améliorée"""
        if text in self.normalization_cache:
            return self.normalization_cache[text]
        
        # Remplacer les caractères spéciaux du Coran
        replacements = {
            '۪': '', 'ۥ': '', 'ۖ': '', 'ۗ': '', 'ۘ': '', 'ۙ': '', 'ۚ': '', 'ۛ': '', 'ۜ': '',
            'ٞ': '', 'ٰ': 'ا', 'ۦ': '', 'ۭ': '', '۫': '', '۬': '', '۩': '', 'ۨ': '', 'ۧ': '',
            '۠': '', 'ۡ': 'ْ', 'ۢ': '', 'ۣ': '', 'ۤ': '', 'ۥ': '', 'ۦ': '', 'ۧ': '', 'ۨ': '',
            '۩': '', '۪': '', '۫': '', '۬': '', 'ۭ': '', 'ۮ': '', 'ۯ': ''
        }
        
        normalized = unicodedata.normalize("NFC", text)
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        self.normalization_cache[text] = normalized
        return normalized
    
    def get_rule_explanation(self, rule_name: str) -> str:
        """Explications étendues des règles"""
        explanations = {
            'izhar_hulqi': 'الإظهار الحلقي: إظهار النون الساكنة أو التنوين عند حروف الحلق (ء، ه، ع، ح، غ، خ)',
            'idgham_ghunnah': 'الإدغام بغنة: إدغام النون الساكنة أو التنوين في الياء، الواو، الميم، النون مع الغنة',
            'idgham_bila_ghunnah': 'الإدغام بلا غنة: إدغام النون الساكنة أو التنوين في الراء، اللام بدون غنة',
            'iqlab': 'الإقلاب: قلب النون الساكنة أو التنوين ميماً مع الغنة عند الباء',
            'ikhfa': 'الإخفاء: إخفاء النون الساكنة أو التنوين عند الحروف الباقية مع الغنة',
            'ikhfa_shafawi': 'الإخفاء الشفوي: إخفاء الميم الساكنة عند الباء مع الغنة',
            'idgham_mithlayn': 'إدغام المثلين الصغير: إدغام الميم الساكنة في الميم',
            'izhar_shafawi': 'الإظهار الشفوي: إظهار الميم الساكنة عند جميع الحروف عدا الباء والميم',
            'madd_tabii': 'المد الطبيعي: مد حروف المد (ا، و، ي) بمقدار حركتين',
            'madd_muttasil': 'المد المتصل: وجوب المد عندما يلتقي حرف المد مع الهمزة في كلمة واحدة',
            'madd_munfasil': 'المد المنفصل: جواز المد عندما يلتقي حرف المد مع الهمزة في كلمتين',
            'madd_lazim': 'المد اللازم: وجوب المد بمقدار ست حركات عند وجود سكون أصلي',
            'madd_arid': 'المد العارض للسكون: جواز المد عند الوقف على حرف المد',
            'tafkhim_ra': 'تفخيم الراء: تغليظ صوت الراء عند الفتح أو الضم أو السكون بعد فتح أو ضم',
            'tarqiq_ra': 'ترقيق الراء: ترقيق صوت الراء عند الكسر أو السكون بعد كسر',
            'qalqala': 'القلقلة: اهتزاز الصوت عند النطق بحرف ساكن من حروف قطب جد',
            'ghunnah': 'الغنة: صوت يخرج من الخيشوم في النون والميم المشددتين وفي الإدغام والإقلاب',
            'hamzat_wasl': 'همزة الوصل: تسقط عند الوصل وتثبت عند الابتداء',
            'hamzat_qat': 'همزة القطع: تثبت وصلاً وابتداء'
        }
        return explanations.get(rule_name, "شرح غير متوفر")
    
    def _check_lam_rules(self, text: str, position: int) -> List[Dict]:
        """Vérification améliorée des règles de Lam"""
        rules_found = []
        
        # Vérifier Lam Shamsiyya/Qamariya
        if position > 0 and text[position] == 'ل':
            # Vérifier le contexte "ال"
            if position >= 2 and text[position-2:position] == "ال":
                if position + 1 < len(text):
                    next_char = text[position+1]
                    if next_char in self.character_categories['solar_letters']:
                        rules_found.append({
                            'rule': 'lam_shamsiyya',
                            'explanation': 'لام شمسية: إدغام اللام الساكنة في الحرف الشمسي التالي',
                            'context': text[max(0, position-2):min(len(text), position+3)]
                        })
                    elif next_char in self.character_categories['lunar_letters']:
                        rules_found.append({
                            'rule': 'lam_qamariyya',
                            'explanation': 'لام قمرية: إظهار اللام الساكنة عند الحروف القمرية',
                            'context': text[max(0, position-2):min(len(text), position+3)]
                        })
        
        return rules_found
    
    def _check_special_cases(self, text: str, position: int) -> List[Dict]:
        """Vérification des cas spéciaux"""
        rules_found = []
        char = text[position]
        context = text[max(0, position-2):min(len(text), position+3)]
        
        # Vérifier les cas spéciaux de Madd
        if char in self.character_categories['huroof_madd']:
            # Vérifier Madd Munfasil (entre deux mots)
            if position > 0 and text[position-1].isspace():
                if position + 1 < len(text) and text[position+1] in ['أ', 'إ', 'ء']:
                    rules_found.append({
                        'rule': 'madd_munfasil',
                        'explanation': self.get_rule_explanation('madd_munfasil'),
                        'context': context
                    })
        
        # Vérifier les cas de Ghunnah supplémentaires
        if char in self.character_categories['huroof_ghunnah']:
            if position + 1 < len(text) and text[position+1] in ['ّ', 'َّ']:
                rules_found.append({
                    'rule': 'ghunnah',
                    'explanation': self.get_rule_explanation('ghunnah'),
                    'context': context
                })
        
        return rules_found
    
    def analyze_character(self, text: str, position: int) -> Dict:
        """Analyse de caractère améliorée"""
        char = text[position]
        context = text[max(0, position-2):min(len(text), position+3)]
        
        detected_rules = []
        used_rules = set()
        
        # Vérifier toutes les règles standards
        for rule_name, pattern_list in self.rules.items():
            if rule_name in used_rules:
                continue
                
            for pattern in pattern_list:
                # Vérifier à partir de la position actuelle
                text_to_check = text[position:]
                match = re.search(pattern, text_to_check)
                
                if match and match.start() == 0:
                    detected_rules.append({
                        'rule': rule_name,
                        'explanation': self.get_rule_explanation(rule_name),
                        'context': context
                    })
                    used_rules.add(rule_name)
                    break
        
        # Vérifier les règles spéciales de Lam
        lam_rules = self._check_lam_rules(text, position)
        for lam_rule in lam_rules:
            if lam_rule['rule'] not in used_rules:
                detected_rules.append(lam_rule)
                used_rules.add(lam_rule['rule'])
        
        # Vérifier les cas spéciaux
        special_rules = self._check_special_cases(text, position)
        for special_rule in special_rules:
            if special_rule['rule'] not in used_rules:
                detected_rules.append(special_rule)
                used_rules.add(special_rule['rule'])
        
        return {
            'position': position,
            'character': char,
            'rules': detected_rules,
            'total_rules': len(detected_rules),
            'context': context
        }
    
    def analyze_verse(self, verse: str) -> Dict:
        """Analyse de verset améliorée"""
        verse = self._normalize(verse)
        analysis_results = []
        
        i = 0
        while i < len(verse):
            if verse[i].isspace():
                i += 1
                continue
                
            char_analysis = self.analyze_character(verse, i)
            analysis_results.append(char_analysis)
            i += 1
        
        return {
            'verse': verse,
            'analysis': analysis_results,
            'statistics': self._generate_statistics(analysis_results),
            'summary': self._generate_summary(analysis_results)
        }
    
    def _generate_statistics(self, analysis_results: List[Dict]) -> Dict:
        """Génération de statistiques améliorée"""
        total_rules = sum(result['total_rules'] for result in analysis_results)
        total_chars = len(analysis_results)
        
        rules_by_type = {}
        for result in analysis_results:
            for rule in result['rules']:
                rule_name = rule['rule']
                rules_by_type[rule_name] = rules_by_type.get(rule_name, 0) + 1
        
        return {
            'total_characters': total_chars,
            'total_rules_detected': total_rules,
            'rules_by_type': rules_by_type,
            'rules_by_category': self._categorize_rules(analysis_results),
            'accuracy_score': self._calculate_accuracy(total_rules, total_chars),
            'rule_density': total_rules / total_chars if total_chars > 0 else 0
        }
    
    def _categorize_rules(self, analysis_results: List[Dict]) -> Dict[str, int]:
        """Catégorisation améliorée"""
        categories = {
            'nun_tanween': ['izhar_hulqi', 'idgham_ghunnah', 'idgham_bila_ghunnah', 'iqlab', 'ikhfa'],
            'meem_sakinah': ['ikhfa_shafawi', 'idgham_mithlayn', 'izhar_shafawi'],
            'madd': ['madd_tabii', 'madd_muttasil', 'madd_munfasil', 'madd_lazim', 'madd_arid'],
            'lam': ['lam_shamsiyya', 'lam_qamariyya'],
            'quality': ['tafkhim_ra', 'tarqiq_ra', 'qalqala', 'ghunnah'],
            'hamz': ['hamzat_wasl', 'hamzat_qat']
        }
        
        category_counts = {category: 0 for category in categories.keys()}
        category_counts['other'] = 0
        
        for result in analysis_results:
            for rule in result['rules']:
                rule_name = rule['rule']
                found = False
                for category, rules in categories.items():
                    if rule_name in rules:
                        category_counts[category] += 1
                        found = True
                        break
                if not found:
                    category_counts['other'] += 1
        
        return category_counts
    
    def _calculate_accuracy(self, total_rules: int, total_chars: int) -> str:
        """Calcul de précision amélioré"""
        if total_chars == 0:
            return "Non calculable"
        
        rule_density = total_rules / total_chars
        
        if rule_density > 0.6:
            return "منخفضة - اكتشاف مفرط"
        elif rule_density > 0.4:
            return "متوسطة - يحتاج تحسين"
        elif rule_density > 0.15:
            return "جيدة - مقبولة"
        else:
            return "عالية - ممتازة"
    
    def _generate_summary(self, analysis_results: List[Dict]) -> Dict:
        """Résumé amélioré"""
        unique_rules = set()
        total_rules = 0
        
        for result in analysis_results:
            total_rules += result['total_rules']
            for rule in result['rules']:
                unique_rules.add(rule['rule'])
        
        # Niveau de complexité
        if total_rules > 25:
            complexity = "عالي جداً"
        elif total_rules > 15:
            complexity = "عالي"
        elif total_rules > 8:
            complexity = "متوسط"
        elif total_rules > 3:
            complexity = "منخفض"
        else:
            complexity = "بسيط"
        
        # Règles notables
        notable_rules = ['idgham_ghunnah', 'iqlab', 'ikhfa', 'madd_muttasil', 'madd_lazim', 'qalqala']
        found_notable = [rule for rule in unique_rules if rule in notable_rules]
        
        return {
            'total_rules': total_rules,
            'unique_rules': list(unique_rules),
            'complexity_level': complexity,
            'notable_rules': found_notable,
            'unique_rules_count': len(unique_rules)
        }

# Test avec le verset complexe
if __name__ == "__main__":
    analyzer = EnhancedTajweedAnalyzer()
    
    complex_verse = "فَلَمَّا ر۪ء۪ا قَمِيصَهُۥ قُدَّ مِن دُبُرٖ قَالَ إِنَّهُۥ مِن كَيْدِكُنَّ إِنَّ كَيْدَكُنَّ عَظِيمٞۖ"
    
    print("🔍 Analyseur de Tajwid Amélioré")
    print("=" * 60)
    print(f"Verset: {complex_verse}")
    print("-" * 60)
    
    result = analyzer.analyze_verse(complex_verse)
    
    # Afficher les règles détectées
    rules_found = False
    for analysis in result['analysis']:
        if analysis['rules']:
            rules_found = True
            print(f"\nالحرف '{analysis['character']}' (الموضع {analysis['position']}):")
            for rule in analysis['rules']:
                print(f"  - {rule['rule']}: {rule['explanation']}")
    
    if not rules_found:
        print("لم يتم العثور على قواعد تجويد")
    
    # Statistiques
    stats = result['statistics']
    print(f"\n📊 الإحصائيات:")
    print(f"  - عدد الحروف: {stats['total_characters']}")
    print(f"  - عدد القواعد: {stats['total_rules_detected']}")
    print(f"  - الدقة: {stats['accuracy_score']}")
    print(f"  - الكثافة: {stats['rule_density']:.3f}")
    print(f"  - توزيع القواعد: {stats['rules_by_type']}")
    
    summary = result['summary']
    print(f"\n📈 الملخص:")
    print(f"  - مستوى التعقيد: {summary['complexity_level']}")
    print(f"  - القواعد الفريدة: {summary['unique_rules']}")
    if summary['notable_rules']:
        print(f"  - القواعد البارزة: {summary['notable_rules']}")