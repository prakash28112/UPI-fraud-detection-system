import pandas as pd
import numpy as np
import os

def generate_upi_data(n_samples=10000, output_path='data/upi_transactions.csv'):
    np.random.seed(42)
    
    # Generate features
    steps = np.random.randint(1, 744, n_samples)
    types = np.random.choice(['PAYMENT', 'TRANSFER', 'CASH_OUT', 'DEBIT', 'CASH_IN'], n_samples)
    amounts = np.random.exponential(scale=5000, size=n_samples)
    
    # Realistic names
    nameOrig = ['C' + str(i).zfill(7) for i in range(n_samples)]
    nameDest = ['M' + str(i).zfill(7) for i in range(n_samples)]
    
    # Balances
    oldbalanceOrg = np.random.uniform(0, 100000, n_samples)
    newbalanceOrig = np.maximum(oldbalanceOrg - amounts, 0)
    
    oldbalanceDest = np.random.uniform(0, 100000, n_samples)
    newbalanceDest = oldbalanceDest + amounts
    
    # Fraud logic:
    # 1. Very high amounts in TRANSFER or CASH_OUT
    # 2. Large transactions that empty the account
    isFraud = np.zeros(n_samples, dtype=int)
    
    # Rule 1: High amount transfer
    fraud_mask = (amounts > 50000) & (np.isin(types, ['TRANSFER', 'CASH_OUT'])) & (np.random.rand(n_samples) < 0.2)
    isFraud[fraud_mask] = 1
    
    # Rule 2: Account draining
    drain_mask = (newbalanceOrig == 0) & (amounts > 10000) & (np.random.rand(n_samples) < 0.1)
    isFraud[drain_mask] = 1

    df = pd.DataFrame({
        'step': steps,
        'type': types,
        'amount': amounts,
        'nameOrig': nameOrig,
        'oldbalanceOrg': oldbalanceOrg,
        'newbalanceOrig': newbalanceOrig,
        'nameDest': nameDest,
        'oldbalanceDest': oldbalanceDest,
        'newbalanceDest': newbalanceDest,
        'isFraud': isFraud,
        'isFlaggedFraud': 0
    })
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Dataset generated with {n_samples} samples and {sum(isFraud)} fraud cases.")
    return output_path

if __name__ == "__main__":
    generate_upi_data()
