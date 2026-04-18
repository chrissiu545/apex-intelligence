import pandas as pd

def update_master_file():
    # Fetch latest list from a reliable data source (e.g., Nasdaq's FTP or a public dataset)
    url = "https://raw.githubusercontent.com/datasets/nasdaq-listings/master/data/nasdaq-listed.csv"
    df = pd.read_csv(url)
    tickers = df['Symbol'].tolist()
    
    with open("ticker_master.txt", "w") as f:
        for ticker in tickers:
            f.write(f"{ticker}\n")
    print(f"✅ Created master list with {len(tickers)} valid tickers.")

update_master_file()