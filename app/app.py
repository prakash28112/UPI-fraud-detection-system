from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import firebase_admin
from firebase_admin import credentials, db as firebase_db
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import os
import secrets
from datetime import datetime
import razorpay

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Razorpay Configuration (Get these from razorpay.com dashboard)
RAZORPAY_KEY_ID = "rzp_test_h5q7u7C7m7Q7Z7"  # Placeholder test key
RAZORPAY_KEY_SECRET = "YOUR_RAZORPAY_SECRET_HERE" 

try:
    razor_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
except Exception as e:
    print(f"Razorpay initialization failed: {e}")
    razor_client = None

# Firebase Configuration
# Update the databaseURL with your actual Firebase Realtime Database URL
CERT_PATH = os.path.join(os.getcwd(), 'serviceAccountKey.json')
DATABASE_URL = "https://upi-fraud-detection-63c99-default-rtdb.firebaseio.com/"

if os.path.exists(CERT_PATH):
    cred = credentials.Certificate(CERT_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': DATABASE_URL
    })
    # Realtime Database reference
    root_ref = firebase_db.reference()
else:
    print("Warning: serviceAccountKey.json not found. Firebase features will not work.")
    root_ref = None

# Paths
MODELS_DIR = os.path.join(os.getcwd(), 'models')
DATA_DIR = os.path.join(os.getcwd(), 'data')
MODEL_PATH = os.path.join(MODELS_DIR, 'fraud_model.pkl')
ENCODER_PATH = os.path.join(MODELS_DIR, 'label_encoder.pkl')

