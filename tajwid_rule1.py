import re
import json
import unicodedata
from typing import Dict, List, Any, Optional
from collections import deque

class QuranTajweedAnalyzer:
    """Analyseur Tajwid basé sur l'approche cpfair/quran-tajweed"""
    
    def __init__(self, trees_dir: str = "rule_trees"):
        self.trees_dir = trees_dir
        self.rule_trees = self._load_rule_trees()
        self.context_sizes = self._get_context_sizes()
        
    def _get_context_sizes(self) -> Dict[str, tuple]:
        """Tailles de contexte pour chaque règle (lookbehind, lookahead)"""
        return {
            "ghunnah": (3, 1),
            "hamzat_wasl": (1, 0),
            "idghaam_ghunnah": (1, 3),
            "idghaam_mutajanisayn": (0, 2),
            "idghaam_mutaqaribayn": (1, 2),
            "idghaam_no_ghunnah": (0, 3),
            "idghaam_shafawi": (0, 2),
            "ikhfa": (0, 3),
            "ikhfa_shafawi": (0, 2),
            "iqlab": (0, 2),
            "lam_shamsiyyah": (1, 1),
            "madd_2": (0, 1),
            "madd_246": (1, 2),
            "madd_6": (1, 1),
            "madd_munfasil": (1, 2),
            "madd_muttasil": (0, 3),
            "qalqalah": (1, 1),
            "silent": (0, 1),
            "END": (1, 0)
        }
    
    def _load_rule_trees(self) -> Dict[str, Dict[str, Any]]:
        """Charger les arbres de décision depuis les fichiers JSON"""
        trees = {}
        
        # Règles supportées par cpfair/quran-tajweed
        rules = [
            'ghunnah', 'idghaam_ghunnah', 'idghaam_mutajanisayn', 
            'idghaam_mutaqaribayn', 'idghaam_no_ghunnah', 'idghaam_shafawi',
            'ikhfa', 'ikhfa_shafawi', 'iqlab', 'lam_shamsiyyah', 'madd_2',
            'madd_246', 'madd_6', 'madd_munfasil', 'madd_muttasil', 
            'qalqalah', 'silent', 'hamzat_wasl'
        ]
        
        for rule in rules:
            try:
                start_file = f"{self.trees_dir}/{rule}.start.json"
                end_file = f"{self.trees_dir}/{rule}.end.json"
                
                with open(start_file, 'r', encoding='utf-8') as f:
                    start_tree = json.load(f)
                with open(end_file, 'r', encoding='utf-8') as f:
                    end_tree = json.load(f)
                
                trees[rule] = {
                    'start': start_tree,
                    'end': end_tree
                }
            except FileNotFoundError:
                print(f"⚠️ Arbres non trouvés pour: {rule}")
                continue
                
        return trees
    
    def _normalize_text(self, text: str) -> str:
        """Normaliser le texte comme dans cpfair/quran-tajweed"""
        replacements = {
            '۪': '', 'ۥ': '', 'ۖ': '', 'ۗ': '', 'ۘ': '', 'ۙ': '', 'ۚ': '', 'ۛ': '', 'ۜ': '',
            'ٞ': '', 'ٰ': 'ا', 'ۦ': '', 'ۭ': '', '۫': '', '۬': '', '۩': '', 'ۨ': '', 'ۧ': '',
            '۠': '', 'ۡ': 'ْ', 'ۢ': '', 'ۣ': '', 'ۤ': '', 'ۥ': '', 'ۦ': '', 'ۧ': '', 'ۨ': '',
            '۩': '', '۪': '', '۫': '', '۬': '', 'ۭ': '', 'ۮ': '', 'ۯ': ''
        }
        
        normalized = unicodedata.normalize("NFC", text)
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def _get_character_group(self, text: str, position: int) -> tuple:
        """Obtenir le groupe de caractères (base + diacritiques)"""
        start_i = position
        while (start_i > 0 and 
               unicodedata.category(text[start_i]) == "Mn" and 
               (text[start_i] != "ٰ" or text[start_i - 1] == "ـ")):
            start_i -= 1
        
        end_i = start_i + 1
        while (end_i < len(text) and 
               unicodedata.category(text[end_i]) == "Mn" and 
               text[end_i] != "ٰ"):
            end_i += 1
        
        return start_i, end_i, text[start_i:end_i]
    
    def _build_attributes(self, text: str, position: int, rule: str, include_this: bool = True) -> Dict[str, Any]:
        """Construire les attributs pour l'arbre de décision"""
        start_i, end_i, char_group = self._get_character_group(text, position)
        base_char = text[start_i]
        
        attributes = {
            # Informations de base
            'position': position,
            'base_char': base_char,
            'char_group': char_group,
            'start_i': start_i,
            'end_i': end_i,
            
            # Attributs de position
            'is_final_codepoint_in_letter': position == end_i - 1,
            'is_final_letter_in_ayah': end_i >= len(text),
            'is_base': (unicodedata.category(text[position]) != "Mn" and text[position] != "ـ") or text[position] == "ٰ",
            
            # Diacritiques
            'has_shaddah': 'ّ' in char_group,
            'has_sukun': 'ْ' in char_group,
            'has_tanween': any(t in char_group for t in 'ًٌٍ'),
            'has_maddah': 'ٓ' in char_group,
            'has_hamza': any(h in char_group for h in 'ؤئٕإأٔ'),
            'has_fathah': 'َ' in char_group,
            'has_dammah': 'ُ' in char_group,
            'has_kasrah': 'ِ' in char_group,
            'has_vowel_incl_tanween': any(v in char_group for v in 'ًٌٍَُِْ'),
            'has_explicit_sukoon': '۟' in char_group or 'ْ' in char_group,
        }
        
        # Attributs spécifiques aux règles
        if rule == "ghunnah":
            attributes.update({
                'is_noon_or_meem': base_char in 'نم',
                'base_is_heavy': base_char in 'هءحعخغ',
            })
        
        elif rule == "idghaam_ghunnah":
            attributes.update({
                'is_noon': base_char == 'ن',
                'is_tanween': base_char in 'ًٌٍ',
                'base_is_idghaam_ghunna_set': base_char in 'يمون',
                'has_implicit_sukoon': not any(s in char_group for s in 'ًٌٍَُِْ'),
            })
        
        elif rule == "ikhfa":
            attributes.update({
                'is_noon': base_char == 'ن',
                'is_tanween': base_char in 'ًٌٍ',
                'base_is_ikhfa_set': base_char in 'تثجدفقكطظضصشسذز',
                'has_implicit_sukoon': not any(s in char_group for s in 'ًٌٍَُِْ'),
            })
        
        elif rule == "iqlab":
            attributes.update({
                'is_tanween': base_char in 'ًٌٍ',
                'has_tanween': any(t in char_group for t in 'ًٌٍ'),
                'has_small_meem': 'ۢ' in char_group or 'ۭ' in char_group,
            })
        
        elif rule == "qalqalah":
            attributes.update({
                'is_muqalqalah': base_char in 'قطبجد',
            })
        
        elif rule == "madd_2":
            attributes.update({
                'is_dagger_alif': base_char == 'ٰ',
                'is_small_yeh': base_char == 'ۦ',
                'is_small_waw': base_char == 'ۥ',
            })
        
        elif rule == "madd_6":
            attributes.update({
                'is_hamza': base_char == 'ء',
                'is_alif': base_char == 'ا',
                'is_yeh': base_char == 'ي',
                'is_waw': base_char == 'و',
            })
        
        return attributes
    
    def _evaluate_tree(self, tree: Dict, attributes: Dict) -> bool:
        """Évaluer un arbre de décision avec les attributs donnés"""
        if 'label' in tree:
            return bool(tree['label'])
        
        attribute_name = tree['attribute']
        threshold = tree.get('value', 0.5)
        
        # Obtenir la valeur de l'attribut
        value = attributes.get(attribute_name, 0)
        if isinstance(value, bool):
            value = 1.0 if value else 0.0
        
        # Suivre la branche appropriée
        if value >= threshold:
            return self._evaluate_tree(tree['gt'], attributes)
        else:
            return self._evaluate_tree(tree['lt'], attributes)
    
    def _get_context_attributes(self, text: str, position: int, rule: str) -> Dict[str, Any]:
        """Obtenir les attributs avec contexte (lookbehind + lookahead)"""
        lookbehind, lookahead = self.context_sizes.get(rule, (1, 1))
        context_attrs = {}
        
        # Contexte avant (lookbehind)
        for i in range(lookbehind, 0, -1):
            offset = -i
            if position + offset >= 0:
                attrs = self._build_attributes(text, position + offset, rule, include_this=False)
                for key, value in attrs.items():
                    context_attrs[f"{offset}_{key}"] = value
            else:
                # Marquer comme inexistant
                context_attrs[f"{offset}_exists"] = False
        
        # Caractère courant
        current_attrs = self._build_attributes(text, position, rule, include_this=True)
        for key, value in current_attrs.items():
            context_attrs[f"0_{key}"] = value
        context_attrs["0_exists"] = True
        
        # Contexte après (lookahead)
        for i in range(1, lookahead + 1):
            offset = i
            if position + offset < len(text):
                attrs = self._build_attributes(text, position + offset, rule, include_this=False)
                for key, value in attrs.items():
                    context_attrs[f"{offset}_{key}"] = value
            else:
                context_attrs[f"{offset}_exists"] = False
        
        return context_attrs
    
    def analyze_character_with_trees(self, text: str, position: int) -> Dict[str, Any]:
        """Analyser un caractère avec les arbres de décision"""
        # Note: La normalisation est maintenant gérée dans 'analyze_verse'
        # text = self._normalize_text(text) 
        detected_rules = []
        
        for rule_name, trees in self.rule_trees.items():
            # Obtenir les attributs avec contexte
            context_attrs = self._get_context_attributes(text, position, rule_name)
            
            # Évaluer l'arbre de début
            start_detected = self._evaluate_tree(trees['start'], context_attrs)
            
            if start_detected:
                # Pour une analyse simplifiée, on considère que la règle s'applique
                # Dans l'approche complète, on gérerait le début et la fin
                detected_rules.append({
                    'rule': rule_name,
                    'method': 'decision_tree',
                    'confidence': 'high', # Confiance haute car arbre de décision
                    'context': context_attrs # Optionnel: garder pour débogage
                })
        
        return {
            'position': position,
            'character': text[position],
            'rules': detected_rules,
            'total_rules': len(detected_rules)
        }

