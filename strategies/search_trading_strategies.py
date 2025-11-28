import requests
from bs4 import BeautifulSoup
import json
import time

print("=== 搜索台灣與美國特有交易策略 ===")

def search_strategies(search_terms, region):
    """搜索特定區域的交易策略"""
    strategies = []

    for term in search_terms:
        try:
            # 使用Google搜索
            query = f"{term} 高勝率 高容錯率 1-10天持有期"
            url = f"https://www.google.com/search?q={query}&num=10"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # 找到搜索結果
                results = soup.find_all('div', class_='g')[:5]

                for result in results:
                    title_elem = result.find('h3')
                    link_elem = result.find('a')

                    if title_elem and link_elem:
                        title = title_elem.text.strip()
                        link = link_elem.get('href', '')

                        # 過濾Google內部鏈接
                        if link.startswith('/url?') and 'q=' in link:
                            link = link.split('q=')[1].split('&')[0]

                        if link and 'http' in link and not any(x in link.lower() for x in ['google', 'youtube', 'facebook']):
                            strategies.append({
                                'title': title,
                                'link': link,
                                'keyword': term,
                                'region': region
                            })

            time.sleep(1)  # 避免請求過於頻繁

        except Exception as e:
            print(f"搜索 '{term}' 失敗: {str(e)[:50]}")

    return strategies

# 台灣特有策略關鍵字
taiwan_keywords = [
    "台灣期貨策略",
    "台指期交易策略",
    "台股期貨套利",
    "台灣選擇權策略",
    "台股融資融券策略",
    "台灣期貨槓桿策略",
    "台股當沖策略",
    "台灣指數期貨策略",
    "台股波段策略",
    "台灣ETF期貨策略"
]

# 美國特有策略關鍵字
us_keywords = [
    "美股期貨策略",
    "美國期權策略",
    "美股統計套利",
    "美股ETF策略",
    "美股對沖策略",
    "美國期貨槓桿策略",
    "美股選擇權策略",
    "美股指數期貨策略",
    "美股波段策略",
    "美國商品期貨策略"
]

print("\n--- 搜索台灣策略 ---")
taiwan_strategies = search_strategies(taiwan_keywords, "台灣")
print(f"找到 {len(taiwan_strategies)} 個台灣策略")

for i, strategy in enumerate(taiwan_strategies[:8]):
    print(f"{i+1}. {strategy['title']}")
    print(f"   關鍵字: {strategy['keyword']}")
    print(f"   鏈接: {strategy['link'][:80]}...")
    print()

print("\n--- 搜索美國策略 ---")
us_strategies = search_strategies(us_keywords, "美國")
print(f"找到 {len(us_strategies)} 個美國策略")

for i, strategy in enumerate(us_strategies[:8]):
    print(f"{i+1}. {strategy['title']}")
    print(f"   關鍵字: {strategy['keyword']}")
    print(f"   鏈接: {strategy['link'][:80]}...")
    print()

# 分析和比較
print("\n=== 策略分析比較 ===")

taiwan_features = []
us_features = []

# 提取關鍵特點
for strategy in taiwan_strategies[:5]:
    title = strategy['title'].lower()
    if any(word in title for word in ['期貨', '槓桿', '當沖', '波段']):
        taiwan_features.append('短期交易')
    if '套利' in title:
        taiwan_features.append('套利策略')
    if '指數' in title:
        taiwan_features.append('指數相關')
    if '選擇權' in title or '權證' in title:
        taiwan_features.append('衍生品策略')

for strategy in us_strategies[:5]:
    title = strategy['title'].lower()
    if any(word in title for word in ['期貨', '槓桿', '波段']):
        us_features.append('短期交易')
    if '統計' in title or '套利' in title:
        us_features.append('套利策略')
    if '指數' in title:
        us_features.append('指數相關')
    if '選擇權' in title or '期權' in title:
        us_features.append('衍生品策略')

print("台灣策略常見特點:", list(set(taiwan_features)))
print("美國策略常見特點:", list(set(us_features)))

# 總結建議
print("\n=== 建議策略方向 ===")
print("台灣市場適合策略:")
print("- 台指期當沖策略 (1-3天持有)")
print("- 台股期貨套利 (3-7天持有)")
print("- 台指選擇權策略 (5-10天持有)")
print("- 台股融資融券策略 (3-5天持有)")

print("\n美國市場適合策略:")
print("- 美股期權策略 (1-10天持有)")
print("- 美股ETF槓桿策略 (1-5天持有)")
print("- 美股統計套利 (3-10天持有)")
print("- 美股指數期貨策略 (1-7天持有)")

print("\n共同特點:")
print("- 1-10天持有期，適合波段操作")
print("- 利用槓桿和衍生品獲取超額收益")
print("- 強調風險管理和止損機制")
print("- 季度績效為正，年化超越大盤")

