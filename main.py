import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import sys

def generate_rss():
    # 1. 从环境变量获取 API Key (安全第一)
    api_key = os.getenv("SCRAPERAPI_KEY")
    if not api_key:
        print("❌ 错误: 请在 GitHub Secrets 中配置 SCRAPERAPI_KEY")
        sys.exit(1)

    target_url = "https://publications.aaahq.org/accounting-review/publish-ahead-of-print"
    
    # 2. 构建 ScraperAPI 代理参数
    # render=true 表示让 ScraperAPI 帮我们运行 JS（类似 Selenium 的效果）
    proxy_url = "http://scraperapi:{}@proxy-server.scraperapi.com:8001".format(api_key)
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }

    print(f"🚀 正在通过 ScraperAPI 请求页面: {target_url}")
    
    try:
        # 即使目标站是 HTTPS，通过代理请求时通常建议 verify=False 或使用其提供的 CA
        response = requests.get(target_url, proxies=proxies, verify=False, timeout=60)
        response.raise_for_status()
        html = response.text
        print("✅ 页面抓取成功!")
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        sys.exit(1)

    # 3. 解析 HTML
    soup = BeautifulSoup(html, "lxml")
    articles = soup.select("div.al-article-items")
    
    if not articles:
        print("⚠️ 未找到文章元素，可能是页面结构变化或被拦截。")
        # 打印部分源码以便在 Action 日志中排查
        print(html[:500])
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
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        link = BASE_URL + title_tag["href"]

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
    print(f"🎉 完成! 已生成包含 {count} 篇文章的 tar.xml")

if __name__ == "__main__":
    generate_rss()
