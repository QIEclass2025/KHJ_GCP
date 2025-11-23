# 📈 Stock Trading Simulator: Parallel 2024

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-blue?style=for-the-badge)
![yfinance](https://img.shields.io/badge/yfinance-Data-green?style=for-the-badge)

## 📖 프로젝트 소개 (Introduction)
이 프로젝트는 **2024년의 실제 주식 시장 데이터**를 기반으로 하되, 예측 불가능한 **무작위성(Randomness)**과 **시장 편향(Market Bias)**을 더한 주식 투자 시뮬레이션 게임입니다.

플레이어는 애플(AAPL), 엔비디아(NVDA) 같은 실제 우량주뿐만 아니라, 변동성이 극심한 **개잡주 주식(NUBURU)**을 거래하며 2024년 1월 1일부터 12월 31일까지 최고의 수익률을 달성해야 합니다.

## ✨ 주요 기능 (Key Features)

### 1. 평행 우주 엔진 (Parallel Universe Engine)
단순히 과거 데이터를 따라가는 것이 아니라, 실제 데이터에 **고유 위험(Idiosyncratic Risk)**과 **체계적 위험(Systemic Risk)**을 혼합하여 매번 다른 시장 상황을 연출합니다. 
- **수식:** $Price_{new} = Price_{old} \times (1 + \text{Real\%} + \text{MarketBias} + \text{Noise})$
- **시장 국면:** 랜덤하게 **폭락장(Crash)**, **약세장(Bear)**, **강세장(Bull)** 이벤트가 발생하며 뉴스 피드를 통해 알려줍니다.

### 2. 개잡주 주식 알고리즘 (Synthetic Meme Stock)
- **NUBURU:** 개발자의 실제 애착 주식으로. 개잡주의 특성을 명확하게 보여주는 주식입니다.
- **Pump & Dump:** 1%의 확률로 30~100% 폭등하거나 반대로 폭락하는 초고위험 자산 시뮬레이션을 구현했습니다.

### 3. 현대적인 UI/UX (Modern Dark Mode)
- **Toss Securities Style:** 복잡한 HTS 대신, 모바일 핀테크 앱(토스 증권)에서 영감을 받은 직관적인 **Dark Mode UI**를 적용했습니다.
- **Responsive Charts:** `matplotlib`을 커스터마이징하여 배경색과 융화되는 세련된 차트를 제공합니다.
- **Dynamic Dashboard:** 실시간 자산 변동, 수익률에 따른 색상 변화(Red/Blue)를 지원합니다.

### 4. 뉴스 및 티어 시스템 (News & Ranking)
- **AI Market Watch:** 주가 변동폭에 따라 긍정/부정/중립 뉴스를 자동으로 생성합니다.
- **Game Result:** 최종 수익률에 따라 '워렌 버핏'부터 '주린이'까지 다양한 등급(Tier)이 매겨집니다. (최악의 플레이를 하시면 이스터에그를 발견하실 수 있을겁니다!)

## 🛠 기술 스택 (Tech Stack)
- **Language:** Python 3.10+
- **GUI Framework:** Tkinter (Standard Library)
- **Data Analysis:** pandas, yfinance
- **Visualization:** matplotlib

## 🚀 설치 및 실행 (Installation & Usage)

이 프로젝트는 `uv` 패키지 매니저를 사용하여 환경을 구축할 수 있습니다. (또는 pip 사용 가능)

### 1. 환경 설정
```bash
# 저장소 클론
git clone [Repository URL]
cd [Repository Name]

# 의존성 설치 (uv 사용 시)
uv sync

# 의존성 설치 (pip 사용 시)
pip install matplotlib yfinance pandas

##게임 방법(How to play)
초기 자본 $100000으로 시작합니다
매수/ 매도: 원하는 종목을 선택하고 수량을 입력하여 거래합니다.
턴 진행 : 1Days, 3Days 1Week 버튼을 눌러 시간을 진행시킵니다
뉴스 확인 : 우측 하단의 뉴스 피트를 통해 시장의 분위기와 급등/ 급락 사유를 파악하세요.
엔딩 : 데이터가 끝나는 2024년 12월 31일이 되면 최종 수익률에 따라서 평가를 받습니다.
