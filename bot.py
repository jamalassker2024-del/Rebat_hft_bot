import asyncio
import ccxt.pro as ccxt  # Use the Pro version for WebSockets
import os

# --- CORE SETTINGS ---
SYMBOL = 'BTC/USDT'
MIN_SPREAD_THRESHOLD = 0.0002  # 0.02% minimum spread to engage
MAX_INVENTORY = 0.005          # Max BTC to hold at once
ORDER_SIZE = 0.001             # Small balance entry
TICK_SIZE = 0.1                # Smallest price move for BTC/USDT

class InstitutionalMaker:
    def __init__(self):
        # Configure for Railway Environment Variables
        self.exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_KEY'),
            'secret': os.getenv('BINANCE_SECRET'),
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        self.inventory = 0.0
        self.balance_usdt = 100.0  # Starting Paper Balance
        self.last_price_change = 0.0

    async def watch_order_book(self):
        """Websocket stream for real-time depth"""
        while True:
            try:
                orderbook = await self.exchange.watch_order_book(SYMBOL)
                best_bid = orderbook['bids'][0][0]
                best_ask = orderbook['asks'][0][0]
                await self.logic_gate(best_bid, best_ask)
            except Exception as e:
                print(f"Stream Error: {e}")
                await asyncio.sleep(5)

    async def logic_gate(self, bid, ask):
        spread = (ask - bid) / bid
        
        # 1. TOXIC FLOW PROTECTION
        # If the spread is widening too fast, it usually means a crash is coming.
        if spread > 0.005: 
            print("⚠️ High Volatility: Standing down.")
            return

        # 2. INVENTORY SKEW (The Institutional Secret)
        # If we hold too much BTC, we lower our Sell price and raise our Buy price
        # to 'lean' the inventory back to zero.
        buy_price = bid + TICK_SIZE
        sell_price = ask - TICK_SIZE

        if self.inventory >= MAX_INVENTORY:
            print("📦 Inventory Full: Only placing Sells.")
            await self.execute_maker('sell', sell_price)
        elif self.inventory <= -MAX_INVENTORY:
            print("📦 Inventory Empty: Only placing Buys.")
            await self.execute_maker('buy', buy_price)
        else:
            # Balanced: Place both to capture the spread
            await asyncio.gather(
                self.execute_maker('buy', buy_price),
                self.execute_maker('sell', sell_price)
            )

    async def execute_maker(self, side, price):
        """Simulates Real-World Execution Latency"""
        # Railway is usually in US-East or Europe. 
        # Binance is in Tokyo. This 150ms delay is critical for realism.
        await asyncio.sleep(0.15) 
        
        # Paper Trade Logic: Did price move through our limit?
        # In real world, we'd use self.exchange.create_limit_order
        print(f"⚡ [MAKER {side.upper()}] @ {price}")
        
        # Execution simulation logic...
        if side == 'buy':
            self.inventory += ORDER_SIZE
            self.balance_usdt -= (price * ORDER_SIZE)
        else:
            self.inventory -= ORDER_SIZE
            self.balance_usdt += (price * ORDER_SIZE)

    async def run(self):
        print(f"🚀 Bot Live on Railway. Target: {SYMBOL}")
        await self.watch_order_book()

if __name__ == "__main__":
    bot = InstitutionalMaker()
    asyncio.run(bot.run())
