from datasets import load_dataset
import librosa
import numpy as np

print("Chargement du dataset en streaming...")

# Charger en streaming
dataset_stream = load_dataset(
    "Sabri12blm/Arabic-Quran-ASR-dataset",
    split="train",
    streaming=True
)

# Prendre 10 000 exemples
subset_dataset = dataset_stream.take(10000)

print(" Dataset chargé en streaming (10 000 exemples)")

# Vérifier quelques exemples
print("\n Aperçu des premiers exemples :")
for i, example in enumerate(subset_dataset):
    print(f"\nExemple {i+1}:")
    print(f"  Audio shape: {example['wave_filename']['array'].shape}")
    print(f"  Transcript: {example['transcript']}")
    if i >= 5:
        break

# ============================================================================
# PARTIE 3 : PRÉTRAITEMENT AUDIO 
# ============================================================================

def preprocess_audio(audio_array, sr=44100):
    """
    Prétraiter l'audio pour Wav2Vec2
    
    Étapes :
    1. Convertir en float32
    2. Normaliser entre -1 et 1
    3. Resampler à 16kHz (requis par Wav2Vec2)
    """
    # Convertir en float32
    audio_float = audio_array.astype(np.float32)
    
    # Normaliser (diviser par la valeur maximale absolue)
    audio_float /= np.max(np.abs(audio_float))
    
    # Resampler à 16kHz (Wav2Vec2 attend cette fréquence)
    audio_resampled = librosa.resample(y=audio_float, orig_sr=sr, target_sr=16000)
    
    return audio_resampled

print("\n Prétraitement des exemples audio...")

# Préparer les exemples (audio + transcription)
processed_exemples = []

# RE-charger le dataset car le streaming est épuisé
subset_dataset = load_dataset(
    "Sabri12blm/Arabic-Quran-ASR-dataset",
    split="train",
    streaming=True
).take(10000)

for i, example in enumerate(subset_dataset):
    # Récupérer l'audio et la transcription
    audio_array = example["wave_filename"]["array"]
    transcript = example["transcript"]
    
    # Prétraiter l'audio
    audio_processed = preprocess_audio(audio_array)
    
    # Stocker
    processed_exemples.append({
        "audio": audio_processed,
        "transcript": transcript
    })
    
    # Afficher progression tous les 1000
    if (i + 1) % 1000 == 0:
        print(f"  → {i + 1} exemples traités...")

print(f"\n {len(processed_exemples)} exemples audio prétraités")

# ============================================================================
# PARTIE 4 : CRÉATION DU TOKENIZER CORANIQUE (NOUVEAU)
# ============================================================================

from transformers import Wav2Vec2CTCTokenizer, Wav2Vec2FeatureExtractor, Wav2Vec2Processor
import json
import os

print("\n" + "="*70)
print(" CRÉATION DU TOKENIZER CORANIQUE")
print("="*70)

def creer_vocabulaire_coranique():
    """
    Créer le vocabulaire complet du Coran (approche optimisée)
    Pas besoin d'analyser le dataset : le Coran a un vocabulaire fixe !
    """
    
    print("\n Création du vocabulaire coranique...")
    
    # Lettres arabes de base (28)
    lettres = [
        'ا', 'ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ذ', 'ر',
        'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف',
        'ق', 'ك', 'ل', 'م', 'ن', 'ه', 'و', 'ي'
    ]
    
    # Variantes (Hamza, Alif, etc.)
    variantes = ['أ', 'إ', 'آ', 'ة', 'ى', 'ئ', 'ؤ', 'ء']
    
    # Diacritiques (IMPORTANT pour le Coran)
    diacritiques = [
        'َ', 'ِ', 'ُ', 'ْ', 'ّ', 'ً', 'ٍ', 'ٌ', 'ٰ', 'ٓ',
        'ٖ', 'ٗ', '٘', 'ٙ', 'ٚ', 'ٛ', 'ٜ', 'ٝ', 'ٞ', 'ٟ'
    ]
    
    # Signes coraniques
    signes = ['۩', '۞', '۝', '﴾', '﴿']
    
    # Chiffres arabes
    chiffres = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩']
    
    # Combiner tout
    vocabulaire = lettres + variantes + diacritiques + signes + chiffres
    
    # Trier et enlever doublons
    vocabulaire = sorted(list(set(vocabulaire)))
    
    print(f" Vocabulaire créé : {len(vocabulaire)} caractères")
    
    return vocabulaire

