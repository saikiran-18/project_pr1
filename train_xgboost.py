import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, f1_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import joblib

import torch
from transformers import RobertaTokenizer, RobertaModel

# Setup bare-minimum functions to replace missing src module
def load_data(path):
    return pd.read_csv(path)

def load_roberta_wrapper():
    tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
    model = RobertaModel.from_pretrained('roberta-base')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    model.eval()
    return tokenizer, model, device

def extract_roberta_features(texts, tokenizer, model, device, batch_size=32):
    features = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        inputs = tokenizer(batch_texts, padding=True, truncation=True, max_length=128, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(**inputs)
        # Using the [CLS] token embedding for classification features
        cls_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        features.extend(cls_embeddings)
    return np.array(features)

def run_pipeline():
    print("Loading data...")
    # Assuming run from root directory Complaint-Routing-System
    df = load_data(path='data/FINAL_80_PERCENT_NOISY_DATASET (1) (2).csv')
    
    # Stratified split to preserve class distribution
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['category'])
    
    print(f"Train size: {len(train_df)}, Test size: {len(test_df)}")
    
    print("Class distribution in training set:")
    print(train_df['category'].value_counts())
    
    print("Loading RoBERTa model...")
    tokenizer, model, device = load_roberta_wrapper()
    
    print("Extracting RoBERTa features for training data...")
    X_train_emb = extract_roberta_features(train_df['text'].tolist(), tokenizer, model, device, batch_size=32)
    
    print("Extracting RoBERTa features for test data...")
    X_test_emb = extract_roberta_features(test_df['text'].tolist(), tokenizer, model, device, batch_size=32)
    
    # Label Encoding
    le = LabelEncoder()
    y_train = le.fit_transform(train_df['category'])
    y_test = le.transform(test_df['category'])
    
    print("Applying SMOTE to balance the training data features...")
    try:
        from imblearn.over_sampling import SMOTE
        smote = SMOTE(random_state=42)
        X_train_emb_resampled, y_train_resampled = smote.fit_resample(X_train_emb, y_train)
        print("Original training data shape:", len(X_train_emb))
        print("Resampled training data shape:", len(X_train_emb_resampled))
    except ImportError:
        print("Warning: imblearn not installed. Please run `pip install imbalanced-learn`.")
        X_train_emb_resampled, y_train_resampled = X_train_emb, y_train
    
    print("Initializing XGBoost classifier...")
    xgb_clf = xgb.XGBClassifier(
        objective='multi:softprob',
        eval_metric='mlogloss',
        random_state=42,
        n_jobs=-1
    )
    
    # Define Parameter Grid for GridSearchCV (Simplified for speed)
    param_grid = {
        'max_depth': [3],
        'learning_rate': [0.1],
        'n_estimators': [100],
    }
    
    print("Starting GridSearchCV...")
    grid_search = GridSearchCV(
        estimator=xgb_clf,
        param_grid=param_grid,
        scoring='f1_macro',
        cv=2,
        verbose=2,
        n_jobs=-1
    )
    
    grid_search.fit(X_train_emb_resampled, y_train_resampled)
    
    print("Best parameters found: ", grid_search.best_params_)
    best_model = grid_search.best_estimator_
    
    print("Evaluating on test set...")
    y_pred = best_model.predict(X_test_emb)
    
    print("\n--- Classification Report ---")
    print(classification_report(y_test, y_pred, target_names=le.classes_))
    
    macro_f1 = f1_score(y_test, y_pred, average='macro')
    print(f"\nOverall Macro-F1 Score: {macro_f1:.4f}")
    
    os.makedirs('models', exist_ok=True)
    joblib.dump(best_model, 'models/xgboost_roberta_best.pkl')
    joblib.dump(le, 'models/label_encoder.pkl')
    print("Model and Label Encoder saved to models/ directory.")

if __name__ == "__main__":
    run_pipeline()