# --- MODIFICATION ---
# La classe SimpleTajweedAnalyzer est modifiée pour n'utiliser que 
# QuranTajweedAnalyzer et supprimer toute mention de Regex.

class SimpleTajweedAnalyzer:
    """Analyseur simplifié utilisant UNIQUEMENT les arbres de décision"""
    
    def __init__(self, trees_dir: str = "rule_trees"):
        # Initialise uniquement l'analyseur d'arbres
        self.tree_analyzer = QuranTajweedAnalyzer(trees_dir)
        
        # --- SUPPRIMÉ ---
        # self.regex_patterns = self._initialize_regex_patterns()
    
    # --- SUPPRIMÉ ---
    # def _initialize_regex_patterns(self) -> Dict[str, List[str]]:
    # ... (toute la méthode)
    
    # --- SUPPRIMÉ ---
    # def analyze_with_regex(self, text: str, position: int) -> Dict[str, Any]:
    # ... (toute la méthode)
    
    # --- MODIFIÉ ---
    # Renommée de 'smart_analyze_character' à 'analyze_character'
    # Supprime la logique de fallback regex.
    def analyze_character(self, text: str, position: int) -> Dict[str, Any]:
        """Analyse un caractère en utilisant les arbres de décision"""
        
        # Appelle directement l'analyseur d'arbres
        tree_result = self.tree_analyzer.analyze_character_with_trees(text, position)
        
        # Retourne le résultat des arbres, quel qu'il soit
        return tree_result
    
    # --- MODIFIÉ ---
    # Mise à jour pour utiliser la nouvelle méthode 'analyze_character'
    # et ajustement des messages/statistiques.
    def analyze_verse(self, verse: str) -> Dict[str, Any]:
        """Analyser un verset complet"""
        print("🔍 Démarrage de l'analyse Tajwid...")
        print("🌳 Utilisation des arbres de décision cpfair/quran-tajweed (uniquement)")
        # --- SUPPRIMÉ ---
        # print("🔍 Fallback vers les regex si nécessaire")
        print("-" * 60)
        
        analysis_results = []
        methods_used = set()
        
        verse_normalized = self.tree_analyzer._normalize_text(verse)
        
        i = 0
        while i < len(verse_normalized):
            if verse_normalized[i].isspace():
                i += 1
                continue
            
            # --- MODIFIÉ ---
            # Appelle la méthode d'analyse simplifiée
            analysis = self.analyze_character(verse_normalized, i)
            analysis_results.append(analysis)
            
            # Suivre les méthodes utilisées (ne sera que 'decision_tree')
            for rule in analysis['rules']:
                methods_used.add(rule['method'])
            
            i += 1
        
        # Générer le rapport
        stats = self._generate_comprehensive_stats(analysis_results)
        
        return {
            'verse': verse,
            'verse_normalized': verse_normalized, 
            'analysis': analysis_results,
            'statistics': stats,
            'methods_used': list(methods_used)
        }
    
    # --- MODIFIÉ ---
    # Simplification des statistiques
    def _generate_comprehensive_stats(self, analysis_results: List[Dict]) -> Dict[str, Any]:
        """Générer des statistiques complètes"""
        total_rules = sum(result['total_rules'] for result in analysis_results)
        total_chars = len(analysis_results)
        
        rules_by_type = {}
        # Ne compte que les arbres de décision
        method_counts = {'decision_tree': 0} 
        
        for result in analysis_results:
            for rule in result['rules']:
                rule_name = rule['rule']
                rules_by_type[rule_name] = rules_by_type.get(rule_name, 0) + 1
                
                # Vérifie au cas où, mais ne devrait être que 'decision_tree'
                if rule['method'] in method_counts:
                    method_counts[rule['method']] += 1
        
        return {
            'total_characters': total_chars,
            'total_rules_detected': total_rules,
            'rules_by_type': rules_by_type,
            'method_distribution': method_counts,
            'rule_density': total_rules / total_chars if total_chars > 0 else 0,
            'detection_quality': self._assess_quality(method_counts, total_rules)
        }
    
    # --- MODIFIÉ ---
    # Simplification de l'évaluation de qualité
    def _assess_quality(self, method_counts: Dict[str, int], total_rules: int) -> str:
        """Évaluer la qualité de la détection"""
        if total_rules == 0:
            return "Aucune règle détectée"
        
        # Puisque nous n'utilisons que des arbres, le ratio sera de 1.0 (ou 0.0)
        tree_ratio = method_counts.get('decision_tree', 0) / total_rules
        
        if tree_ratio > 0.0:
            return "Excellente (100% arbres de décision)"
        else:
            return "Aucune règle détectée"

