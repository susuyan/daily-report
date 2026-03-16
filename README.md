# Daily Report Dashboard

自动生成每日早报，部署在 GitHub Pages。

## 数据源
- 🌤️ 天气: Open-Meteo
- 📈 股票: Yahoo Finance (yfinance)
- 📰 新闻: NewsAPI / GNews

## 部署步骤

1. Fork 本仓库
2. 在 Settings → Secrets → Actions 中添加:
   - `NEWS_API_KEY` - 从 https://newsapi.org/ 获取 (免费)
3. 启用 GitHub Pages (Settings → Pages → Source: GitHub Actions)
4. 手动运行 workflow 测试

## 本地开发
```bash
pip install -r requirements.txt
python scripts/fetch_data.py
python -m http.server 8000
# 打开 http://localhost:8000
```
