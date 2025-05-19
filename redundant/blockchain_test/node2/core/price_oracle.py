"""
Simplified Price Oracle for Blockchain Core
"""
import time
from dataclasses import dataclass
from collections import deque
from typing import List, Dict, Optional

@dataclass
class OrderBookEntry:
    price: float
    amount: float
    timestamp: float
    order_type: str  # "BUY" or "SELL"

@dataclass
class TradeHistory:
    price: float
    amount: float
    timestamp: float

class PriceOracle:
    def __init__(self):
        self.buy_orders: List[OrderBookEntry] = []
        self.sell_orders: List[OrderBookEntry] = []
        self.trade_history: deque = deque(maxlen=1000)
        self.last_price: float = 0.01
        self.price_history: Dict[int, float] = {}
        
        # Market metrics
        self.volume_24h: float = 0.0
        self.high_24h: float = 0.0
        self.low_24h: Optional[float] = None
        
    def get_current_price(self) -> float:
        """Get current market price"""
        return self.last_price
    
    def calculate_market_price(self, blockchain) -> float:
        """Simplified market price calculation"""
        # Ensure base_price is valid
        base_price = self.last_price if self.last_price is not None and self.last_price > 0 else 0.01
        
        # Basic market price calculation
        market_price = base_price
        
        # Add some variation based on blockchain metrics
        try:
            if hasattr(blockchain, 'chain') and len(blockchain.chain) > 0:
                # Make price increase with more mined blocks
                block_factor = 1.0 + (0.001 * len(blockchain.chain))
                market_price *= block_factor
                
                # Add transaction activity factor
                tx_count = sum(len(block.transactions) for block in blockchain.chain[-5:])
                tx_factor = 1.0 + (min(tx_count, 50) * 0.001)
                market_price *= tx_factor
        except (AttributeError, IndexError):
            pass
            
        return round(market_price, 8)  # Round to 8 decimal places
        
    def add_order(self, price, amount, order_type):
        """Add an order to the order book"""
        if price <= 0 or amount <= 0:
            return
            
        entry = OrderBookEntry(float(price), float(amount), time.time(), order_type)
        
        if order_type == "BUY":
            self.buy_orders.append(entry)
            # Sort buy orders by price (highest first)
            self.buy_orders.sort(key=lambda x: x.price, reverse=True)
        else:
            self.sell_orders.append(entry)
            # Sort sell orders by price (lowest first)
            self.sell_orders.sort(key=lambda x: x.price)

# Create global instance
PRICE_ORACLE = PriceOracle()