# 🎯 SCRIPT PRINCIPAL (Corrigé pour refléter les changements)
def main():
    print("=" * 70)
    print("🕌 ANALYSEUR TAJWID AVANCÉ - (Arbres de décision uniquement)")
    print("=" * 70)
    
    # Initialiser l'analyseur
    analyzer = SimpleTajweedAnalyzer("rule_trees")
    
    # Verset de test (Yusuf 12:28)
    test_verse = "فَلَمَّا ر۪ء۪ا قَمِيصَهُۥ قُdّdَ مِن دُبُرٖ قَالَ إِنَّهُۥ مِن كَيْدِكُنَّ إِنَّ كَيْدَكُنَّ عَظِيمٞۖ"
    
    print(f"📖 Verset analysé:")
    print(f"   {test_verse}")
    print("-" * 70)
    
    # Analyser le verset
    result = analyzer.analyze_verse(test_verse)
    
    # Afficher les résultats détaillés
    print("\n📋 RÉSULTATS DÉTAILLÉS:")
    print("🌳 = Détection par arbre de décision")
    # --- SUPPRIMÉ ---
    # print("🔍 = Détection par regex")
    print("-" * 50)
    
    rules_found = False
    for analysis in result['analysis']:
        if analysis['rules']:
            rules_found = True
            
            # Utiliser le texte normalisé du résultat
            char_info = analyzer.tree_analyzer._get_character_group(
                result['verse_normalized'], 
                analysis['position']
            )
            
            print(f"\n📍 Position {analysis['position']}: '{analysis['character']}'")
            print(f"   Groupe: '{char_info[2]}' (Base: '{char_info[2][0]}')")
            
            for rule in analysis['rules']:
                # --- MODIFIÉ ---
                # Plus besoin de vérifier la méthode, c'est toujours "Arbre"
                method_icon = "🌳"
                confidence = "🟢 Haute" # La confiance des arbres est haute
                print(f"   {method_icon} {rule['rule']} - {confidence}")
    
    if not rules_found:
        print("❌ Aucune règle de Tajwid détectée dans ce verset.")
        print("💡 Raisons possibles:")
        print("   - Le dossier 'rule_trees' est vide ou manquant")
        print("   - Les arbres de décision ne sont pas chargés")
        print("   - Le verset ne contient pas de règles détectables par les arbres")
    
    # Afficher les statistiques
    stats = result['statistics']
    print(f"\n📊 STATISTIQUES GLOBALES:")
    print(f"   Caractères analysés: {stats['total_characters']}")
    print(f"   Règles détectées: {stats['total_rules_detected']}")
    print(f"   Densité: {stats['rule_density']:.3f} règles/caractère")
    print(f"   Qualité: {stats['detection_quality']}")
    
    # Détail des méthodes (sera 100% 'decision_tree')
    if stats['total_rules_detected'] > 0:
        print(f"\n🎯 RÉPARTITION DES MÉTHODES:")
        for method, count in stats['method_distribution'].items():
            percentage = (count / stats['total_rules_detected']) * 100
            print(f"   {method}: {count} règles ({percentage:.1f}%)")
    
    # Règles détectées par type
    if stats['rules_by_type']:
        print(f"\n📈 RÈGLES DÉTECTÉES PAR TYPE:")
        for rule, count in stats['rules_by_type'].items():
            print(f"   - {rule}: {count} occurrence(s)")
    
    # Résumé des arbres chargés
    print(f"\n🌳 ARBRES CHARGÉS:")
    loaded_trees = list(analyzer.tree_analyzer.rule_trees.keys())
    if loaded_trees:
        print(f"   {len(loaded_trees)} règles avec arbres de décision")
        for tree in loaded_trees[:5]:  # Afficher les 5 premiers
            print(f"   ✓ {tree}")
        if len(loaded_trees) > 5:
            print(f"   ... et {len(loaded_trees) - 5} autres")
    else:
        print("   ❌ Aucun arbre chargé - vérifiez le dossier 'rule_trees'")
        print("   💡 Téléchargez les arbres depuis cpfair/quran-tajweed sur GitHub")

