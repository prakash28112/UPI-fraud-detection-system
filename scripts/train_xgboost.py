import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
import os

def train_model(data_path='data/upi_transactions.csv', model_dir='models/'):
    # Load data
    df = pd.read_csv(data_path)
    
    # Preprocessing
    le = LabelEncoder()
    df['type'] = le.fit_transform(df['type'])
    
    # Select features
    features = ['step', 'type', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest']
    X = df[features]
    y = df['isFraud']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Calculate scale_pos_weight for imbalanced data
    ratio = float(np.sum(y == 0)) / np.sum(y == 1)
    
    # Initialize XGBoost
    model = xgb.XGBClassifier(
        max_depth=6,
        learning_rate=0.1,
        n_estimators=100,
        scale_pos_weight=ratio,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    # Train
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred)
    }
    
    print("\n--- Model Performance ---")
    for k, v in metrics.items():
        print(f"{k.capitalize()}: {v:.4f}")
    
    # Save
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(model, os.path.join(model_dir, 'fraud_model.pkl'))
    joblib.dump(le, os.path.join(model_dir, 'label_encoder.pkl'))
    print(f"\nModel and Encoder saved to {model_dir}")
    
    return metrics

if __name__ == "__main__":
    train_model()