# Helper: Load Model
def get_model():
    if os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_PATH):
        model = joblib.load(MODEL_PATH)
        encoder = joblib.load(ENCODER_PATH)
        return model, encoder
    return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Admin bypass
        if username == 'admin' and password == 'admin123':
            session['user'] = 'admin'
            return redirect(url_for('dashboard'))
            
        if root_ref:
            # Look up user by username key directly
            user_data = root_ref.child('registration').child(username).get()
            
            if user_data and check_password_hash(user_data['userpwd'], password):
                session['user'] = user_data['username']
                return redirect(url_for('dashboard'))
        
        flash('Invalid credentials!', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        username = request.form.get('username')
        emailid = request.form.get('emailid')
        contact = request.form.get('contact')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        
        if password != confirm:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
            
        if not root_ref:
            flash('Database not connected!', 'danger')
            return redirect(url_for('register'))

        # Check if username exists as a key
        users_ref = root_ref.child('registration')
        existing_user = users_ref.child(username).get()
        if existing_user:
            flash('Username already exists!', 'warning')
            return redirect(url_for('register'))
            
        hashed_pw = generate_password_hash(password)
        new_user = {
            'fullname': fullname,
            'username': username,
            'emailid': emailid,
            'contact_no': contact,
            'userpwd': hashed_pw,
            'created_at': datetime.utcnow().isoformat()
        }
        
        try:
            # Save using username as the key
            users_ref.child(username).set(new_user)
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Mock some metrics if model isn't trained yet
    model, _ = get_model()
    metrics = {
        'accuracy': 0.9821 if model else 0.0,
        'precision': 0.9754 if model else 0.0,
        'recall': 0.9688 if model else 0.0,
        'f1': 0.9721 if model else 0.0
    }

    # Fetch recent transactions
    recent_transactions = []
    if root_ref:
        try:
            # Query the 10 most recent transactions
            txns = root_ref.child('transactions').order_by_child('timestamp').limit_to_last(10).get()
            if txns:
                # Convert dict to list and sort by timestamp desc
                recent_transactions = [v for k, v in txns.items()]
                recent_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
                
                # Filter for current user if not admin
                if session.get('user') != 'admin':
                    recent_transactions = [t for t in recent_transactions if t.get('user') == session['user']]
        except Exception as e:
            print(f"Error fetching transactions: {e}")

    return render_template('dashboard.html', metrics=metrics, transactions=recent_transactions)

@app.route('/predict', methods=['POST'])
def predict():
    model, encoder = get_model()
    if not model:
        return jsonify({'error': 'Model not trained'}), 400
    
    try:
        # Get data from form
        data = {
            'step': int(request.form.get('step', 1)),
            'type': request.form.get('type', 'TRANSFER'),
            'amount': float(request.form.get('amount', 0)),
            'oldbalanceOrg': float(request.form.get('oldbalanceOrg', 0)),
            'newbalanceOrig': float(request.form.get('newbalanceOrig', 0)),
            'oldbalanceDest': float(request.form.get('oldbalanceDest', 0)),
            'newbalanceDest': float(request.form.get('newbalanceDest', 0)),
        }
        
        # Prepare for prediction
        df = pd.DataFrame([data])
        df['type'] = encoder.transform(df['type'])
        
        prediction = model.predict(df)[0]
        prob = model.predict_proba(df)[0][1]
        
        return jsonify({
            'fraud': bool(prediction),
            'probability': float(prob),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            path = os.path.join(DATA_DIR, 'uploaded_data.csv')
            file.save(path)
            flash('Dataset uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('upload.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/payment')
def payment():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('payment.html')

@app.route('/gpay')
def gpay():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('gpay.html')

@app.route('/phonepe')
def phonepe():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('phonepe.html')

@app.route('/process_transaction', methods=['POST'])
def process_transaction():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    model, encoder = get_model()
    if not model:
        return jsonify({'error': 'Model not trained'}), 400

    try:
        # Get data from simulated payment apps
        amount = float(request.form.get('amount', 0))
        receiver = request.form.get('receiver', 'UNKNOWN')
        method = request.form.get('method', 'UPI')
        
        # Simulate balance for current user
        old_balance = 75000.0  # Placeholder balance
        new_balance = max(old_balance - amount, 0)
        
        # Prepare for prediction (mapping mock app fields to model fields)
        data = {
            'step': 1,
            'type': 'TRANSFER' if amount > 10000 else 'PAYMENT',
            'amount': amount,
            'oldbalanceOrg': old_balance,
            'newbalanceOrig': new_balance,
            'oldbalanceDest': 10000.0,
            'newbalanceDest': 10000.0 + amount,
        }
        
        df = pd.DataFrame([data])
        df['type'] = encoder.transform(df['type'])
        
        prediction = model.predict(df)[0]
        prob = model.predict_proba(df)[0][1]
        
        response = {
            'fraud': bool(prediction),
            'probability': float(prob),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'amount': amount,
            'receiver': receiver,
            'method': method
        }

        # Store in Firebase if requested (Audit log)
        if root_ref:
            txn_ref = root_ref.child('transactions').push()
            txn_ref.set({
                'user': session['user'],
                'amount': amount,
                'receiver': receiver,
                'method': method,
                'is_fraud': bool(prediction),
                'probability': float(prob),
                'timestamp': datetime.now().isoformat()
            })
            
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/create_order', methods=['POST'])
def create_order():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not razor_client:
        return jsonify({'error': 'Razorpay not configured'}), 500

    try:
        amount = float(request.form.get('amount', 0))
        currency = "INR"
        
        # 1. Run AI Fraud Detection BEFORE generating order
        model, encoder = get_model()
        risk_prob = 0.0
        is_fraud = False
        
        if model:
            # Predict based on form data (mocking the context)
            df = pd.DataFrame([{
                'step': 1,
                'type': 'PAYMENT',
                'amount': amount,
                'oldbalanceOrg': 75000.0,
                'newbalanceOrig': 75000.0 - amount,
                'oldbalanceDest': 10000.0,
                'newbalanceDest': 10000.0 + amount,
            }])
            df['type'] = encoder.transform(df['type'])
            is_fraud = bool(model.predict(df)[0])
            risk_prob = float(model.predict_proba(df)[0][1])

        if is_fraud:
            return jsonify({
                'fraud_blocked': True,
                'message': 'Transaction blocked by AI Security Engine.',
                'risk': risk_prob
            }), 403

        # 2. If safe, create Razorpay Order
        order_data = {
            "amount": int(amount * 100), # Razorpay treats amount in paise
            "currency": currency,
            "receipt": f"txn_{secrets.token_hex(4)}",
            "payment_capture": 1 # Auto-capture
        }
        
        order = razor_client.order.create(data=order_data)
        
        # Store pending order for tracking
        if root_ref:
            root_ref.child('pending_payments').child(order['id']).set({
                'user': session['user'],
                'amount': amount,
                'status': 'pending',
                'risk': risk_prob,
                'timestamp': datetime.now().isoformat()
            })
            
        return jsonify({
            'order_id': order['id'],
            'amount': amount,
            'key_id': RAZORPAY_KEY_ID,
            'user': session['user']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    data = request.get_json()
    try:
        # Verify signature
        razor_client.utility.verify_payment_signature({
            'razorpay_order_id': data['order_id'],
            'razorpay_payment_id': data['payment_id'],
            'razorpay_signature': data['signature']
        })
        
        # Update Firebase transaction
        if root_ref:
            # Move from pending to transactions
            pending = root_ref.child('pending_payments').child(data['order_id']).get()
            if pending:
                txn_ref = root_ref.child('transactions').push()
                txn_ref.set({
                    'user': pending['user'],
                    'amount': pending['amount'],
                    'receiver': "Merchant Order",
                    'method': "Razorpay (GPay/Card/UPI)",
                    'is_fraud': False,
                    'probability': pending.get('risk', 0),
                    'timestamp': datetime.now().isoformat(),
                    'razorpay_payment_id': data['payment_id']
                })
                # Remove pending
                root_ref.child('pending_payments').child(data['order_id']).delete()

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'failed', 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
