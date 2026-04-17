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

class ApexMonitor(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_timestamp = 0
        self.watchlist = []
        # Initial scan of your reports folder
        self.update_watchlist()

    def update_watchlist(self):
        """Scans the latest HTML report in the docs folder for tickers and catalysts"""
        try:
            # This tells the bot: "Go up one level, then into docs, then into reports"
            report_path = os.path.join("..", "docs", "reports", "*.html")
            
            list_of_files = glob.glob(report_path)
            
            if not list_of_files:
                print("⚠️ No reports found. Using default tactical watchlist.")
                self.watchlist = ["UNH", "NFLX", "AVGO", "CPI"] 
                return

            # Find the most recently created file
            latest_report = max(list_of_files, key=os.path.getctime)
            print(f"🔍 Syncing catalysts from: {latest_report}")

            with open(latest_report, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                text = soup.get_text().upper()

                # Regex: Find 3-4 uppercase letters (Tickers)
                found_tickers = re.findall(r'\b[A-Z]{3,4}\b', text)
                
                # Custom tactical keywords to always track
                manual_keywords = ["CEASEFIRE", "CPI", "MEDICARE", "BLOCKADE", "ISLAMABAD"]
                
                # Combine, remove duplicates, and filter out common non-ticker words
                ignore_list = ["HTML", "BODY", "SPAN", "TRUE", "NONE", "DONE", "APEX"]
                combined = list(set(found_tickers + manual_keywords))
                self.watchlist = [word for word in combined if word not in ignore_list]
                
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
                        
                        # Trigger alert if any watchlist word is in the headline
                        if any(word in headline for word in self.watchlist):
                            embed = discord.Embed(
                                title="🚨 APEX CATALYST DETECTED",
                                description=f"**{item['headline']}**",
                                color=0xc53030, # Apex Red
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
        """Auto-syncs with the reports folder once a day"""
        self.update_watchlist()

# --- RUN BOT ---
intents = discord.Intents.default()
intents.message_content = True
client = ApexMonitor(intents=intents)
client.run(TOKEN)