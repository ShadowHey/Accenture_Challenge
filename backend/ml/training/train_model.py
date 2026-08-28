import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib

def train():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, "training_data.csv")
    
    if not os.path.exists(data_path):
        print(f"Data not found at {data_path}. Please run generate_training_data.py first.")
        return
        
    df = pd.read_csv(data_path)
    
    X = df.drop(columns=['label'])
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    
    print("Training model...")
    model = GradientBoostingClassifier(
        n_estimators=100, 
        max_depth=4, 
        learning_rate=0.1, 
        min_samples_split=10, 
        min_samples_leaf=5, 
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    print("Evaluating...")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    print("\nFeature Importances:")
    importances = list(zip(X.columns, model.feature_importances_))
    importances.sort(key=lambda x: x[1], reverse=True)
    for feat, imp in importances:
        print(f"{feat}: {imp:.4f}")
        
    model_dir = os.path.join(os.path.dirname(current_dir), "models")
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, "triage_model.joblib")
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train()
