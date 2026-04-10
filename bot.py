import asyncio
import ccxt.pro as ccxt
import os
import time

# --- HFT CONFIGURATION ---
SYMBOL = 'SOL/USDT'
ORDER_SIZE = 0.0005        # Small balance entry (~$35-40)
MAX_INVENTORY = 0.002      # Max BTC to hold (Risk Management)
TICK_SIZE = 0.01           # Smallest price move for BTC/USDT
REBATE_RATE = 0.0001       # 0.01% Maker Rebate (Est. for small accounts)
LATENCY_SIM = 0.15         # 150ms Railway-to-Exchange delay

class InstitutionalMaker:
    def __init__(self):
        # Initialize Exchange
        self.exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_KEY', 'dummy'),
            'secret': os.getenv('BINANCE_SECRET', 'dummy'),
            'enableRateLimit': True,
        })
        
        # Performance Tracking
        self.inventory = 0.0
        self.balance_usdt = 100.0  # Simulated Start
        self.total_rebates = 0.0
        self.trades_count = 0
        self.start_time = time.time()

    async def watch_market(self):
        """Websocket stream for sub-millisecond price updates"""
        while True:
            try:
                # watch_order_book is better for HFT than watch_ticker
                orderbook = await self.exchange.watch_order_book(SYMBOL)
                bid = orderbook['bids'][0][0]
                ask = orderbook['asks'][0][0]
                
                await self.logic_gate(bid, ask)
            except Exception as e:
                print(f"Connection Error: {e}")
                await asyncio.sleep(5)

    async def logic_gate(self, bid, ask):
        # 1. CALCULATE SPREAD
        spread = ask - bid
        
        # 2. TOXIC FLOW FILTER
        # If spread is huge (>0.5%), the market is crashing/pumping. Don't touch it.
        if (spread / bid) > 0.005:
            return

        # 3. PENNY JUMPING (The Maker Strategy)
        # We place our orders 1 tick inside the spread to be first in line.
        target_buy = bid + TICK_SIZE
        target_sell = ask - TICK_SIZE

        # 4. PROFITABILITY CHECK
        # Ensure (Sell - Buy) + Rebates > 0. 
        # Inverted spreads (like in your logs) are skipped.
        if target_sell <= target_buy:
            return

        # 5. INVENTORY SKEW
        # If we have too much BTC, we stop buying and only sell.
        tasks = []
        if self.inventory < MAX_INVENTORY:
            tasks.append(self.execute_maker('buy', target_buy))
        
        if self.inventory > -MAX_INVENTORY:
            tasks.append(self.execute_maker('sell', target_sell))

        if tasks:
            await asyncio.gather(*tasks)

    async def execute_maker(self, side, price):
        # Real-world Execution Simulation
        await asyncio.sleep(LATENCY_SIM)
        
        # 15% Fill Probability (Typical for competitive HFT Maker orders)
        import random
        if random.random() > 0.50:
            return

        # Execute Trade
        rebate = (price * ORDER_SIZE) * REBATE_RATE
        self.total_rebates += rebate
        self.trades_count += 1

        if side == 'buy':
            self.inventory += ORDER_SIZE
            self.balance_usdt -= (price * ORDER_SIZE)
        else:
            self.inventory -= ORDER_SIZE
            self.balance_usdt += (price * ORDER_SIZE)

        # 6. LOG PERFORMANCE EVERY 20 TRADES
        if self.trades_count % 20 == 0:
            self.print_report()

    def print_report(self):
        uptime = (time.time() - self.start_time) / 60
        # Calculate current value of inventory + cash
        # Use a placeholder price for current BTC value
        current_valuation = self.balance_usdt + (self.inventory * 72000) 
        
        print(f"""
{'='*30}
📈 HFT PERFORMANCE REPORT
⏱️ Uptime: {uptime:.2f} mins
✅ Fills: {self.trades_count}
💰 Est. Rebates: ${self.total_rebates:.6f}
📦 Inventory: {self.inventory:.5f} BTC
💵 Net PnL: ${current_valuation - 100:.4f}
{'='*30}
        """)

    async def run(self):
        print(f"🚀 Bot starting on Railway... Monitoring {SYMBOL}")
        await self.watch_market()

if __name__ == "__main__":
    bot = InstitutionalMaker()
    asyncio.run(bot.run())
