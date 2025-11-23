from game import HistoricalDataManager
import pandas as pd

def test_nuburu_generation():
    print("Testing NUBURU generation...")
    manager = HistoricalDataManager(["NUBURU"])
    
    if "NUBURU" in manager.data:
        df = manager.data["NUBURU"]
        print(f"NUBURU data shape: {df.shape}")
        print(df.head())
        print(df.tail())
        
        # Check for volatility
        df['Change'] = df['Close'].pct_change()
        max_change = df['Change'].max()
        min_change = df['Change'].min()
        
        print(f"Max Daily Change: {max_change*100:.2f}%")
        print(f"Min Daily Change: {min_change*100:.2f}%")
        
        if not df.empty:
            print("✅ NUBURU data generated successfully.")
        else:
            print("❌ NUBURU data is empty.")
    else:
        print("❌ NUBURU not found in data manager.")

if __name__ == "__main__":
    test_nuburu_generation()
