#!/usr/bin/env python3
"""
数据采集脚本 - 每日早报
"""
import os
import json
import requests
import yfinance as yf
from datetime import datetime
from pathlib import Path

# 配置
CITIES = [
    {"name": "武汉市", "lat": 30.5928, "lon": 114.3055},
    {"name": "东莞市", "lat": 23.0489, "lon": 113.7447},
    {"name": "河南省信阳市光山县", "lat": 32.0090, "lon": 114.9190},
]

# 全球指数 - 使用 ETF 代替部分指数，数据更稳定
GLOBAL_INDICES = {
    "美国": [
        {"symbol": "SPY", "name": "标普500"},
        {"symbol": "DIA", "name": "道琼斯"},
        {"symbol": "QQQ", "name": "纳斯达克100"},
    ],
    "欧洲": [
        {"symbol": "VGK", "name": "欧洲ETF"},
        {"symbol": "EWU", "name": "英国ETF"},
        {"symbol": "EWG", "name": "德国ETF"},
    ],
    "亚太": [
        {"symbol": "EWJ", "name": "日本ETF"},
        {"symbol": "EWH", "name": "香港ETF"},
        {"symbol": "ASHR", "name": "沪深300"},
    ],
}

MARKET_SECTORS = {
    "科技股": [
        {"symbol": "AAPL", "name": "苹果"},
        {"symbol": "MSFT", "name": "微软"},
        {"symbol": "GOOGL", "name": "谷歌"},
        {"symbol": "NVDA", "name": "英伟达"},
    ],
    "宏观": [
        {"symbol": "GLD", "name": "黄金"},
        {"symbol": "USO", "name": "原油"},
        {"symbol": "UUP", "name": "美元指数"},
    ],
}

# 涨幅榜扩大到 Top 10
TOP_GAINERS = [
    {"symbol": "NVDA", "name": "英伟达"},
    {"symbol": "AMD", "name": "AMD"},
    {"symbol": "META", "name": "Meta"},
    {"symbol": "AMZN", "name": "亚马逊"},
    {"symbol": "NFLX", "name": "奈飞"},
    {"symbol": "TSLA", "name": "特斯拉"},
    {"symbol": "CRM", "name": "Salesforce"},
    {"symbol": "UBER", "name": "Uber"},
    {"symbol": "COIN", "name": "Coinbase"},
    {"symbol": "PLTR", "name": "Palantir"},
]

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
                    "temp": round(data["current"]["temperature_2m"]),
                    "humidity": data["current"]["relative_humidity_2m"],
                },
                "today": {
                    "max": round(data["daily"]["temperature_2m_max"][0]),
                    "min": round(data["daily"]["temperature_2m_min"][0]),
                }
            })
        except Exception as e:
            print(f"天气获取失败 {city['name']}: {e}")
    return weather_data


def fetch_stock_with_history(item):
    """获取股票数据，包含近期走势"""
    try:
        ticker = yf.Ticker(item["symbol"])
        hist = ticker.history(period="6d")
        if len(hist) < 2:
            return None
        
        # 计算近5日涨跌幅用于迷你图
        prices = hist["Close"].tolist()
        current = prices[-1]
        prev = prices[-2]
        change = (current - prev) / prev * 100
        
        # 迷你图数据 (5日收盘价，归一化到0-100)
        min_p, max_p = min(prices), max(prices)
        if max_p > min_p:
            sparkline = [round((p - min_p) / (max_p - min_p) * 100) for p in prices]
        else:
            sparkline = [50] * len(prices)
        
        return {
            "symbol": item["symbol"],
            "name": item["name"],
            "price": round(current, 2),
            "change": round(change, 2),
            "sparkline": sparkline,
        }
    except Exception as e:
        print(f"股票获取失败 {item['symbol']}: {e}")
        return None


def fetch_stock_data(symbols_list):
    """获取股票列表数据"""
    result = []
    for item in symbols_list:
        data = fetch_stock_with_history(item)
        if data:
            result.append(data)
    return result


def fetch_news():
    """获取热点资讯"""
    articles = []
    
    # 尝试 NewsAPI
    if NEWS_API_KEY:
        try:
            url = f"https://newsapi.org/v2/top-headlines?category=business&language=zh&pageSize=10&apiKey={NEWS_API_KEY}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            for article in data.get("articles", [])[:8]:
                title = article.get("title", "")
                if len(title) > 60:
                    title = title[:57] + "..."
                articles.append({
                    "title": title,
                    "source": article.get("source", {}).get("name", ""),
                    "url": article.get("url", ""),
                    "published": article.get("publishedAt", "")[:10],
                })
            if articles:
                return {"articles": articles}
        except Exception as e:
            print(f"NewsAPI error: {e}")
    
    # 备用：HackerNews
    try:
        hn_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        top_ids = requests.get(hn_url, timeout=10).json()[:10]
        
        for story_id in top_ids:
            try:
                story = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=5).json()
                if story and story.get("title"):
                    title = story.get("title")
                    if len(title) > 70:
                        title = title[:67] + "..."
                    articles.append({
                        "title": title,
                        "source": "Hacker News",
                        "url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                        "published": datetime.fromtimestamp(story.get("time", 0)).strftime("%Y-%m-%d"),
                    })
            except:
                continue
        
        if articles:
            return {"articles": articles, "source": "Hacker News (备用)"}
    except Exception as e:
        print(f"HackerNews error: {e}")
    
    return {"error": "新闻获取失败"}


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
