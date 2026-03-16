#!/usr/bin/env python3
"""
数据采集脚本 - 每天运行一次，生成静态 JSON 数据
"""
import os
import json
import requests
import yfinance as yf
from datetime import datetime
from pathlib import Path

# 配置 - 国内城市，国外数据源(Open-Meteo支持全球)
CITIES = [
    {"name": "武汉市", "lat": 30.5928, "lon": 114.3055},
    {"name": "东莞市", "lat": 23.0489, "lon": 113.7447},
    {"name": "河南省信阳市光山县", "lat": 32.0090, "lon": 114.9190},
]

# 全球指数
GLOBAL_INDICES = {
    "美国": [
        {"symbol": "^GSPC", "name": "标普500"},
        {"symbol": "^DJI", "name": "道琼斯"},
        {"symbol": "^IXIC", "name": "纳斯达克"},
    ],
    "欧洲": [
        {"symbol": "^FTSE", "name": "英国富时100"},
        {"symbol": "^GDAXI", "name": "德国DAX"},
        {"symbol": "^FCHI", "name": "法国CAC40"},
    ],
    "亚太": [
        {"symbol": "^N225", "name": "日经225"},
        {"symbol": "^HSI", "name": "恒生指数"},
    ],
}

# 市场板块
MARKET_SECTORS = {
    "股票": [
        {"symbol": "AAPL", "name": "苹果"},
        {"symbol": "MSFT", "name": "微软"},
        {"symbol": "GOOGL", "name": "谷歌"},
        {"symbol": "TSLA", "name": "特斯拉"},
    ],
    "宏观": [
        {"symbol": "GLD", "name": "黄金"},
        {"symbol": "USO", "name": "原油"},
        {"symbol": "UUP", "name": "美元指数"},
    ],
}

# 涨幅榜（示例热门股）
TOP_GAINERS = [
    {"symbol": "NVDA", "name": "英伟达"},
    {"symbol": "AMD", "name": "AMD"},
    {"symbol": "META", "name": "Meta"},
    {"symbol": "AMZN", "name": "亚马逊"},
    {"symbol": "NFLX", "name": "奈飞"},
]

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
OUTPUT_DIR = Path("site")
OUTPUT_DIR.mkdir(exist_ok=True)


def fetch_weather():
    """获取天气数据 - 使用 Open-Meteo (国外免费数据源)"""
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
            print(f"天气获取失败 {city['name']}: {e}")
    return weather_data


def fetch_stock_data(symbols_list):
    """获取股票数据"""
    result = []
    for item in symbols_list:
        try:
            ticker = yf.Ticker(item["symbol"])
            hist = ticker.history(period="5d")
            if len(hist) < 2:
                continue
                
            current = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2]
            change = (current - prev) / prev * 100
            
            result.append({
                "symbol": item["symbol"],
                "name": item["name"],
                "price": round(current, 2),
                "change": round(change, 2),
            })
        except Exception as e:
            print(f"股票获取失败 {item['symbol']}: {e}")
    return result


def fetch_news():
    """获取热点资讯"""
    if not NEWS_API_KEY:
        return {"error": "NEWS_API_KEY 未配置"}
    
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
        "date": datetime.now().strftime("%Y年%m月%d日"),
        "weather": fetch_weather(),
        "global_indices": {k: fetch_stock_data(v) for k, v in GLOBAL_INDICES.items()},
        "market_sectors": {k: fetch_stock_data(v) for k, v in MARKET_SECTORS.items()},
        "top_gainers": fetch_stock_data(TOP_GAINERS),
        "news": fetch_news(),
    }
    
    with open(OUTPUT_DIR / "data.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"报告已生成: {OUTPUT_DIR / 'data.json'}")
    return report


if __name__ == "__main__":
    generate_report()