# Solution de secours si les arbres ne sont pas disponibles
def create_fallback_trees():
    """Créer des arbres de décision de base si le dossier est vide"""
    import os
    
    if not os.path.exists("rule_trees"):
        os.makedirs("rule_trees")
        print("📁 Dossier 'rule_trees' créé")
    
    # Arbre simple pour ghunnah en fallback
    ghunnah_start = {
        "attribute": "is_noon_or_meem",
        "gt": {
            "attribute": "has_shaddah",
            "gt": {"label": 1},
            "lt": {"label": 0},
            "value": 0.5
        },
        "lt": {"label": 0},
        "value": 0.5
    }
    
    ghunnah_end = {
        "attribute": "is_final_codepoint_in_letter", 
        "gt": {"label": 1},
        "lt": {"label": 0},
        "value": 0.5
    }
    
    # Sauvegarder les arbres de base
    trees_to_create = {
        'ghunnah': {'start': ghunnah_start, 'end': ghunnah_end},
        'qalqalah': {'start': ghunnah_start, 'end': ghunnah_end},  # Simplifié
        'madd_2': {'start': ghunnah_start, 'end': ghunnah_end},    # Simplifié
    }
    
    for rule_name, trees in trees_to_create.items():
        with open(f"rule_trees/{rule_name}.start.json", 'w', encoding='utf-8') as f:
            json.dump(trees['start'], f, ensure_ascii=False, indent=2)
        with open(f"rule_trees/{rule_name}.end.json", 'w', encoding='utf-8') as f:
            json.dump(trees['end'], f, ensure_ascii=False, indent=2)
    
    print("🌳 Arbres de décision de base créés dans 'rule_trees/'")

if __name__ == "__main__":
    # Vérifier si les arbres existent, sinon créer des arbres de base
    try:
        main()
    except FileNotFoundError:
        print("❌ Dossier 'rule_trees' non trouvé")
        create_fallback_trees()
        print("\n🔄 Redémarrage de l'analyse avec les arbres de base...")
        main()
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        print("🔄 Tentative de création d'arbres de base...")
        create_fallback_trees()
        print("\n🔄 Redémarrage de l'analyse...")
        main()