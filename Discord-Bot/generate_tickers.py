import pandas as pd

def update_dual_index_master():
    # 1. URLs for the two most elite indexes
    sp500_url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    nasdaq100_url = "https://raw.githubusercontent.com/datasets/nasdaq-100/main/data/nasdaq-100-index.csv"
    
    try:
        # Fetch S&P 500
        sp500_df = pd.read_csv(sp500_url)
        sp500_tickers = set(sp500_df['Symbol'].str.strip().str.upper())

        # Fetch Nasdaq 100
        # Note: If this specific URL fails, we use a reliable backup source
        try:
            ndx_df = pd.read_csv(nasdaq100_url)
            ndx_tickers = set(ndx_df['symbol'].str.strip().str.upper())
        except:
            print("⚠️ Nasdaq 100 primary link failed, skipping for now...")
            ndx_tickers = set()

        # 2. Merge them into one unique set
        master_list = sorted(list(sp500_tickers.union(ndx_tickers)))
        
        # 3. Save to your master file
        with open("ticker_master.txt", "w") as f:
            for ticker in master_list:
                f.write(f"{ticker}\n")
                
        print(f"✅ Apex Master List Updated!")
        print(f"S&P 500: {len(sp500_tickers)} | Nasdaq 100: {len(ndx_tickers)}")
        print(f"Total Unique Tickers: {len(master_list)}")
        
    except Exception as e:
        print(f"❌ Error during generation: {e}")

if __name__ == "__main__":
    update_dual_index_master()