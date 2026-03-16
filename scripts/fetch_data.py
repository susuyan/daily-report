#!/usr/bin/env python3
"""
数据采集脚本 - 每天运行一次，生成静态 JSON 数据
"""
import os
import json
import requests
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path

# 配置
CITIES = [
    {"name": "北京", "lat": 39.9042, "lon": 116.4074},
    {"name": "上海", "lat": 31.2304, "lon": 121.4737},
    {"name": "纽约", "lat": 40.7128, "lon": -74.0060},
]

STOCKS = {
    "全球指数": ["^GSPC", "^DJI", "^IXIC", "^FTSE", "^N225"],
    "加密货币": ["BTC-USD", "ETH-USD"],
    "ETF": ["QQQ", "SPY", "ARKK"],
}

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
OUTPUT_DIR = Path("site")
OUTPUT_DIR.mkdir(exist_ok=True)


def fetch_weather():
    """获取天气数据"""
    weather_data = []
    for city in CITIES:
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={city['lat']}&longitude={city['lon']}&current=temperature_2m,relative_humidity_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=auto"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            
            weather_data.append({
                "city": city["name"],
                "current": {
                    "temp": data["current"]["temperature_2m"],
                    "humidity": data["current"]["relative_humidity_2m"],
                },
                "today": {
                    "max": data["daily"]["temperature_2m_max"][0],
                    "min": data["daily"]["temperature_2m_min"][0],
                }
            })
        except Exception as e:
            print(f"Weather error for {city['name']}: {e}")
    return weather_data


def fetch_stocks():
    """获取股票数据"""
    result = {}
    for category, symbols in STOCKS.items():
        category_data = []
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")
                if len(hist) < 2:
                    continue
                    
                current = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2]
                change = (current - prev) / prev * 100
                
                category_data.append({
                    "symbol": symbol,
                    "name": ticker.info.get("shortName", symbol),
                    "price": round(current, 2),
                    "change": round(change, 2),
                })
            except Exception as e:
                print(f"Stock error for {symbol}: {e}")
        result[category] = category_data
    return result


def fetch_news():
    """获取新闻数据"""
    if not NEWS_API_KEY:
        return {"error": "NEWS_API_KEY not configured"}
    
    try:
        url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&pageSize=10&apiKey={NEWS_API_KEY}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        articles = []
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title", ""),
                "source": article.get("source", {}).get("name", ""),
                "url": article.get("url", ""),
                "published": article.get("publishedAt", "")[:10],
            })
        return {"articles": articles}
    except Exception as e:
        return {"error": str(e)}


def generate_report():
    """生成完整报告"""
    report = {
        "generated_at": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "weather": fetch_weather(),
        "markets": fetch_stocks(),
        "news": fetch_news(),
    }
    
    # 保存 JSON 数据
    with open(OUTPUT_DIR / "data.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"Report generated: {OUTPUT_DIR / 'data.json'}")
    return report


if __name__ == "__main__":
    generate_report()
