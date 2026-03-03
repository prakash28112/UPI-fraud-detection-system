# Machine Learning Driven Fraud Detection System for UPI Transactions

A premium Flask-based web application that identifies fraudulent UPI transactions using XGBoost.

## Features
- **Real-time Fraud Identification**: Instant detection using an XGBoost model.
- **Admin Dashboard**: Visualize key performance metrics (Accuracy, Precision, Recall).
- **Dataset Management**: Upload new transaction data to retrain the model.
- **Modern UI**: Dark-mode glassmorphic design for a professional experience.

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Firebase Setup**:
   - Go to [Firebase Console](https://console.firebase.google.com/).
   - Create a new project.
   - Go to Project Settings > Service Accounts.
   - Click "Generate new private key".
   - Save the downloaded JSON as `serviceAccountKey.json` in the project root.
   - Enable "Firestore Database" in the Firebase Console.

3. **Train the Model**:
   - Generate synthetic data: `python scripts/data_generator.py`
   - Train model: `python scripts/train_xgboost.py`

4. **Run Application**:
   ```bash
   python app/app.py
   ```
   Access the app at `http://127.0.0.1:5000`.

## Directory Structure
- `app/`: Flask application code and templates.
- `database/`: SQL schema files.
- `scripts/`: Data generation and ML training scripts.
- `models/`: Saved model files and encoders.
- `data/`: Datasets used for training and testing.
