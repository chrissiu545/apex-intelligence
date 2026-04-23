import discord
import requests
import asyncio
import os
import glob
import re
from discord.ext import tasks
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# --- INITIALIZATION ---
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
FINNHUB_KEY = os.getenv('FINNHUB_KEY')
CHANNEL_ID = int(os.getenv('CHANNEL_ID')) if os.getenv('CHANNEL_ID') else 0

# --- NOISE FILTER ---
# Add words here that you want the bot to ignore even if they are ALL CAPS
EXCLUDED_WORDS = {
    "THE", "AND", "WAS", "FOR", "THAT", "WITH", "THIS", "FROM", "BUT", "NOT", 
    "ARE", "ALL", "WERE", "WHEN", "WHAT", "ALSO", "THAN", "THEN", "ONLY",
    "ANY", "WHY", "NOW", "HERE", "SOME", "SAME", "BOTH", "EACH", "INTO", "OVER",
    "HTML", "CSS", "MODE", "EDIT", "VIEW", "TEXT", "PART", "LIST", "ITEM", "FILE",
    "DATE", "HOUR", "STEP", "YEAR", "TERM", "SHOW", "PAST", "POST", "DONE", "DATA",
    "REAL", "BACK", "FACT", "CASE", "DAYS", "SIZE", "TIME", "WELL", "MADE", "LOOK",
    "IT", "DE", "HAS", "ON", "SO"
}

class ApexMonitor(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load the master list into memory ONCE
        with open("ticker_master.txt", "r") as f:
            self.master_tickers = set(line.strip().upper() for line in f)
        
        self.last_timestamp = 0
        self.watchlist = []
        self.update_watchlist()

    def update_watchlist(self):
        """Scans the latest HTML report in the docs folder for tickers and catalysts"""
        try:
            report_path = os.path.join("..", "docs", "reports", "*.html")
            list_of_files = glob.glob(report_path)
            
            if not list_of_files:
                print("⚠️ No reports found. Using default tactical watchlist.")
                self.watchlist = ["UNH", "NFLX", "AVGO", "CPI"] 
                return

            latest_report = max(list_of_files, key=os.path.getctime)
            print(f"🔍 Syncing catalysts from: {latest_report}")

            with open(latest_report, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                text = soup.get_text().upper()

                # 1. Grab potential tickers (2 to 5 characters long)
                found_tickers = re.findall(r'\b[A-Z]{2,5}\b', text)
                
                # 2. Your must-track tactical keywords
                manual_keywords = ["CEASEFIRE", "CPI", "BLOCKADE", "GLD", "V"]
                
                # 3. Combine and filter
                combined = list(set(found_tickers + manual_keywords))
                
                # We filter out the EXCLUDED_WORDS and ensure words are 2-5 chars 
                # (unless they are in our manual_keywords list)
                self.watchlist = [
                    word for word in combined 
                    if (word in self.master_tickers or word in manual_keywords)
                    and word not in EXCLUDED_WORDS
                ]
                
                print(f"✅ Watchlist updated: {self.watchlist}")

        except Exception as e:
            print(f"❌ Failed to update watchlist: {e}")

    async def setup_hook(self) -> None:
        self.monitor_loop.start()
        self.refresh_watchlist_task.start()

    async def on_ready(self):
        print(f'🚀 Logged in as {self.user}')
        channel = self.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f"🛡️ **Apex Intelligence Monitor: ONLINE**\n*Tracking: {', '.join(self.watchlist)}*")

    @tasks.loop(seconds=60)
    async def monitor_loop(self):
        channel = self.get_channel(CHANNEL_ID)
        if not channel or not self.watchlist:
            return

        try:
            url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
            response = requests.get(url)
            
            if response.status_code == 200:
                news_items = response.json()
                for item in news_items[:5]:
                    if item['datetime'] > self.last_timestamp:
                        headline = item['headline'].upper()
                        
                        if any(word in headline for word in self.watchlist):
                            embed = discord.Embed(
                                title="🚨 APEX CATALYST DETECTED",
                                description=f"**{item['headline']}**",
                                color=0xc53030, 
                                url=item['url']
                            )
                            embed.set_footer(text=f"Source: {item['source']} | Catalyst Sync Active")
                            await channel.send(embed=embed)
                
                if news_items:
                    self.last_timestamp = news_items[0]['datetime']
        except Exception as e:
            print(f"Monitor Error: {e}")

    @tasks.loop(hours=24)
    async def refresh_watchlist_task(self):
        self.update_watchlist()

# --- RUN BOT ---
intents = discord.Intents.default()
intents.message_content = True
client = ApexMonitor(intents=intents)
client.run(TOKEN)