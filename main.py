import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import sys

def generate_rss():
    # 1. 从环境变量获取 API Key
    api_key = os.getenv("scraper_api")
    if not api_key:
        print("❌ 错误: 请在 GitHub Secrets 中配置 scraper_api")
        sys.exit(1)

    # 2. 准备请求参数
    # 如果后续发现抓不到文章，可以在 payload 增加 'render': 'true'
    target_url = "https://publications.aaahq.org/accounting-review/publish-ahead-of-print"
    payload = { 
        'api_key': api_key, 
        'url': target_url,
        'keep_headers': 'true' # 建议加上，让 ScraperAPI 更好地处理请求头
    }

    print(f"🚀 正在通过 ScraperAPI 请求: {target_url}")
    
    try:
        # 使用你提到的 api.scraperapi.com 接口
        r = requests.get('https://api.scraperapi.com/', params=payload, timeout=60)
        r.raise_for_status()
        html = r.text
        print("✅ 页面抓取成功!")
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        sys.exit(1)

    # 3. 解析 HTML
    soup = BeautifulSoup(html, "lxml")
    articles = soup.select("div.al-article-items")
    
    if not articles:
        print("⚠️ 未找到文章元素。")
        # 调试：看看是不是被拦截了
        if "captcha" in html.lower() or "robot" in html.lower():
            print("🛑 似乎遇到了验证码，可能需要增加 render: true 参数")
        return

    # 4. 创建 RSS 结构
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    BASE_URL = "https://publications.aaahq.org"
    ET.SubElement(channel, "title").text = "The Accounting Review – Early Access"
    ET.SubElement(channel, "link").text = target_url
    ET.SubElement(channel, "description").text = "Early access articles from The Accounting Review"
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    # 5. 逐篇文章写入 item
    count = 0
    for art in articles:
        title_tag = art.select_one("h5.al-title a")
        if not title_tag: continue

        title = title_tag.get_text(strip=True)
        link = BASE_URL + title_tag["href"] if title_tag["href"].startswith('/') else title_tag["href"]

        authors_block = art.select_one(".al-authors-list")
        authors = authors_block.get_text(separator="", strip=True) if authors_block else "Authors not listed"

        pub_date_tag = art.select_one(".al-pub-date")
        pub_date = pub_date_tag.get_text(strip=True) if pub_date_tag else ""

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid").text = link
        ET.SubElement(item, "description").text = f"<b>Authors:</b> {authors}<br/>{pub_date}"
        count += 1

    # 6. 输出 rss.xml
    tree = ET.ElementTree(rss)
    tree.write("tar.xml", encoding="utf-8", xml_declaration=True)
    print(f"🎉 完成! 已生成 {count} 篇文章")

if __name__ == "__main__":
    generate_rss()
