import asyncio
import ccxt.pro as ccxt
import os
import time
import random

# --- HFT CONFIGURATION ---
SYMBOL = 'SOL/USDT'
ORDER_SIZE = 0.1           # Small SOL entry (~$15-20 depending on price)
MAX_INVENTORY = 1.0        # Max SOL to hold
TICK_SIZE = 0.01           # Smallest price move for SOL/USDT
REBATE_RATE = 0.0001       # 0.01% Maker Rebate
LATENCY_SIM = 0.05         # Reduced latency for faster testing

class InstitutionalMaker:
    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_KEY', 'dummy'),
            'secret': os.getenv('BINANCE_SECRET', 'dummy'),
            'enableRateLimit': True,
        })
        
        self.inventory = 0.0
        self.balance_usdt = 100.0
        self.total_rebates = 0.0
        self.trades_count = 0
        self.last_heartbeat = time.time()
        self.start_time = time.time()

    async def watch_market(self):
        while True:
            try:
                # Heartbeat to show Railway is alive
                if time.time() - self.last_heartbeat > 30:
                    print(f"💓 Heartbeat: Still monitoring {SYMBOL}... Current Inv: {self.inventory:.2f}")
                    self.last_heartbeat = time.time()

                orderbook = await self.exchange.watch_order_book(SYMBOL)
                bid = orderbook['bids'][0][0]
                ask = orderbook['asks'][0][0]
                
                await self.logic_gate(bid, ask)
            except Exception as e:
                print(f"Connection Error: {e}")
                await asyncio.sleep(5)

    async def logic_gate(self, bid, ask):
        spread = ask - bid
        
        if (spread / bid) > 0.005:
            return

        target_buy = bid + TICK_SIZE
        target_sell = ask - TICK_SIZE

        # Profitability Check
        if target_sell <= target_buy:
            return

        tasks = []
        if self.inventory < MAX_INVENTORY:
            tasks.append(self.execute_maker('buy', target_buy))
        
        if self.inventory > -MAX_INVENTORY:
            tasks.append(self.execute_maker('sell', target_sell))

        if tasks:
            await asyncio.gather(*tasks)

    async def execute_maker(self, side, price):
        await asyncio.sleep(LATENCY_SIM)
        
        # FIX: Set to 1.0 (100%) so you can see the bot working immediately
        # Change back to 0.15 later for realistic simulation
        if random.random() > 1.0: 
            return

        rebate = (price * ORDER_SIZE) * REBATE_RATE
        self.total_rebates += rebate
        self.trades_count += 1

        if side == 'buy':
            self.inventory += ORDER_SIZE
            self.balance_usdt -= (price * ORDER_SIZE)
        else:
            self.inventory -= ORDER_SIZE
            self.balance_usdt += (price * ORDER_SIZE)

        # FIX: Report on EVERY trade so you see the money move
        self.print_report(price)

    def print_report(self, current_price):
        uptime = (time.time() - self.start_time) / 60
        current_valuation = self.balance_usdt + (self.inventory * current_price) 
        
        print(f"""
{'='*30}
📈 HFT TRADE EXECUTED
⏱️ Uptime: {uptime:.2f} mins
✅ Total Fills: {self.trades_count}
💰 Total Rebates: ${self.total_rebates:.6f}
📦 Inventory: {self.inventory:.4f} SOL
💵 Net PnL: ${current_valuation - 100:.4f}
{'='*30}
        """)

    async def run(self):
        print(f"🚀 Bot starting on Railway... Monitoring {SYMBOL}")
        await self.watch_market()

if __name__ == "__main__":
    bot = InstitutionalMaker()
    asyncio.run(bot.run())
