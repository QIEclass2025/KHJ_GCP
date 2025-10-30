#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
실시간 주식 투자 시뮬레이션 게임 (Finnhub API 활용)
- 단일 파일로 구성된 포터블 코드
- Finnhub 무료 API를 활용한 실시간 주가 및 뉴스
- tkinter GUI 인터페이스
"""

# ========== 1. 설정 및 임포트 ==========
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# requests 모듈 자동 설치
try:
    import requests
except ImportError:
    print("requests 모듈이 설치되지 않았습니다. 자동으로 설치합니다...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "requests"])
    import requests
    print("requests 모듈 설치 완료!")

# matplotlib 모듈 자동 설치
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    print("matplotlib 모듈이 설치되지 않았습니다. 자동으로 설치합니다...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "matplotlib"])
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    print("matplotlib 모듈 설치 완료!")

import json
from datetime import datetime, timedelta
import random
import time
from collections import deque, defaultdict
import threading
from typing import Dict, List, Optional, Tuple
import os

# ========== 2. API 설정 ==========
FINNHUB_API_KEY = "d3hkbh1r01qi2vu1akb0d3hkbh1r01qi2vu1akbg"  # 여기에 발급받은 API 키를 입력하세요!
API_BASE_URL = "https://finnhub.io/api/v1"

# 게임 설정
INITIAL_CASH = 10000.0
POPULAR_STOCKS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
CACHE_DURATION = 60  # 캐시 유효 시간 (초)
MAX_API_CALLS_PER_MINUTE = 60  # Finnhub 무료 제한

# 게임 시간 설정
GAME_START_DATE = datetime(2024, 1, 1, 9, 0)  # 게임 시작 시간: 2024년 1월 1일 오전 9시
HOURS_PER_TICK = 3  # 한 턴당 3시간 진행
MARKET_OPEN_HOUR = 9  # 시장 개장 시간
MARKET_CLOSE_HOUR = 16  # 시장 마감 시간

# ========== 3. FinnhubAPI 클래스 ==========
class FinnhubAPI:
    """Finnhub API 호출 및 rate limiting, 캐싱 관리"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = API_BASE_URL
        self.cache = {}  # {endpoint: {'data': data, 'timestamp': timestamp}}
        self.call_times = deque(maxlen=MAX_API_CALLS_PER_MINUTE)
        self.offline_mode = False

    def _wait_if_rate_limited(self):
        """Rate limit 관리 - 분당 60회 제한"""
        now = time.time()
        # 1분 이전 호출 제거
        while self.call_times and self.call_times[0] < now - 60:
            self.call_times.popleft()

        # 60회 도달 시 대기
        if len(self.call_times) >= MAX_API_CALLS_PER_MINUTE:
            wait_time = 60 - (now - self.call_times[0])
            if wait_time > 0:
                print(f"⏳ Rate limit 도달. {wait_time:.1f}초 대기 중...")
                time.sleep(wait_time)

        self.call_times.append(time.time())

    def _get_cached(self, cache_key: str) -> Optional[dict]:
        """캐시에서 데이터 가져오기"""
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < CACHE_DURATION:
                return cached['data']
        return None

    def _set_cache(self, cache_key: str, data: dict):
        """캐시에 데이터 저장"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }

    def _make_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """API 요청 실행"""
        cache_key = f"{endpoint}:{json.dumps(params or {}, sort_keys=True)}"

        # 캐시 확인
        cached_data = self._get_cached(cache_key)
        if cached_data:
            return cached_data

        # 오프라인 모드면 시뮬레이션 데이터 반환
        if self.offline_mode:
            return self._generate_fallback_data(endpoint, params)

        try:
            # Rate limit 체크
            self._wait_if_rate_limited()

            # API 호출
            params = params or {}
            params['token'] = self.api_key
            url = f"{self.base_url}/{endpoint}"

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self._set_cache(cache_key, data)
                return data
            elif response.status_code == 401:
                messagebox.showerror("API 키 오류",
                    "Finnhub API 키가 잘못되었습니다.\n코드 상단의 FINNHUB_API_KEY를 확인하세요.")
                return None
            else:
                print(f"⚠️ API 오류: {response.status_code}")
                return self._generate_fallback_data(endpoint, params)

        except requests.exceptions.RequestException as e:
            print(f"⚠️ 네트워크 오류: {e}")
            self.offline_mode = True
            return self._generate_fallback_data(endpoint, params)

    def _generate_fallback_data(self, endpoint: str, params: dict) -> dict:
        """오프라인/오류 시 시뮬레이션 데이터 생성"""
        if 'quote' in endpoint:
            base_price = random.uniform(100, 500)
            change = random.uniform(-5, 5)
            return {
                'c': base_price,  # current price
                'h': base_price + random.uniform(0, 10),  # high
                'l': base_price - random.uniform(0, 10),  # low
                'o': base_price - change,  # open
                'pc': base_price - change,  # previous close
                'd': change,  # change
                'dp': (change / base_price) * 100  # percent change
            }
        elif 'company-news' in endpoint or 'news' in endpoint:
            return [
                {
                    'headline': f"시뮬레이션 뉴스: {params.get('symbol', 'MARKET')} 관련 소식",
                    'summary': "오프라인 모드에서 생성된 시뮬레이션 뉴스입니다.",
                    'source': 'Simulation',
                    'datetime': int(time.time()),
                    'sentiment': random.choice(['positive', 'negative', 'neutral'])
                }
                for _ in range(3)
            ]
        elif 'stock/profile2' in endpoint:
            return {
                'name': params.get('symbol', 'Unknown'),
                'ticker': params.get('symbol', 'N/A'),
                'marketCapitalization': random.uniform(100, 3000),
                'finnhubIndustry': 'Technology'
            }
        elif 'stock/recommendation' in endpoint:
            return [
                {
                    'buy': random.randint(5, 20),
                    'hold': random.randint(5, 15),
                    'sell': random.randint(0, 10),
                    'strongBuy': random.randint(5, 15),
                    'strongSell': random.randint(0, 5),
                    'period': datetime.now().strftime('%Y-%m-%d')
                }
            ]
        return {}

    def get_quote(self, symbol: str) -> Optional[dict]:
        """실시간 주가 조회"""
        return self._make_request('quote', {'symbol': symbol})

    def get_company_news(self, symbol: str, days_back: int = 7) -> List[dict]:
        """기업 뉴스 조회"""
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        news = self._make_request('company-news', {
            'symbol': symbol,
            'from': from_date,
            'to': to_date
        })
        return news[:10] if news else []  # 최대 10개

    def get_market_news(self, category: str = 'general') -> List[dict]:
        """시장 전체 뉴스 조회"""
        news = self._make_request('news', {'category': category})
        return news[:10] if news else []

    def get_company_profile(self, symbol: str) -> Optional[dict]:
        """기업 프로필 조회"""
        return self._make_request('stock/profile2', {'symbol': symbol})

    def get_recommendations(self, symbol: str) -> List[dict]:
        """애널리스트 추천 조회"""
        recs = self._make_request('stock/recommendation', {'symbol': symbol})
        return recs if recs else []


# ========== 4. Stock 클래스 ==========
class Stock:
    """주식 종목 클래스"""

    def __init__(self, symbol: str, api: FinnhubAPI):
        self.symbol = symbol
        self.api = api
        self.price_history = []  # [(timestamp, {'open': o, 'high': h, 'low': l, 'close': c}), ...]
        self.current_price = 0.0
        self.daily_change = 0.0
        self.daily_change_percent = 0.0
        self.company_name = symbol
        self.market_cap = 0.0
        self.industry = "Unknown"

        # 초기 데이터 로드
        self.update_price()
        self.load_company_info()

    def update_price(self):
        """실시간 가격 업데이트"""
        quote = self.api.get_quote(self.symbol)
        if quote and 'c' in quote:
            self.current_price = quote['c']
            self.daily_change = quote.get('d', 0)
            self.daily_change_percent = quote.get('dp', 0)

            # 히스토리 저장 (최대 100개)
            self.price_history.append((time.time(), self.current_price))
            if len(self.price_history) > 100:
                self.price_history.pop(0)

    def load_company_info(self):
        """기업 정보 로드"""
        profile = self.api.get_company_profile(self.symbol)
        if profile:
            self.company_name = profile.get('name', self.symbol)
            self.market_cap = profile.get('marketCapitalization', 0)
            self.industry = profile.get('finnhubIndustry', 'Unknown')

    def get_recommendation_text(self) -> str:
        """애널리스트 추천 텍스트"""
        recs = self.api.get_recommendations(self.symbol)
        if recs:
            latest = recs[0]
            strong_buy = latest.get('strongBuy', 0)
            buy = latest.get('buy', 0)
            hold = latest.get('hold', 0)
            sell = latest.get('sell', 0)

            total = strong_buy + buy + hold + sell
            if total == 0:
                return "N/A"

            if strong_buy + buy > sell * 2:
                return "🟢 Strong Buy"
            elif strong_buy + buy > sell:
                return "🟢 Buy"
            elif sell > buy * 2:
                return "🔴 Sell"
            else:
                return "🟡 Hold"
        return "N/A"

    def get_52week_range(self) -> Tuple[float, float]:
        """52주 최고/최저 (시뮬레이션)"""
        if self.current_price:
            low = self.current_price * random.uniform(0.7, 0.9)
            high = self.current_price * random.uniform(1.1, 1.3)
            return (low, high)
        return (0, 0)


# ========== 5. MarketNews 클래스 ==========
class MarketNews:
    """뉴스 관리 및 센티먼트 분석"""

    def __init__(self, api: FinnhubAPI):
        self.api = api
        self.news_cache = {}  # {symbol: [news_items]}

    def get_stock_news(self, symbol: str) -> List[dict]:
        """종목별 뉴스 가져오기"""
        news = self.api.get_company_news(symbol)
        enhanced_news = []

        for item in news:
            # 센티먼트 분석 (간단한 키워드 기반)
            sentiment = self._analyze_sentiment(item.get('headline', '') + ' ' + item.get('summary', ''))
            enhanced_news.append({
                'headline': item.get('headline', 'No headline'),
                'summary': item.get('summary', ''),
                'source': item.get('source', 'Unknown'),
                'datetime': item.get('datetime', int(time.time())),
                'sentiment': sentiment,
                'url': item.get('url', '')
            })

        self.news_cache[symbol] = enhanced_news
        return enhanced_news

    def get_market_sentiment(self) -> str:
        """전체 시장 분위기"""
        market_news = self.api.get_market_news()
        if not market_news:
            return "중립"

        sentiments = [self._analyze_sentiment(n.get('headline', '') + ' ' + n.get('summary', ''))
                     for n in market_news]

        positive = sentiments.count('positive')
        negative = sentiments.count('negative')

        if positive > negative * 1.5:
            return "🟢 강세"
        elif negative > positive * 1.5:
            return "🔴 약세"
        else:
            return "🟡 중립"

    def _analyze_sentiment(self, text: str) -> str:
        """간단한 센티먼트 분석"""
        text = text.lower()

        positive_words = ['surge', 'gain', 'rise', 'up', 'growth', 'profit', 'beat',
                         'success', 'bullish', 'positive', 'strong', 'high', 'record']
        negative_words = ['fall', 'drop', 'decline', 'loss', 'miss', 'concern',
                         'bearish', 'negative', 'weak', 'low', 'crash', 'sell-off']

        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)

        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'

    def calculate_news_impact(self, symbol: str) -> float:
        """뉴스가 주가에 미치는 영향 계산 (-5% ~ +5%)"""
        news = self.news_cache.get(symbol, [])
        if not news:
            return 0.0

        recent_news = news[:5]  # 최근 5개
        sentiments = [n['sentiment'] for n in recent_news]

        impact = 0.0
        for s in sentiments:
            if s == 'positive':
                impact += random.uniform(0.5, 1.5)
            elif s == 'negative':
                impact += random.uniform(-1.5, -0.5)

        return max(-5.0, min(5.0, impact))  # -5% ~ +5% 제한


# ========== 6. Player 클래스 ==========
class Player:
    """플레이어 클래스 - 포트폴리오 관리"""

    def __init__(self, initial_cash: float = INITIAL_CASH):
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.portfolio = {}  # {symbol: {'shares': int, 'avg_price': float}}
        self.trade_history = []  # [{timestamp, type, symbol, shares, price}, ...]

    def buy_stock(self, symbol: str, shares: int, price: float) -> bool:
        """주식 매수"""
        total_cost = shares * price

        if total_cost > self.cash:
            return False

        self.cash -= total_cost

        if symbol in self.portfolio:
            # 평균 단가 재계산
            old_shares = self.portfolio[symbol]['shares']
            old_avg = self.portfolio[symbol]['avg_price']
            new_shares = old_shares + shares
            new_avg = (old_shares * old_avg + shares * price) / new_shares

            self.portfolio[symbol] = {'shares': new_shares, 'avg_price': new_avg}
        else:
            self.portfolio[symbol] = {'shares': shares, 'avg_price': price}

        # 거래 히스토리 저장
        self.trade_history.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': '매수',
            'symbol': symbol,
            'shares': shares,
            'price': price
        })

        return True

    def sell_stock(self, symbol: str, shares: int, price: float) -> bool:
        """주식 매도"""
        if symbol not in self.portfolio or self.portfolio[symbol]['shares'] < shares:
            return False

        total_revenue = shares * price
        self.cash += total_revenue

        self.portfolio[symbol]['shares'] -= shares

        if self.portfolio[symbol]['shares'] == 0:
            del self.portfolio[symbol]

        # 거래 히스토리 저장
        self.trade_history.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': '매도',
            'symbol': symbol,
            'shares': shares,
            'price': price
        })

        return True

    def get_total_assets(self, stocks: Dict[str, Stock]) -> float:
        """총 자산 계산"""
        stock_value = sum(
            stocks[symbol].current_price * data['shares']
            for symbol, data in self.portfolio.items()
            if symbol in stocks
        )
        return self.cash + stock_value

    def get_profit_loss(self, stocks: Dict[str, Stock]) -> Tuple[float, float]:
        """수익금 및 수익률 계산"""
        total_assets = self.get_total_assets(stocks)
        profit = total_assets - self.initial_cash
        profit_percent = (profit / self.initial_cash) * 100
        return profit, profit_percent

    def get_portfolio_summary(self, stocks: Dict[str, Stock]) -> List[dict]:
        """포트폴리오 요약"""
        summary = []
        for symbol, data in self.portfolio.items():
            if symbol in stocks:
                current_price = stocks[symbol].current_price
                shares = data['shares']
                avg_price = data['avg_price']
                current_value = current_price * shares
                cost = avg_price * shares
                profit = current_value - cost
                profit_percent = (profit / cost * 100) if cost > 0 else 0

                summary.append({
                    'symbol': symbol,
                    'shares': shares,
                    'avg_price': avg_price,
                    'current_price': current_price,
                    'profit': profit,
                    'profit_percent': profit_percent
                })

        return summary


# ========== 7. GameEngine 클래스 ==========
class GameEngine:
    """게임 엔진 - 일별 진행 시스템"""

    def __init__(self, api: FinnhubAPI):
        self.api = api
        self.stocks = {}
        self.player = Player()
        self.market_news = MarketNews(api)
        self.current_time = GAME_START_DATE  # 게임 내 현재 시간
        self.tick_count = 0  # 진행된 틱 수
        self.leaderboard = []  # [(name, profit_percent), ...]

        # 초기 주식 로드
        for symbol in POPULAR_STOCKS:
            stock = Stock(symbol, api)
            # 초기 가격 히스토리에 게임 시작 시간 저장 (OHLC 형태)
            initial_ohlc = {
                'open': stock.current_price,
                'high': stock.current_price,
                'low': stock.current_price,
                'close': stock.current_price
            }
            stock.price_history = [(self.current_time, initial_ohlc)]
            self.stocks[symbol] = stock

    def next_tick(self):
        """다음 시간대로 진행 (3시간 후)"""
        self.tick_count += 1
        self.current_time += timedelta(hours=HOURS_PER_TICK)

        # 시장 마감 시간 이후면 다음 날 개장 시간으로
        if self.current_time.hour >= MARKET_CLOSE_HOUR:
            # 다음 날 개장 시간으로 설정
            next_day = self.current_time.date() + timedelta(days=1)
            self.current_time = datetime.combine(next_day, datetime.min.time()) + timedelta(hours=MARKET_OPEN_HOUR)

        # 모든 주식 가격 업데이트 (시뮬레이션)
        for stock in self.stocks.values():
            # 이전 종가를 시가로 사용
            open_price = stock.current_price

            # 랜덤 가격 변동 (-8% ~ +8%) - 변동성 증가
            change_percent = random.uniform(-8, 8)
            close_price = open_price * (1 + change_percent / 100)

            # 고가/저가 생성 (시가와 종가 사이에서 변동) - 변동폭 증가
            high_price = max(open_price, close_price) * random.uniform(1.0, 1.05)
            low_price = min(open_price, close_price) * random.uniform(0.95, 1.0)

            # 현재가 업데이트
            stock.current_price = close_price
            stock.daily_change = close_price - open_price
            stock.daily_change_percent = change_percent

            # OHLC 데이터 생성
            ohlc_data = {
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price
            }

            # 히스토리 저장 (게임 시간 사용)
            stock.price_history.append((self.current_time, ohlc_data))
            if len(stock.price_history) > 100:
                stock.price_history.pop(0)

            # 뉴스 임팩트 추가 적용 (30% 확률로 증가)
            if random.random() < 0.3:
                impact = self.market_news.calculate_news_impact(stock.symbol)
                stock.current_price *= (1 + impact / 100)

        # 랜덤 이벤트 (10% 확률로 증가)
        if random.random() < 0.1:
            self._trigger_random_event()

        # 게임 오버 체크 (자산이 초기 자금의 30% 이하)
        return self.check_game_over()

    def _trigger_random_event(self):
        """랜덤 이벤트 발생"""
        events = [
            "📈 시장 급등! 모든 주식 +5%",
            "📉 시장 급락! 모든 주식 -5%",
            "💡 기술주 강세! 기술주 +8%",
            "⚡ 실적 발표 시즌! 일부 주식 변동성 증가",
            "🚨 경제 위기! 모든 주식 -7%",
            "🎉 호재 발표! 모든 주식 +7%"
        ]

        event = random.choice(events)
        print(f"🎲 이벤트 발생: {event}")

        # 이벤트 효과 적용
        if "급등" in event:
            for stock in self.stocks.values():
                stock.current_price *= 1.05
        elif "급락" in event:
            for stock in self.stocks.values():
                stock.current_price *= 0.95
        elif "경제 위기" in event:
            for stock in self.stocks.values():
                stock.current_price *= 0.93
        elif "호재" in event:
            for stock in self.stocks.values():
                stock.current_price *= 1.07

    def check_game_over(self) -> bool:
        """게임 오버 체크 - 자산이 초기 자금의 30% 이하면 게임 종료"""
        total_assets = self.player.get_total_assets(self.stocks)
        threshold = self.player.initial_cash * 0.3

        if total_assets <= threshold:
            return True
        return False

    def save_game(self, filename: str = "savegame.json"):
        """게임 저장"""
        save_data = {
            'player': {
                'cash': self.player.cash,
                'initial_cash': self.player.initial_cash,
                'portfolio': self.player.portfolio,
                'trade_history': self.player.trade_history
            },
            'current_time': self.current_time.isoformat(),
            'tick_count': self.tick_count,
            'leaderboard': self.leaderboard
        }

        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)

        print(f"💾 게임이 저장되었습니다: {filename}")

    def load_game(self, filename: str = "savegame.json"):
        """게임 불러오기"""
        if not os.path.exists(filename):
            print("⚠️ 저장 파일이 없습니다.")
            return False

        try:
            with open(filename, 'r') as f:
                save_data = json.load(f)

            self.player.cash = save_data['player']['cash']
            self.player.initial_cash = save_data['player']['initial_cash']
            self.player.portfolio = save_data['player']['portfolio']
            self.player.trade_history = save_data['player']['trade_history']
            self.current_time = datetime.fromisoformat(save_data['current_time'])
            self.tick_count = save_data['tick_count']
            self.leaderboard = save_data.get('leaderboard', [])

            print(f"📂 게임을 불러왔습니다: {filename}")
            return True
        except Exception as e:
            print(f"❌ 불러오기 실패: {e}")
            return False


# ========== 8. StockTradingGUI 클래스 ==========
class StockTradingGUI:
    """tkinter GUI 클래스"""

    def __init__(self, root: tk.Tk, game_engine: GameEngine):
        self.root = root
        self.game = game_engine
        self.root.title("📈 실시간 주식 투자 시뮬레이션 (Finnhub)")
        self.root.geometry("1400x900")

        # 자동 업데이트 스레드
        self.running = True
        self.update_thread = None

        self.setup_ui()
        self.start_auto_update()

    def setup_ui(self):
        """UI 구성"""
        # 메인 컨테이너
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ===== 상단: 대시보드 =====
        dashboard_frame = ttk.LabelFrame(main_container, text="📊 대시보드", padding=10)
        dashboard_frame.pack(fill=tk.X, pady=(0, 10))

        self.dashboard_labels = {}
        dashboard_info = [
            ("총 자산", "total_assets"),
            ("현금", "cash"),
            ("투자금액", "invested"),
            ("수익금", "profit"),
            ("수익률", "profit_percent"),
            ("게임 시간", "game_time"),
            ("시장 분위기", "market_sentiment")
        ]

        for i, (label, key) in enumerate(dashboard_info):
            ttk.Label(dashboard_frame, text=f"{label}:").grid(row=0, column=i*2, padx=5, sticky=tk.W)
            value_label = ttk.Label(dashboard_frame, text="$0", font=('Arial', 10, 'bold'))
            value_label.grid(row=0, column=i*2+1, padx=5, sticky=tk.W)
            self.dashboard_labels[key] = value_label

        # ===== 중앙 컨테이너 =====
        center_container = ttk.Frame(main_container)
        center_container.pack(fill=tk.BOTH, expand=True)

        # 왼쪽: 주식 시세 + 거래
        left_frame = ttk.Frame(center_container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 주식 시세 패널
        stock_frame = ttk.LabelFrame(left_frame, text="💹 실시간 주가", padding=10)
        stock_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 주식 목록 테이블
        columns = ("종목", "현재가", "변동", "변동률", "추천")
        self.stock_tree = ttk.Treeview(stock_frame, columns=columns, show='headings', height=8)

        for col in columns:
            self.stock_tree.heading(col, text=col)
            self.stock_tree.column(col, width=100)

        self.stock_tree.pack(fill=tk.BOTH, expand=True)

        # 주식 목록 클릭 시 자동 선택
        self.stock_tree.bind('<<TreeviewSelect>>', self.on_stock_select)

        # 거래 패널
        trade_frame = ttk.LabelFrame(left_frame, text="💰 거래", padding=10)
        trade_frame.pack(fill=tk.X)

        ttk.Label(trade_frame, text="종목:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.symbol_var = tk.StringVar(value=POPULAR_STOCKS[0])
        symbol_combo = ttk.Combobox(trade_frame, textvariable=self.symbol_var,
                                     values=POPULAR_STOCKS, state='readonly', width=10)
        symbol_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(trade_frame, text="수량:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.shares_var = tk.StringVar(value="1")
        shares_entry = ttk.Entry(trade_frame, textvariable=self.shares_var, width=10)
        shares_entry.grid(row=0, column=3, padx=5, pady=5)

        self.trade_info_label = ttk.Label(trade_frame, text="예상 금액: $0", foreground="blue")
        self.trade_info_label.grid(row=0, column=4, padx=10, pady=5)

        ttk.Button(trade_frame, text="🟢 매수", command=self.buy_stock).grid(row=0, column=5, padx=5, pady=5)
        ttk.Button(trade_frame, text="🔴 매도", command=self.sell_stock).grid(row=0, column=6, padx=5, pady=5)
        ttk.Button(trade_frame, text="⏩ 3시간 후", command=self.next_tick).grid(row=0, column=7, padx=5, pady=5)

        # 수량 변경 시 예상 금액 업데이트
        self.shares_var.trace_add('write', lambda *args: self.update_trade_info())
        self.symbol_var.trace_add('write', lambda *args: (self.update_trade_info(), self.update_chart(self.symbol_var.get())))

        # 포트폴리오 패널
        portfolio_frame = ttk.LabelFrame(left_frame, text="🎯 내 포트폴리오", padding=10)
        portfolio_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        port_columns = ("종목", "수량", "평균단가", "현재가", "손익", "손익률")
        self.portfolio_tree = ttk.Treeview(portfolio_frame, columns=port_columns, show='headings', height=6)

        for col in port_columns:
            self.portfolio_tree.heading(col, text=col)
            self.portfolio_tree.column(col, width=90)

        self.portfolio_tree.pack(fill=tk.BOTH, expand=True)

        # 오른쪽: 그래프 + 뉴스 + 히스토리
        right_frame = ttk.Frame(center_container)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # 가격 차트
        chart_frame = ttk.LabelFrame(right_frame, text="📈 주가 차트", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # matplotlib 그래프 설정
        self.fig = Figure(figsize=(6, 3), dpi=80)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 뉴스 피드
        news_frame = ttk.LabelFrame(right_frame, text="📰 실시간 뉴스", padding=10)
        news_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.news_text = scrolledtext.ScrolledText(news_frame, wrap=tk.WORD, height=8,
                                                     font=('Arial', 9))
        self.news_text.pack(fill=tk.BOTH, expand=True)

        # 뉴스 새로고침 버튼
        ttk.Button(news_frame, text="🔄 뉴스 새로고침",
                  command=self.refresh_news).pack(pady=(5, 0))

        # 거래 히스토리
        history_frame = ttk.LabelFrame(right_frame, text="📜 거래 히스토리", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True)

        hist_columns = ("시간", "종목", "유형", "수량", "가격")
        self.history_tree = ttk.Treeview(history_frame, columns=hist_columns, show='headings', height=10)

        for col in hist_columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=90)

        self.history_tree.pack(fill=tk.BOTH, expand=True)

        # 메뉴바
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="파일", menu=file_menu)
        file_menu.add_command(label="저장", command=self.save_game)
        file_menu.add_command(label="불러오기", command=self.load_game)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.quit_app)

        # 초기 업데이트
        self.update_all()

    def update_all(self):
        """모든 UI 업데이트"""
        self.update_dashboard()
        self.update_stock_list()
        self.update_portfolio()
        self.update_history()
        self.update_trade_info()
        # 현재 선택된 종목의 차트 업데이트
        current_symbol = self.symbol_var.get()
        if current_symbol:
            self.update_chart(current_symbol)

    def update_dashboard(self):
        """대시보드 업데이트"""
        total_assets = self.game.player.get_total_assets(self.game.stocks)
        profit, profit_percent = self.game.player.get_profit_loss(self.game.stocks)
        invested = total_assets - self.game.player.cash

        self.dashboard_labels['total_assets'].config(text=f"${total_assets:,.2f}")
        self.dashboard_labels['cash'].config(text=f"${self.game.player.cash:,.2f}")
        self.dashboard_labels['invested'].config(text=f"${invested:,.2f}")

        profit_color = "green" if profit >= 0 else "red"
        self.dashboard_labels['profit'].config(text=f"${profit:,.2f}", foreground=profit_color)
        self.dashboard_labels['profit_percent'].config(
            text=f"{profit_percent:+.2f}%", foreground=profit_color)

        # 게임 시간 표시
        game_time_str = self.game.current_time.strftime('%Y-%m-%d %H:%M')
        self.dashboard_labels['game_time'].config(text=game_time_str)

        # 시장 분위기 (백그라운드로 실행)
        market_sentiment = self.game.market_news.get_market_sentiment()
        self.dashboard_labels['market_sentiment'].config(text=market_sentiment)

    def update_stock_list(self):
        """주식 목록 업데이트"""
        # 기존 항목 삭제
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)

        # 주식 추가
        for symbol, stock in self.game.stocks.items():
            change_color = "green" if stock.daily_change >= 0 else "red"
            recommendation = stock.get_recommendation_text()

            item = self.stock_tree.insert("", tk.END, values=(
                symbol,
                f"${stock.current_price:.2f}",
                f"${stock.daily_change:+.2f}",
                f"{stock.daily_change_percent:+.2f}%",
                recommendation
            ))

            # 색상 태그
            self.stock_tree.item(item, tags=(change_color,))

        self.stock_tree.tag_configure("green", foreground="green")
        self.stock_tree.tag_configure("red", foreground="red")

    def update_portfolio(self):
        """포트폴리오 업데이트"""
        for item in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(item)

        summary = self.game.player.get_portfolio_summary(self.game.stocks)

        for item_data in summary:
            profit_color = "green" if item_data['profit'] >= 0 else "red"

            tree_item = self.portfolio_tree.insert("", tk.END, values=(
                item_data['symbol'],
                item_data['shares'],
                f"${item_data['avg_price']:.2f}",
                f"${item_data['current_price']:.2f}",
                f"${item_data['profit']:+.2f}",
                f"{item_data['profit_percent']:+.2f}%"
            ))

            self.portfolio_tree.item(tree_item, tags=(profit_color,))

        self.portfolio_tree.tag_configure("green", foreground="green")
        self.portfolio_tree.tag_configure("red", foreground="red")

    def update_history(self):
        """거래 히스토리 업데이트"""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # 최근 20개만 표시
        for trade in self.game.player.trade_history[-20:]:
            self.history_tree.insert("", 0, values=(  # 0으로 최상단 삽입
                trade['timestamp'],
                trade['symbol'],
                trade['type'],
                trade['shares'],
                f"${trade['price']:.2f}"
            ))

    def update_trade_info(self, *args):
        """거래 예상 금액 업데이트"""
        try:
            symbol = self.symbol_var.get()
            shares = int(self.shares_var.get())

            if symbol in self.game.stocks:
                price = self.game.stocks[symbol].current_price
                total = price * shares
                self.trade_info_label.config(text=f"예상 금액: ${total:,.2f}")
        except ValueError:
            self.trade_info_label.config(text="수량을 입력하세요")

    def on_stock_select(self, event):
        """주식 목록에서 종목 선택 시 콤보박스에 반영"""
        selection = self.stock_tree.selection()
        if selection:
            item = self.stock_tree.item(selection[0])
            symbol = item['values'][0]  # 첫 번째 컬럼이 종목 심볼
            self.symbol_var.set(symbol)
            self.update_chart(symbol)

    def update_chart(self, symbol: str):
        """선택한 주식의 가격 차트 업데이트"""
        if symbol not in self.game.stocks:
            return

        stock = self.game.stocks[symbol]

        # 가격 히스토리가 충분하지 않으면 기본 차트 표시
        if len(stock.price_history) < 2:
            self.ax.clear()
            self.ax.text(0.5, 0.5, f'{symbol}\n데이터 수집 중...\n"다음 날"을 클릭하세요',
                        ha='center', va='center', fontsize=12)
            self.ax.set_xlim(0, 1)
            self.ax.set_ylim(0, 1)
            self.canvas.draw()
            return

        # 가격 데이터 추출
        times = []
        time_labels = []
        opens = []
        highs = []
        lows = []
        closes = []

        for idx, (t, data) in enumerate(stock.price_history):
            time_obj = t if isinstance(t, datetime) else datetime.fromtimestamp(t)
            times.append(idx)  # 인덱스 사용
            time_labels.append(time_obj.strftime('%m/%d\n%H:%M'))  # 표시용 레이블

            # OHLC 데이터 추출
            if isinstance(data, dict):
                opens.append(data['open'])
                highs.append(data['high'])
                lows.append(data['low'])
                closes.append(data['close'])
            else:
                # 구버전 데이터 호환성
                opens.append(data)
                highs.append(data)
                lows.append(data)
                closes.append(data)

        # 차트 그리기
        self.ax.clear()

        # 캔들스틱 차트 그리기
        from matplotlib.patches import Rectangle

        # 캔들 너비 (인덱스 기반이므로 0.8로 설정)
        candle_width = 0.8

        for i in range(len(times)):
            x = times[i]

            # 상승/하락 색상 결정
            if closes[i] >= opens[i]:
                color = 'red'  # 상승 (빨강)
                body_color = 'red'
            else:
                color = 'blue'  # 하락 (파랑)
                body_color = 'blue'

            # 고가-저가 선 (꼬리)
            self.ax.plot([x, x], [lows[i], highs[i]], color=color, linewidth=1.5)

            # 시가-종가 박스 (몸통)
            height = closes[i] - opens[i]

            # 시가와 종가가 거의 같으면 작은 박스로 표시
            if abs(height) < stock.current_price * 0.001:
                # 십자형태로 표시
                self.ax.plot([x - candle_width/2, x + candle_width/2], [opens[i], opens[i]],
                        color=color, linewidth=2)
            else:
                rect = Rectangle((x - candle_width/2, opens[i]), candle_width, height,
                            facecolor=body_color, edgecolor=body_color, alpha=0.9)
                self.ax.add_patch(rect)

        self.ax.set_title(f'{symbol} 주가 차트 (캔들스틱)', fontsize=12, fontweight='bold')
        self.ax.set_xlabel('시간 경과 (틱)', fontsize=9)
        self.ax.set_ylabel('가격 ($)', fontsize=9)
        self.ax.grid(True, alpha=0.3, linestyle='--')

        # X축 범위 조정 (캔들이 화면에 꽉 차도록)
        if len(times) > 0:
            self.ax.set_xlim(-0.5, len(times) - 0.5)

        # X축 눈금 설정
        if len(times) > 0:
            # 적절한 간격으로 눈금 표시
            if len(times) <= 10:
                tick_positions = times
                tick_labels = time_labels
            else:
                # 데이터가 많으면 간격을 띄워서 표시
                step = max(1, len(times) // 8)
                tick_positions = times[::step]
                tick_labels = time_labels[::step]

            self.ax.set_xticks(tick_positions)
            self.ax.set_xticklabels(tick_labels, fontsize=8)

        # 현재가 표시
        if closes:
            current_price = closes[-1]
            self.ax.axhline(y=current_price, color='green', linestyle='--', alpha=0.7, linewidth=1.5)

            # 현재가 텍스트를 차트 오른쪽에 표시
            if len(times) > 0:
                self.ax.text(len(times) - 0.5, current_price, f' ${current_price:.2f}',
                            fontsize=9, color='green', verticalalignment='bottom', fontweight='bold')

        self.fig.tight_layout()
        self.canvas.draw()

    def refresh_news(self):
        """뉴스 새로고침"""
        self.news_text.delete(1.0, tk.END)

        # 보유 종목 뉴스 우선
        symbols_to_check = list(self.game.player.portfolio.keys())[:3]  # 최대 3개

        if not symbols_to_check:
            symbols_to_check = [self.symbol_var.get()]

        for symbol in symbols_to_check:
            news_items = self.game.market_news.get_stock_news(symbol)

            if news_items:
                self.news_text.insert(tk.END, f"\n{'='*50}\n")
                self.news_text.insert(tk.END, f"📌 {symbol} 관련 뉴스\n")
                self.news_text.insert(tk.END, f"{'='*50}\n\n")

                for news in news_items[:5]:  # 최대 5개
                    sentiment_icon = {
                        'positive': '🟢',
                        'negative': '🔴',
                        'neutral': '🟡'
                    }.get(news['sentiment'], '⚪')

                    self.news_text.insert(tk.END, f"{sentiment_icon} {news['headline']}\n")
                    self.news_text.insert(tk.END, f"   {news['summary'][:100]}...\n")
                    self.news_text.insert(tk.END, f"   출처: {news['source']} | ", "gray")

                    news_time = datetime.fromtimestamp(news['datetime']).strftime('%Y-%m-%d %H:%M')
                    self.news_text.insert(tk.END, f"{news_time}\n\n", "gray")

        self.news_text.tag_config("gray", foreground="gray")

    def buy_stock(self):
        """주식 매수"""
        try:
            symbol = self.symbol_var.get()
            shares = int(self.shares_var.get())

            if shares <= 0:
                messagebox.showwarning("입력 오류", "수량은 1 이상이어야 합니다.")
                return

            if symbol in self.game.stocks:
                price = self.game.stocks[symbol].current_price

                if self.game.player.buy_stock(symbol, shares, price):
                    messagebox.showinfo("매수 성공",
                        f"{symbol} {shares}주를 ${price:.2f}에 매수했습니다.")
                    self.update_all()
                    # 매수 후에도 게임 오버 체크
                    self.check_game_over_status()
                else:
                    messagebox.showerror("매수 실패", "현금이 부족합니다.")
        except ValueError:
            messagebox.showwarning("입력 오류", "올바른 수량을 입력하세요.")

    def sell_stock(self):
        """주식 매도"""
        try:
            symbol = self.symbol_var.get()
            shares = int(self.shares_var.get())

            if shares <= 0:
                messagebox.showwarning("입력 오류", "수량은 1 이상이어야 합니다.")
                return

            if symbol in self.game.stocks:
                price = self.game.stocks[symbol].current_price

                if self.game.player.sell_stock(symbol, shares, price):
                    messagebox.showinfo("매도 성공",
                        f"{symbol} {shares}주를 ${price:.2f}에 매도했습니다.")
                    self.update_all()
                    # 매도 후에도 게임 오버 체크
                    self.check_game_over_status()
                else:
                    messagebox.showerror("매도 실패", "보유 수량이 부족합니다.")
        except ValueError:
            messagebox.showwarning("입력 오류", "올바른 수량을 입력하세요.")

    def check_game_over_status(self):
        """현재 자산 상태를 체크하여 게임 오버 여부 확인"""
        if self.game.check_game_over():
            total_assets = self.game.player.get_total_assets(self.game.stocks)
            initial_cash = self.game.player.initial_cash
            loss_percent = ((initial_cash - total_assets) / initial_cash) * 100

            messagebox.showerror("게임 오버!",
                f"💀 파산했습니다!\n\n"
                f"총 자산: ${total_assets:,.2f}\n"
                f"초기 자금: ${initial_cash:,.2f}\n"
                f"손실률: {loss_percent:.2f}%\n\n"
                f"자산이 초기 자금의 30% 이하로 떨어졌습니다.\n"
                f"게임을 종료합니다.")
            self.quit_app()

    def next_tick(self):
        """다음 시간대로 진행 (3시간 후)"""
        is_game_over = self.game.next_tick()
        current_time_str = self.game.current_time.strftime('%Y년 %m월 %d일 %H:%M')

        if is_game_over:
            total_assets = self.game.player.get_total_assets(self.game.stocks)
            initial_cash = self.game.player.initial_cash
            loss_percent = ((initial_cash - total_assets) / initial_cash) * 100

            messagebox.showerror("게임 오버!",
                f"💀 파산했습니다!\n\n"
                f"총 자산: ${total_assets:,.2f}\n"
                f"초기 자금: ${initial_cash:,.2f}\n"
                f"손실률: {loss_percent:.2f}%\n\n"
                f"자산이 초기 자금의 30% 이하로 떨어졌습니다.\n"
                f"게임을 종료합니다.")
            self.quit_app()
            return

        messagebox.showinfo("시간 경과", f"{current_time_str}로 진행되었습니다!")
        self.update_all()
        self.refresh_news()

    def save_game(self):
        """게임 저장"""
        self.game.save_game()
        messagebox.showinfo("저장 완료", "게임이 저장되었습니다.")

    def load_game(self):
        """게임 불러오기"""
        if self.game.load_game():
            messagebox.showinfo("불러오기 완료", "게임을 불러왔습니다.")
            self.update_all()
        else:
            messagebox.showerror("불러오기 실패", "저장 파일을 찾을 수 없습니다.")

    def start_auto_update(self):
        """자동 업데이트 시작 (30초마다)"""
        def auto_update():
            while self.running:
                time.sleep(30)
                if self.running:
                    # 주가만 업데이트 (UI는 메인 스레드에서)
                    for stock in self.game.stocks.values():
                        stock.update_price()

                    # UI 업데이트는 메인 스레드에서
                    self.root.after(0, self.update_stock_list)
                    self.root.after(0, self.update_portfolio)
                    self.root.after(0, self.update_dashboard)

        self.update_thread = threading.Thread(target=auto_update, daemon=True)
        self.update_thread.start()

    def quit_app(self):
        """앱 종료"""
        if messagebox.askyesno("종료", "게임을 종료하시겠습니까?"):
            self.running = False
            self.root.quit()


# ========== 9. 메인 실행 ==========
def main():
    """메인 함수"""
    # API 키 확인
    if FINNHUB_API_KEY == "YOUR_API_KEY_HERE":
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning("API 키 필요",
            "Finnhub API 키를 설정해주세요!\n\n"
            "1. https://finnhub.io/ 에서 무료 가입\n"
            "2. API Key 복사\n"
            "3. 코드 상단의 FINNHUB_API_KEY 변수에 붙여넣기\n\n"
            "현재는 시뮬레이션 모드로 실행됩니다.")
        root.destroy()

    # API 및 게임 엔진 초기화
    api = FinnhubAPI(FINNHUB_API_KEY)
    game_engine = GameEngine(api)

    # GUI 실행
    root = tk.Tk()
    app = StockTradingGUI(root, game_engine)

    # 시작 시 뉴스 로드
    root.after(1000, app.refresh_news)

    root.mainloop()


if __name__ == "__main__":
    main()