def creer_tokenizer_quran(vocabulaire, save_dir="./tokenizer_quran"):
    """
    Créer le tokenizer CTC pour le Coran
    """
    
    print(f"\n Création du tokenizer...")
    
    # Créer le dossier de sauvegarde
    os.makedirs(save_dir, exist_ok=True)
    
    # Créer le dictionnaire vocabulaire avec IDs
    vocab_dict = {}
    
    # Tokens spéciaux (IDs 0, 1, 2)
    vocab_dict["<pad>"] = 0
    vocab_dict["<unk>"] = 1
    vocab_dict["|"] = 2  # Séparateur de mots
    
    # Ajouter les caractères coraniques (IDs à partir de 3)
    for i, char in enumerate(vocabulaire):
        vocab_dict[char] = i + 3
    
    print(f"   • Taille vocabulaire total : {len(vocab_dict)} tokens")
    
    # Sauvegarder vocab.json
    vocab_file = os.path.join(save_dir, "vocab.json")
    with open(vocab_file, 'w', encoding='utf-8') as f:
        json.dump(vocab_dict, f, ensure_ascii=False, indent=2)
    
    print(f"   • vocab.json sauvegardé : {vocab_file}")
    
    # Créer le tokenizer
    tokenizer = Wav2Vec2CTCTokenizer(
        vocab_file=vocab_file,
        unk_token="<unk>",
        pad_token="<pad>",
        word_delimiter_token="|",
        do_lower_case=False  # Important pour l'arabe !
    )
    
    # Sauvegarder le tokenizer complet
    tokenizer.save_pretrained(save_dir)
    
    print(f" Tokenizer sauvegardé dans : {save_dir}")
    
    return tokenizer

# Créer le vocabulaire et le tokenizer
vocabulaire = creer_vocabulaire_coranique()
tokenizer = creer_tokenizer_quran(vocabulaire)

# Tester le tokenizer
print("\n Test du tokenizer :")
texte_test = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
tokens = tokenizer.tokenize(texte_test)
token_ids = tokenizer.convert_tokens_to_ids(tokens)
decode = tokenizer.decode(token_ids)

print(f"   Texte original : {texte_test}")
print(f"   Tokens        : {tokens}")
print(f"   Nombre tokens : {len(tokens)}")
print(f"   Token IDs     : {token_ids[:20]}...")  # Premiers 20 IDs
print(f"   Décodé        : {decode}")
print(f"   <unk> count   : {tokens.count('<unk>')} (devrait être 0!)")

# ============================================================================
# PARTIE 5 : CRÉATION DU PROCESSOR (Feature Extractor + Tokenizer)
# ============================================================================

print("\n" + "="*70)
print(" CRÉATION DU PROCESSOR COMPLET")
print("="*70)

# Le Feature Extractor (garde celui pré-entraîné de Wav2Vec2)
feature_extractor = Wav2Vec2FeatureExtractor(
    feature_size=1,
    sampling_rate=16000,  # Fréquence qu'on a utilisée
    padding_value=0.0,
    do_normalize=True,
    return_attention_mask=True
)

# Combiner Feature Extractor + Tokenizer = Processor
processor = Wav2Vec2Processor(
    feature_extractor=feature_extractor,
    tokenizer=tokenizer
)

# Sauvegarder le processor complet
processor.save_pretrained("./processor_quran")
print(" Processor sauvegardé dans : ./processor_quran")

