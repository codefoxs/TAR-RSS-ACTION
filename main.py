import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import time
import sys

# 1. 配置 undetected_chromedriver
options = uc.ChromeOptions()
options.add_argument("--headless")  # GitHub Actions 必须开启 headless
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

# 注意：uc 内部会自动生成合适的 User-Agent，通常不需要手动加 fake-useragent
# 但如果想更稳妥，可以保留这行，但 uc 默认的已经很强了
# options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

try:
    print("🚀 正在启动 undetected_chromedriver...")
    driver = uc.Chrome(options=options)
    
    print("🌐 正在访问页面...")
    driver.get("https://publications.aaahq.org/accounting-review/publish-ahead-of-print")

    # 模拟人类随机等待 3-5 秒，让页面脚本运行
    time.sleep(5)

    print("⏳ 等待页面元素加载...")
    # 增加到 30 秒超时，并在失败时捕获错误
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.al-article-items")))

    html = driver.page_source
    print("✅ 页面加载成功，开始解析...")

except Exception as e:
    print(f"❌ 运行出错: {e}")
    # 调试关键：报错时打印页面标题，看是否被拦截（如显示 403 Forbidden）
    if 'driver' in locals():
        print(f"当前页面标题: {driver.title}")
        # 如果被拦截，可以保存源码查看原因
        # with open("error_debug.html", "w", encoding="utf-8") as f:
        #     f.write(driver.page_source)
    sys.exit(1)

# --- 以下逻辑保持不变 ---

soup = BeautifulSoup(html, "lxml")
articles = soup.select("div.al-article-items")

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

for art in articles:
    title_tag = art.select_one("h5.al-title a")
    if not title_tag:
        continue

    title = title_tag.get_text(strip=True)
    link = BASE_URL + title_tag["href"]

    authors_block = art.select_one(".al-authors-list")
    authors = authors_block.get_text(
        separator="", strip=True
    ) if authors_block else "Authors not listed"

    pub_date_tag = art.select_one(".al-pub-date")
    pub_date = pub_date_tag.get_text(strip=True) if pub_date_tag else ""

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = link
    ET.SubElement(item, "guid").text = link
    ET.SubElement(item, "description").text = (
        f"<b>Authors:</b> {authors}<br/>{pub_date}"
    )

tree = ET.ElementTree(rss)
tree.write("tar.xml", encoding="utf-8", xml_declaration=True)

driver.quit()
print("🎉 tar.xml 已成功生成")
