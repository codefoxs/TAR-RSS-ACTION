from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

options = Options()
options.add_argument("--headless")  # 必须：无界面模式
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)
driver.get("https://publications.aaahq.org/accounting-review/publish-ahead-of-print")

WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "div.al-article-items"))
)

html = driver.page_source

# 1. 读取 HTML
soup = BeautifulSoup(html, "lxml")

articles = soup.select("div.al-article-items")

# 2. 创建 RSS 结构
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")

BASE_URL = "https://publications.aaahq.org"
ET.SubElement(channel, "title").text = "The Accounting Review – Early Access"
ET.SubElement(channel, "link").text = BASE_URL + "/accounting-review/publish-ahead-of-print"
ET.SubElement(channel, "description").text = "Early access articles from The Accounting Review"
ET.SubElement(channel, "language").text = "en-us"
ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime(
    "%a, %d %b %Y %H:%M:%S GMT"
)

# 3. 逐篇文章写入 item
for art in articles:
    title_tag = art.select_one("h5.al-title a")
    if not title_tag:
        continue

    title = title_tag.get_text(strip=True)
    link = BASE_URL + title_tag["href"]

    # ✅ 作者（修正重点）
    authors_block = art.select_one(".al-authors-list")
    authors = authors_block.get_text(
        separator="", strip=True
    ) if authors_block else "Authors not listed"

    # 日期
    pub_date_tag = art.select_one(".al-pub-date")
    pub_date = pub_date_tag.get_text(strip=True) if pub_date_tag else ""

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = link
    ET.SubElement(item, "guid").text = link
    ET.SubElement(item, "description").text = (
        f"<b>Authors:</b> {authors}<br/>{pub_date}"
    )


# 4. 输出 rss.xml
tree = ET.ElementTree(rss)
tree.write("tar.xml", encoding="utf-8", xml_declaration=True)

print("✅ tar.xml 已生成")