# ============================================================================
# PARTIE 6 : PRÉPARER LE DATASET POUR L'ENTRAÎNEMENT
# ============================================================================

print("\n" + "="*70)
print("PRÉPARATION DU DATASET POUR TRAINING")
print("="*70)

def prepare_dataset_for_training(processed_exemples, processor):
    """
    Préparer les données pour l'entraînement Wav2Vec2
    """
    
    print(f"\n Conversion de {len(processed_exemples)} exemples...")
    
    dataset_ready = []
    
    for i, exemple in enumerate(processed_exemples):
        audio = exemple["audio"]
        text = exemple["transcript"]
        
        # Traiter l'audio avec le feature extractor
        input_values = processor.feature_extractor(
            audio,
            sampling_rate=16000,
            return_tensors="pt"
        ).input_values[0]  # Enlever la dimension batch
        
        # Traiter le texte avec le tokenizer
        with processor.as_target_processor():
            labels = processor.tokenizer(text).input_ids
        
        # Créer l'exemple formaté
        dataset_ready.append({
            "input_values": input_values,
            "labels": labels
        })
        
        # Progression
        if (i + 1) % 1000 == 0:
            print(f"   → {i + 1}/{len(processed_exemples)} convertis...")
    
    print(f"Dataset prêt : {len(dataset_ready)} exemples")
    
    return dataset_ready

# Préparer le dataset
dataset_ready = prepare_dataset_for_training(processed_exemples, processor)

# Afficher un exemple
print("\n Exemple de données prêtes pour l'entraînement :")
exemple = dataset_ready[0]
print(f"   input_values shape : {exemple['input_values'].shape}")
print(f"   labels (premiers 20): {exemple['labels'][:20]}")
print(f"   labels length     : {len(exemple['labels'])}")

# ============================================================================
# PARTIE 7 : SPLIT TRAIN/VALIDATION
# ============================================================================

print("\n" + "="*70)
print(" SPLIT TRAIN/VALIDATION")
print("="*70)

from sklearn.model_selection import train_test_split

# Split 90% train / 10% validation
train_data, val_data = train_test_split(
    dataset_ready, 
    test_size=0.1, 
    random_state=42
)

print(f" Split effectué :")
print(f"   • Train : {len(train_data)} exemples")
print(f"   • Validation : {len(val_data)} exemples")

# ============================================================================
# PARTIE 8 : SAUVEGARDER LES DONNÉES PRÉPARÉES
# ============================================================================

print("\n" + "="*70)
print(" SAUVEGARDE DES DONNÉES")
print("="*70)

import pickle

# Sauvegarder les données préparées
with open("train_data.pkl", "wb") as f:
    pickle.dump(train_data, f)

with open("val_data.pkl", "wb") as f:
    pickle.dump(val_data, f)

print(" Données sauvegardées :")
print("   • train_data.pkl")
print("   • val_data.pkl")

# ============================================================================
# RÉCAPITULATIF FINAL
# ============================================================================

print("\n" + "="*70)
print(" PRÉPARATION TERMINÉE !")
print("="*70)
print("\n RÉSUMÉ :")
print(f"    Dataset chargé : 10 000 exemples")
print(f"    Audio prétraité : 16kHz, normalisé")
print(f"    Tokenizer créé : {len(tokenizer)} tokens (arabe coranique)")
print(f"    Processor créé : Feature Extractor + Tokenizer")
print(f"    Dataset formaté : input_values + labels")
print(f"    Split effectué : {len(train_data)} train / {len(val_data)} val")
print(f"    Données sauvegardées")

print("\n PROCHAINES ÉTAPES :")
print("   1. Charger le modèle Wav2Vec2")
print("   2. Créer le Data Collator")
print("   3. Configurer le Trainer")
print("   4. Lancer le fine-tuning")

print("\n FICHIERS CRÉÉS :")
print("   • ./tokenizer_quran/")
print("   • ./processor_quran/")
print("   • train_data.pkl")
print("   • val_data.pkl")

