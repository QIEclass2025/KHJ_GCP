#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
실시간 주식 투자 시뮬레이션 게임 (Yahoo Finance 활용)
"""

# ========== 1. 설정 및 임포트 ==========
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, font
import platform
import os
from datetime import datetime
import random
import threading
from typing import Dict, List, Tuple

# 필수 라이브러리 확인
try:
    import matplotlib
    import yfinance as yf
    import pandas as pd
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    error_message = ("필수 라이브러리(matplotlib, yfinance, pandas)가 설치되지 않았습니다.\n"
                     "터미널에서 'pip install matplotlib yfinance pandas'를 실행해주세요.")
    print(error_message)
    sys.exit(1)

# 게임 설정
INITIAL_CASH = 100000.0
POPULAR_STOCKS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "NFLX", "NUBURU"]

# ========== 2. 데이터 관리자 클래스 ==========
class HistoricalDataManager:
    def __init__(self, symbols):
        self.symbols = symbols
        self.data = {}
        self.current_index = 0
        self.dates = []
        
        print("📥 과거 데이터 다운로드 중... (잠시만 기다려주세요)")
        self._download_data()
        print("✅ 데이터 준비 완료!")

    def _download_data(self):
        start_date = "2024-01-01"
        end_date = "2024-12-31"
        
        for symbol in self.symbols:
            try:
                if symbol == "NUBURU":
                    # Generate synthetic data for NUBURU
                    # We need to know how many days. 2024 is a leap year, so 366 days.
                    # However, trading days are fewer. Let's generate for the full range and filter or just generate enough.
                    # yfinance history returns trading days.
                    # To be safe and consistent with other stocks, let's download one real stock first to get the index,
                    # or if NUBURU is the only one, we might need a calendar.
                    # Assuming other stocks exist, we can use their index if available.
                    # But to be robust, let's just generate for all days and let the game loop handle it,
                    # OR better: wait until we have at least one real stock's data to copy the index.
                    # If NUBURU is processed first, we might have an issue if we rely on others.
                    # Let's generate a date range using pandas for business days in 2024.
                    self.data[symbol] = self._generate_synthetic_data(symbol)
                    if not self.dates and not self.data[symbol].empty:
                         self.dates = self.data[symbol].index.strftime('%Y-%m-%d').tolist()
                else:
                    ticker = yf.Ticker(symbol)
                    df = ticker.history(start=start_date, end=end_date, interval="1d")
                    if not df.empty:
                        self.data[symbol] = df
                        if not self.dates:
                            self.dates = df.index.strftime('%Y-%m-%d').tolist()
            except Exception as e:
                print(f"⚠️ {symbol} 데이터 다운로드 실패: {e}")

    def _generate_synthetic_data(self, symbol):
        """
        Generates synthetic data for a Meme Stock (Pump & Dump logic).
        """
        # Create a date range for 2024 business days
        dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq='B') # 'B' for business days
        
        # Initial Price
        price = 1.00 # Start at $1.00 (Penny Stock)
        
        data = []
        
        for _ in dates:
            # 1. Base Volatility (High Variance: 5% ~ 10%)
            volatility = random.uniform(-0.10, 0.10)
            
            # 2. Jump Event (Pump: 1% prob, +30% ~ +100%)
            if random.random() < 0.01:
                volatility = random.uniform(0.30, 1.00)
                
            # 3. Crash Event (Dump: 1% prob, -30% ~ -50%)
            elif random.random() < 0.01:
                volatility = random.uniform(-0.50, -0.30)
                
            # Apply change
            change = price * volatility
            new_price = price + change
            
            # 4. Price Floor ($0.01)
            new_price = max(0.01, new_price)
            
            # Generate OHLC (Simplified)
            # Open is previous close (or close to it)
            open_p = price
            close_p = new_price
            high_p = max(open_p, close_p) * (1 + random.uniform(0, 0.02))
            low_p = min(open_p, close_p) * (1 - random.uniform(0, 0.02))
            
            data.append([open_p, high_p, low_p, close_p, 0, 0, 0]) # Volume, Dividends, Stock Splits = 0
            
            price = new_price

        # Create DataFrame
        df = pd.DataFrame(data, index=dates, columns=["Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"])
        df.index.name = "Date"
        
        return df

    def get_current_date(self):
        if self.dates and self.current_index < len(self.dates):
            return self.dates[self.current_index]
        return "2024-01-01"

    def get_price_data(self, symbol):
        if symbol not in self.data:
            return None
        df = self.data[symbol]
        idx = min(self.current_index, len(df) - 1)
        row = df.iloc[idx]
        
        prev_row = df.iloc[idx-1] if idx > 0 else row
        change = row['Close'] - prev_row['Close']
        change_percent = (change / prev_row['Close']) * 100 if prev_row['Close'] != 0 else 0
        
        return {
            'c': row['Close'], 'h': row['High'], 'l': row['Low'],
            'o': row['Open'], 'd': change, 'dp': change_percent
        }

    def next_day(self):
        if self.dates and self.current_index < len(self.dates) - 1:
            self.current_index += 1
            return True
        return False

# ========== 3. 뉴스 생성기 클래스 ==========
class NewsGenerator:
    def __init__(self):
        self.good_news = ["실적 서프라이즈", "신제품 기대감", "대규모 계약 체결", "목표 주가 상향", "점유율 1위 달성"]
        self.bad_news = ["원자재 가격 상승", "경쟁 심화 우려", "규제 조사 착수", "실적 전망 하회", "차익 실현 매물"]
        self.neutral_news = ["보합세 유지", "특별한 이슈 부재", "관망세 짙어", "기관 매수세 유입"]

    def generate_news(self, symbol, change_percent):
        if change_percent >= 3.0:
            sentiment, head = "positive", f"[{symbol}] 급등! {random.choice(self.good_news)}"
        elif change_percent <= -3.0:
            sentiment, head = "negative", f"[{symbol}] 급락... {random.choice(self.bad_news)}"
        elif change_percent > 0:
            sentiment, head = "positive", f"[{symbol}] 소폭 상승, {random.choice(self.good_news)}"
        elif change_percent < 0:
            sentiment, head = "negative", f"[{symbol}] 소폭 하락, {random.choice(self.bad_news)}"
        else:
            sentiment, head = "neutral", f"[{symbol}] {random.choice(self.neutral_news)}"

        return {
            'headline': head,
            'summary': f"전일 대비 {change_percent:.2f}% 변동을 보였습니다.",
            'source': 'AI Market Watch',
            'datetime': "", 
            'sentiment': sentiment
        }

# ========== 4. Stock 클래스 (중복 제거 및 수정됨) ==========
class Stock:
    def __init__(self, symbol: str, data_manager):
        self.symbol = symbol
        self.data_manager = data_manager
        self.price_history = [] 
        self.current_price = 0.0
        self.daily_change = 0.0
        self.daily_change_percent = 0.0
        self.update_price() # 초기 가격 설정

    def update_price(self, market_bias=0.0):
        """
        Updates the stock price using the 'Parallel Universe' logic.
        New Price = Old Price * (1 + (Real_Change + Market_Bias + Random_Noise) / 100)
        """
        quote = self.data_manager.get_price_data(self.symbol)
        if quote:
            # 1. Get Real Historical Change (%)
            real_change_percent = quote['dp']
            
            # 2. Generate Idiosyncratic Risk (Random Noise)
            # Gaussian distribution: mean=0, sigma=1.5 (approx +/- 4.5% max deviation usually)
            random_noise = random.gauss(mu=0, sigma=1.5)
            
            # 3. Calculate Total Percent Change
            total_change_percent = real_change_percent + market_bias + random_noise
            
            # 4. Calculate New Price (Cumulative Divergence)
            # If it's the first update, we might want to sync with real price, 
            # but for "Parallel Universe", we start diverging immediately or from the previous simulated price.
            # Here, we assume self.current_price is already set (initially from real data).
            prev_price = self.current_price if self.current_price > 0 else quote['c']
            
            new_price = prev_price * (1 + total_change_percent / 100.0)
            
            # Ensure price doesn't go negative
            self.current_price = max(0.01, new_price)
            
            # Update change metrics
            self.daily_change = self.current_price - prev_price
            self.daily_change_percent = total_change_percent
            
            current_date_str = self.data_manager.get_current_date()
            # 날짜 객체로 변환하여 저장
            dt_obj = datetime.strptime(current_date_str, "%Y-%m-%d")
            
            self.price_history.append((dt_obj, {
                'open': quote['o'], 'high': quote['h'], 'low': quote['l'], 'close': self.current_price # Use simulated close
            }))
            if len(self.price_history) > 365:
                self.price_history.pop(0)

    def get_recommendation_text(self) -> str:
        if self.daily_change_percent > 5.0: return "🔴 Strong Sell"
        elif self.daily_change_percent > 2.0: return "🔴 Sell"
        elif self.daily_change_percent < -5.0: return "🟢 Strong Buy"
        elif self.daily_change_percent < -2.0: return "🟢 Buy"
        else: return "🟡 Hold"

# ========== 5. MarketNews 클래스 (수정됨) ==========
class MarketNews:
    def __init__(self, generator):
        self.generator = generator
        self.news_cache = {}  # 종목별 뉴스
        self.news_log = []    # 전체 뉴스 로그 (GUI 표시용)

    def add_news(self, symbol: str, news_item: dict):
        if symbol not in self.news_cache:
            self.news_cache[symbol] = []
        
        # 종목별 캐시에 추가
        self.news_cache[symbol].insert(0, news_item)
        if len(self.news_cache[symbol]) > 20: self.news_cache[symbol].pop()

        # 전체 로그에 추가
        self.news_log.append(news_item)
        if len(self.news_log) > 50: self.news_log.pop(0)

    def get_stock_news(self, symbol: str) -> List[dict]:
        return self.news_cache.get(symbol, [])

    def get_market_sentiment(self) -> str:
        val = random.random()
        if val > 0.7: return "🟢 강세 (Bullish)"
        elif val < 0.3: return "🔴 약세 (Bearish)"
        else: return "🟡 중립 (Neutral)"

# ========== 6. Player 클래스 ==========
class Player:
    def __init__(self, initial_cash: float = INITIAL_CASH):
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.portfolio = {}
        self.trade_history = []

    def buy_stock(self, symbol: str, shares: int, price: float) -> bool:
        total_cost = shares * price
        if total_cost > self.cash: return False
        self.cash -= total_cost

        if symbol in self.portfolio:
            old_s = self.portfolio[symbol]['shares']
            old_p = self.portfolio[symbol]['avg_price']
            new_s = old_s + shares
            new_p = (old_s * old_p + shares * price) / new_s
            self.portfolio[symbol] = {'shares': new_s, 'avg_price': new_p}
        else:
            self.portfolio[symbol] = {'shares': shares, 'avg_price': price}

        self.trade_history.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'type': '매수', 'symbol': symbol, 'shares': shares, 'price': price
        })
        return True

    def sell_stock(self, symbol: str, shares: int, price: float) -> bool:
        if symbol not in self.portfolio or self.portfolio[symbol]['shares'] < shares:
            return False
        total_revenue = shares * price
        self.cash += total_revenue
        self.portfolio[symbol]['shares'] -= shares
        if self.portfolio[symbol]['shares'] == 0: del self.portfolio[symbol]

        self.trade_history.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'type': '매도', 'symbol': symbol, 'shares': shares, 'price': price
        })
        return True

    def get_total_assets(self, stocks: Dict[str, Stock]) -> float:
        val = sum(stocks[sym].current_price * d['shares'] for sym, d in self.portfolio.items() if sym in stocks)
        return self.cash + val

    def get_profit_loss(self, stocks: Dict[str, Stock]) -> Tuple[float, float]:
        total = self.get_total_assets(stocks)
        profit = total - self.initial_cash
        pct = (profit / self.initial_cash) * 100
        return profit, pct

    def get_portfolio_summary(self, stocks: Dict[str, Stock]) -> List[dict]:
        summary = []
        for sym, data in self.portfolio.items():
            if sym in stocks:
                curr = stocks[sym].current_price
                cost = data['avg_price'] * data['shares']
                curr_val = curr * data['shares']
                prof = curr_val - cost
                prof_pct = (prof/cost*100) if cost>0 else 0
                summary.append({
                    'symbol': sym, 'shares': data['shares'], 'avg_price': data['avg_price'],
                    'current_price': curr, 'profit': prof, 'profit_percent': prof_pct
                })
        return summary

# ========== 7. GameEngine 클래스  ==========
class GameEngine:
    def __init__(self):
        self.symbols = POPULAR_STOCKS
        self.data_manager = HistoricalDataManager(self.symbols)
        self.news_generator = NewsGenerator()
        self.market_news = MarketNews(self.news_generator)
        self.stocks = {}
        self.player = Player()
        self.tick_count = 0 
        
        # 주식 객체 생성
        for symbol in self.symbols:
            self.stocks[symbol] = Stock(symbol, self.data_manager)

    def next_turn(self, days=1):
        """다음 턴(하루 또는 여러 날) 진행"""
        for _ in range(days):
            self.tick_count += 1
            has_next = self.data_manager.next_day()
            
            if not has_next:
                return False, True # Game Over(X), Data End(O)

            current_date_str = self.data_manager.get_current_date()
            
            # --- Calculate Market Bias (Systemic Risk) ---
            market_bias = self._calculate_market_bias()

            for symbol, stock in self.stocks.items():
                # Pass market bias to stock update
                stock.update_price(market_bias)
                
                # 뉴스 생성 (3% 이상 변동 시)
                if abs(stock.daily_change_percent) > 3.0:
                    news_item = self.news_generator.generate_news(symbol, stock.daily_change_percent)
                    news_item['datetime'] = current_date_str
                    self.market_news.add_news(symbol, news_item)

            # 랜덤 이벤트 (Market Bias가 매우 클 때 추가 뉴스 생성 가능)
            if market_bias < -5.0:
                self.market_news.add_news("MARKET", {
                    'headline': "📉 Market Crash! Panic Selling!", 
                    'summary': 'The market is taking a heavy hit.',
                    'source': 'Global News', 'datetime': current_date_str, 'sentiment': 'negative'
                })
            elif market_bias > 5.0:
                self.market_news.add_news("MARKET", {
                    'headline': "📈 Bull Run! Market is Booming!", 
                    'summary': 'Investors are optimistic.',
                    'source': 'Global News', 'datetime': current_date_str, 'sentiment': 'positive'
                })

            if self.check_game_over():
                return True, False
        
        return False, False

    def _calculate_market_bias(self) -> float:
        """
        Determines the daily market sentiment (Systemic Risk).
        Returns a percentage bias (e.g., -10.0 for -10%).
        """
        rand_val = random.random()
        
        # 1. Crash (Black Swan): 2% probability
        if rand_val < 0.02:
            # Bias: -10% to -15%
            return random.uniform(-15.0, -10.0)
        
        # 2. Bear Market: 15% probability (0.02 to 0.17)
        elif rand_val < 0.17:
            # Bias: -2% to -5%
            return random.uniform(-5.0, -2.0)
            
        # 3. Bull Market: 15% probability (0.17 to 0.32)
        elif rand_val < 0.32:
            # Bias: +3% to +8%
            return random.uniform(3.0, 8.0)
            
        # 4. Normal Market: 68% probability
        else:
            # Bias: -1% to +1% (Slight variance)
            return random.uniform(-1.0, 1.0)

    def _trigger_random_event(self, date_str):
        events = [("📈 금리 동결 시사!", "positive"), ("📉 물가지수 쇼크!", "negative")]
        headline, sentiment = random.choice(events)
        self.market_news.add_news("MARKET", {
            'headline': headline, 'summary': '거시경제 뉴스 발생',
            'source': 'Global News', 'datetime': date_str, 'sentiment': sentiment
        })

    def check_game_over(self) -> bool:
        total = self.player.get_total_assets(self.stocks)
        return total <= self.player.initial_cash * 0.3

    def save_game(self): pass 
    def load_game(self): return False

# ========== 8. StockTradingGUI 클래스 (UI Redesign) ==========
def get_default_font_name():
    system = platform.system()
    if system == "Windows": return "Malgun Gothic"
    elif system == "Darwin": return "AppleGothic"
    return "NanumGothic"

class StockTradingGUI:
    # --- Color Palette (Toss Securities Style Dark Mode) ---
    COLOR_BG = "#191919"        # Deep Dark Background
    COLOR_CARD = "#2C2C2C"      # Card Background
    COLOR_TEXT = "#FFFFFF"      # Primary Text
    COLOR_TEXT_SUB = "#B0B0B0"  # Secondary Text
    COLOR_ACCENT_UP = "#FF4B4B" # Red (Rise)
    COLOR_ACCENT_DOWN = "#4B89DC"# Blue (Fall)
    COLOR_PRIMARY = "#3182F6"   # Toss Blue
    COLOR_BORDER = "#333333"    # Subtle Border

    def __init__(self, root: tk.Tk, game_engine: GameEngine):
        self.root = root
        self.game = game_engine
        self.root.title("Stock Simulator")
        self.root.geometry("1400x900")
        self.root.configure(bg=self.COLOR_BG)

        self.font_name = get_default_font_name()
        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('default')

        # Configure Colors & Fonts
        style.configure(".", 
                        background=self.COLOR_BG, 
                        foreground=self.COLOR_TEXT, 
                        font=(self.font_name, 10))
        
        style.configure("TFrame", background=self.COLOR_BG)
        
        # Card Style (for panels)
        style.configure("Card.TFrame", background=self.COLOR_CARD, relief="flat")
        
        # Label Styles
        style.configure("TLabel", background=self.COLOR_BG, foreground=self.COLOR_TEXT)
        style.configure("Card.TLabel", background=self.COLOR_CARD, foreground=self.COLOR_TEXT)
        style.configure("Header.TLabel", font=(self.font_name, 20, "bold"), background=self.COLOR_BG, foreground=self.COLOR_TEXT)
        style.configure("SubHeader.TLabel", font=(self.font_name, 14, "bold"), background=self.COLOR_CARD, foreground=self.COLOR_TEXT)
        style.configure("Value.TLabel", font=(self.font_name, 12), background=self.COLOR_CARD, foreground=self.COLOR_TEXT)

        # Button Styles
        style.configure("TButton", 
                        font=(self.font_name, 10, "bold"), 
                        background=self.COLOR_PRIMARY, 
                        foreground="white", 
                        borderwidth=0, 
                        focuscolor=self.COLOR_PRIMARY)
        style.map("TButton", 
                  background=[('active', '#2565C0')], 
                  foreground=[('active', 'white')])
        
        style.configure("Buy.TButton", background=self.COLOR_ACCENT_UP)
        style.map("Buy.TButton", background=[('active', '#D32F2F')])
        
        style.configure("Sell.TButton", background=self.COLOR_ACCENT_DOWN)
        style.map("Sell.TButton", background=[('active', '#1976D2')])

        # Treeview (List) Style
        style.configure("Treeview", 
                        background=self.COLOR_BG, 
                        foreground=self.COLOR_TEXT, 
                        fieldbackground=self.COLOR_BG, 
                        rowheight=30,
                        borderwidth=0)
        style.configure("Treeview.Heading", 
                        background=self.COLOR_CARD, 
                        foreground=self.COLOR_TEXT, 
                        font=(self.font_name, 10, "bold"),
                        borderwidth=0)
        style.map("Treeview", background=[('selected', self.COLOR_CARD)], foreground=[('selected', self.COLOR_TEXT)])

    def setup_ui(self):
        # Main Layout
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # --- 1. Header (Dashboard) ---
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        # App Title
        ttk.Label(header_frame, text="Stock Simulator", style="Header.TLabel").pack(side=tk.LEFT)
        
        # Dashboard Info
        self.dashboard_labels = {}
        info_container = ttk.Frame(header_frame)
        info_container.pack(side=tk.RIGHT)

        for key, label in [("game_time", "Date"), ("cash", "Cash"), ("total_assets", "Total Assets"), ("profit_percent", "Return")]:
            frame = ttk.Frame(info_container, padding=(15, 0))
            frame.pack(side=tk.LEFT)
            ttk.Label(frame, text=label, foreground=self.COLOR_TEXT_SUB, font=(self.font_name, 9)).pack(anchor="e")
            lbl = ttk.Label(frame, text="-", font=(self.font_name, 12, "bold"))
            lbl.pack(anchor="e")
            self.dashboard_labels[key] = lbl

        # --- 2. Content Area ---
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left Panel (Market & Portfolio)
        left_panel = ttk.Frame(content_frame, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 20))
        
        # Right Panel (Chart, Trade, News)
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Left Panel Content ---
        # Stock List
        stock_card = self._create_card(left_panel, "Market")
        stock_card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        cols = ("Symbol", "Price", "Chg%", "Rec")
        self.stock_tree = ttk.Treeview(stock_card, columns=cols, show='headings', height=10)
        for col in cols: 
            self.stock_tree.heading(col, text=col)
            self.stock_tree.column(col, width=70 if col != "Rec" else 100, anchor="e" if col != "Symbol" else "w")
        self.stock_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.stock_tree.bind('<<TreeviewSelect>>', self.on_stock_select)

        # Portfolio
        port_card = self._create_card(left_panel, "My Portfolio")
        port_card.pack(fill=tk.BOTH, expand=True)
        
        p_cols = ("Symbol", "Shares", "Avg", "Rtn%")
        self.port_tree = ttk.Treeview(port_card, columns=p_cols, show='headings', height=8)
        for col in p_cols: 
            self.port_tree.heading(col, text=col)
            self.port_tree.column(col, width=70, anchor="e" if col != "Symbol" else "w")
        self.port_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.port_tree.bind('<<TreeviewSelect>>', self.on_port_select)

        # --- Right Panel Content ---
        # Chart Area
        chart_card = self._create_card(right_panel, "Price Chart")
        chart_card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.fig = Figure(figsize=(5, 3), dpi=100, facecolor=self.COLOR_CARD)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.COLOR_CARD)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_card)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Bottom Section (Trade & News)
        bottom_frame = ttk.Frame(right_panel)
        bottom_frame.pack(fill=tk.X, ipady=10)

        # Trade Panel
        trade_card = self._create_card(bottom_frame, "Order")
        trade_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        trade_inner = ttk.Frame(trade_card, style="Card.TFrame", padding=15)
        trade_inner.pack(fill=tk.BOTH, expand=True)

        self.symbol_var = tk.StringVar()
        self.shares_var = tk.StringVar(value="1")

        # Selected Stock Info
        self.lbl_selected_stock = ttk.Label(trade_inner, text="Select a stock", font=(self.font_name, 14, "bold"), style="Card.TLabel")
        self.lbl_selected_stock.pack(anchor="w", pady=(0, 10))

        # Inputs
        input_frame = ttk.Frame(trade_inner, style="Card.TFrame")
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(input_frame, text="Quantity", style="Card.TLabel").pack(side=tk.LEFT)
        # Use tk.Entry for better color control in dark mode
        entry = tk.Entry(input_frame, textvariable=self.shares_var, width=10, font=(self.font_name, 12),
                         bg=self.COLOR_CARD, fg=self.COLOR_TEXT, insertbackground=self.COLOR_TEXT,
                         relief="flat", highlightthickness=1, highlightbackground=self.COLOR_BORDER)
        entry.pack(side=tk.RIGHT)

        # Buttons
        btn_frame = ttk.Frame(trade_inner, style="Card.TFrame")
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Buy", style="Buy.TButton", command=self.buy_stock).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(btn_frame, text="Sell", style="Sell.TButton", command=self.sell_stock).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        # Next Day Buttons
        next_day_frame = ttk.Frame(trade_inner, style="Card.TFrame")
        next_day_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(next_day_frame, text="+1 Day", command=lambda: self.next_turn(1)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(next_day_frame, text="+3 Days", command=lambda: self.next_turn(3)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(next_day_frame, text="+1 Week", command=lambda: self.next_turn(7)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        # News Panel
        news_card = self._create_card(bottom_frame, "Market News")
        news_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.news_text = scrolledtext.ScrolledText(news_card, height=10, bg=self.COLOR_BG, fg=self.COLOR_TEXT, 
                                                   insertbackground="white", relief="flat", padx=10, pady=10)
        self.news_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.update_all()

    def _create_card(self, parent, title):
        card = ttk.Frame(parent, style="Card.TFrame", padding=1) # Padding for border effect if needed
        # Title Header
        header = ttk.Frame(card, style="Card.TFrame", padding=(15, 10))
        header.pack(fill=tk.X)
        ttk.Label(header, text=title, style="SubHeader.TLabel").pack(side=tk.LEFT)
        return card

    def update_all(self):
        # 1. Dashboard
        pl = self.game.player
        profit, pct = pl.get_profit_loss(self.game.stocks)
        
        self.dashboard_labels['total_assets'].config(text=f"${pl.get_total_assets(self.game.stocks):,.0f}")
        self.dashboard_labels['cash'].config(text=f"${pl.cash:,.0f}")
        
        color = self.COLOR_ACCENT_UP if pct >= 0 else self.COLOR_ACCENT_DOWN
        self.dashboard_labels['profit_percent'].config(text=f"{pct:+.2f}%", foreground=color)
        self.dashboard_labels['game_time'].config(text=self.game.data_manager.get_current_date())

        # 2. Stock List
        for item in self.stock_tree.get_children(): self.stock_tree.delete(item)
        for sym, stock in self.game.stocks.items():
            # Determine color based on daily change
            color_tag = "up" if stock.daily_change >= 0 else "down"
            self.stock_tree.insert("", "end", values=(
                sym, f"${stock.current_price:.2f}", f"{stock.daily_change_percent:+.2f}%", stock.get_recommendation_text()
            ), tags=(color_tag,))
        
        self.stock_tree.tag_configure("up", foreground=self.COLOR_ACCENT_UP)
        self.stock_tree.tag_configure("down", foreground=self.COLOR_ACCENT_DOWN)

        # 3. Portfolio
        for item in self.port_tree.get_children(): self.port_tree.delete(item)
        for p in pl.get_portfolio_summary(self.game.stocks):
            color_tag = "up" if p['profit'] >= 0 else "down"
            self.port_tree.insert("", "end", values=(
                p['symbol'], p['shares'], f"${p['avg_price']:.2f}", f"{p['profit_percent']:+.2f}%"
            ), tags=(color_tag,))
        
        self.port_tree.tag_configure("up", foreground=self.COLOR_ACCENT_UP)
        self.port_tree.tag_configure("down", foreground=self.COLOR_ACCENT_DOWN)

        # 4. Chart & News
        if self.symbol_var.get(): 
            self.update_chart(self.symbol_var.get())
            self.lbl_selected_stock.config(text=f"{self.symbol_var.get()}  ${self.game.stocks[self.symbol_var.get()].current_price:.2f}")
        else:
            self.lbl_selected_stock.config(text="Select a stock")
            
        self.refresh_news()

    def update_chart(self, symbol):
        stock = self.game.stocks.get(symbol)
        if not stock or not stock.price_history: return
        
        self.ax.clear()
        dates = [x[0] for x in stock.price_history]
        closes = [x[1]['close'] for x in stock.price_history]
        
        # Dark Theme Chart
        self.ax.plot(dates, closes, label=symbol, color=self.COLOR_PRIMARY, linewidth=2)
        self.ax.fill_between(dates, closes, alpha=0.1, color=self.COLOR_PRIMARY)
        
        self.ax.set_title(f"{symbol} Price chart", color=self.COLOR_TEXT, pad=10)
        self.ax.tick_params(axis='x', colors=self.COLOR_TEXT_SUB)
        self.ax.tick_params(axis='y', colors=self.COLOR_TEXT_SUB)
        self.ax.spines['bottom'].set_color(self.COLOR_BORDER)
        self.ax.spines['top'].set_color(self.COLOR_BORDER) 
        self.ax.spines['left'].set_color(self.COLOR_BORDER)
        self.ax.spines['right'].set_color(self.COLOR_BORDER)
        self.ax.grid(True, color=self.COLOR_BORDER, linestyle='--', alpha=0.5)
        
        import matplotlib.dates as mdates
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//5)))
        self.fig.autofmt_xdate()
        self.canvas.draw()

    def refresh_news(self):
        self.news_text.config(state=tk.NORMAL) # Enable editing
        self.news_text.delete(1.0, tk.END)
        for news in reversed(self.game.market_news.news_log[-15:]):
            icon = "🔴" if news['sentiment'] == 'negative' else "🟢" if news['sentiment'] == 'positive' else "⚪"
            
            # Insert Headline
            self.news_text.insert(tk.END, f"{icon} {news['headline']}\n", "headline")
            
            # Insert Details
            self.news_text.insert(tk.END, f"   {news['datetime']} | {news['source']}\n\n", "details")
            
        # Configure tags for colors
        self.news_text.tag_config("headline", foreground=self.COLOR_TEXT, font=(self.font_name, 10, "bold"))
        self.news_text.tag_config("details", foreground=self.COLOR_TEXT_SUB, font=(self.font_name, 9))
        self.news_text.config(state=tk.DISABLED) # Disable editing

    def show_game_result(self):
        pl = self.game.player
        profit, pct = pl.get_profit_loss(self.game.stocks)
        total_assets = pl.get_total_assets(self.game.stocks)
        
        # Determine Tier
        if pct >= 100: tier, icon = "주식의 신 - 당신은 워렌 버핏입니다", "👑"
        elif pct >= 50: tier, icon = "수익률이 좋으시군요. 메로나 하나만 사주시길", "💎"
        elif pct >= 20: tier, icon = "좋은 수익률입니다. 축하드립니다", "🥇"
        elif pct >= 0: tier, icon = "흔한 투자자이시군요.", "🥈"
        elif pct > -20: tier, icon = "당신은 주린이입니다. 광대가 되지 않게 조심하십시요.", "🥉"
        else: tier, icon = "당신은 전인구입니다. 제발 당신의 계좌를 생각해서라도 주식은 하지 마십쇼", "💩"
        
        msg = (f"=== 2024 Season Finished ===\n\n"
               f"Final Assets: ${total_assets:,.0f}\n"
               f"Total Return: {pct:+.2f}%\n\n"
               f"Your Rank: {icon} {tier}")
        
        messagebox.showinfo("Game Clear!", msg)
        self.root.quit()

    def next_turn(self, days=1):
        is_over, is_end = self.game.next_turn(days)
        if is_over: 
            messagebox.showinfo("게임오버", "파산!")
            self.root.quit()
        elif is_end: 
            self.show_game_result()
        else: 
            self.update_all()

    def buy_stock(self): self._trade(True)
    def sell_stock(self): self._trade(False)

    def _trade(self, is_buy):
        sym = self.symbol_var.get()
        try: shares = int(self.shares_var.get())
        except: return
        if not sym or shares < 1: return
        
        price = self.game.stocks[sym].current_price
        success = self.game.player.buy_stock(sym, shares, price) if is_buy else self.game.player.sell_stock(sym, shares, price)
        
        if success: 
            self.update_all()
            # messagebox.showinfo("Success", f"{'Buy' if is_buy else 'Sell'} Complete!") # Removed popup for smoother flow
        else: messagebox.showerror("Failed", "Insufficient funds or shares")

    def on_stock_select(self, e):
        sel = self.stock_tree.selection()
        if sel: 
            sym = self.stock_tree.item(sel[0])['values'][0]
            self.symbol_var.set(sym)
            self.update_all() # Update chart and selected label

    def on_port_select(self, e):
        sel = self.port_tree.selection()
        if sel:
            sym = self.port_tree.item(sel[0])['values'][0]
            self.symbol_var.set(sym)
            self.update_all()

# ========== 9. Main Execution ==========
if __name__ == "__main__":
    game = GameEngine()
    root = tk.Tk()
    
    # Set window background immediately to avoid white flash
    root.configure(bg="#191919")
    
    app = StockTradingGUI(root, game)
    root.mainloop()