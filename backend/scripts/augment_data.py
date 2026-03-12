import pandas as pd
import numpy as np
import nltk
from nltk.corpus import wordnet
import random
import re

# Download WordNet if not present
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')
    nltk.download('omw-1.4')

def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonym = lemma.name().replace("_", " ").replace("-", " ").lower()
            synonym = "".join([char for char in synonym if char in " qwertyuiopasdfghjklzxcvbnm"])
            synonyms.add(synonym)
    if word in synonyms:
        synonyms.remove(word)
    return list(synonyms)

def synonym_replacement(words, n):
    new_words = words.copy()
    random_word_list = list(set([word for word in words if word.isalnum()]))
    random.shuffle(random_word_list)
    num_replaced = 0
    for random_word in random_word_list:
        synonyms = get_synonyms(random_word)
        if len(synonyms) >= 1:
            synonym = random.choice(list(synonyms))
            new_words = [synonym if word == random_word else word for word in new_words]
            num_replaced += 1
        if num_replaced >= n:
            break
    
    sentence = ' '.join(new_words)
    return sentence

def augment_text(text, alpha_sr=0.1):
    """
    Apply simple Synonym Replacement
    alpha_sr: percentage of words to be replaced
    """
    words = text.split()
    num_words = len(words)
    if num_words < 4:  # Too short to safely augment
        return text
    n_sr = max(1, int(alpha_sr * num_words))
    return synonym_replacement(words, n_sr)

def clean_text(text):
    """Basic text cleaning."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)  # Keep only letters and spaces
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces
    return text

def augment_dataframe(df, target_samples=2500):
    print("Starting data augmentation...")
    augmented_rows = []
    
    category_counts = df['category'].value_counts()
    print("Initial class distribution:")
    print(category_counts)
    
    for category, count in category_counts.items():
        # Clean existing text
        cat_df = df[df['category'] == category].copy()
        cat_df['text'] = cat_df['text'].apply(clean_text)
        
        # Add original rows to final list
        augmented_rows.extend(cat_df.to_dict('records'))
        
        # Calculate how many synthetics we need
        samples_needed = target_samples - count
        
        if samples_needed > 0:
            print(f"Generating {samples_needed} synthetic samples for category '{category}'...")
            
            # Extract list of texts to base augmented text off of
            base_texts = cat_df['text'].tolist()
            
            for _ in range(samples_needed):
                # Randomly pick a base text
                base_text = random.choice(base_texts)
                # Augment it
                synth_text = augment_text(base_text, alpha_sr=0.15)  # 15% synonym replacement
                
                # Create a new synthetic row based on a random original row to keep metadata mostly intact
                base_row = random.choice(cat_df.to_dict('records'))
                new_row = base_row.copy()
                new_row['text'] = synth_text
                # Optional: flag it as synthetic
                new_row['is_synthetic'] = True
                augmented_rows.append(new_row)
    
    augmented_df = pd.DataFrame(augmented_rows)
    # Fill NaN for originals
    if 'is_synthetic' in augmented_df.columns:
        augmented_df['is_synthetic'] = augmented_df['is_synthetic'].fillna(False)
    
    # Shuffle the entire dataset
    augmented_df = augmented_df.sample(frac=1, random_state=42).reset_index(drop=True)
    return augmented_df

if __name__ == "__main__":
    input_path = 'data/FINAL_80_PERCENT_NOISY_DATASET (1) (2).csv'
    output_path = 'data/AUGMENTED_BALANCED_DATASET.csv'
    
    # Load dataset
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Run augmentation
    # Target samples = max count (Product has 2500, so we target 2500 for all)
    target = df['category'].value_counts().max()
    balanced_df = augment_dataframe(df, target_samples=target)
    
    print("\nBalanced class distribution:")
    print(balanced_df['category'].value_counts())
    
    print(f"\nSaving augmented dataset to {output_path}...")
    balanced_df.to_csv(output_path, index=False)
    print("Data augmentation complete!")
