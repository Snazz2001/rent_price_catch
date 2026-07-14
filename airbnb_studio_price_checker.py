#!/usr/bin/env python3
"""
Airbnb Studio 价格查询工具 — MAG 318, Business Bay, Dubai

用法:
    pip install playwright --break-system-packages
    playwright install chromium
    python airbnb_studio_price_checker.py --checkin 2026-08-01 --checkout 2026-08-07

可选参数:
    --building   要搜索的楼盘/地区关键词 (默认: "MAG 318, Business Bay, Dubai, United Arab Emirates")
    --keyword    用于从结果中筛选"户型"的标题关键词 (默认: "studio")
    --adults     入住人数 (默认: 1)
    --headless   True/False，是否隐藏浏览器窗口 (默认: True)
    --csv        输出的 CSV 文件路径 (默认: airbnb_studio_prices.csv)

原理说明:
    Airbnb 搜索结果页不会在页面文本中直接暴露"每日价格"，只会给出
    "整个入住区间的总价"（这是官方前端为了避免逐日爬取而做的设计）。
    所以本脚本抓取的是每个房源的【总价】和【总晚数】，然后计算出
    "平均每晚价格" = 总价 / 晚数。
    如果你要精确到某一天的真实浮动价格（旺季/周末溢价等），
    需要针对单个房源打开预订日历逐日查看，Airbnb 官方 App/网页也是如此。
"""

import argparse
import csv
import re
import sys
from datetime import datetime
from urllib.parse import quote

from playwright.sync_api import sync_playwright


def build_search_url(building: str, checkin: str, checkout: str, adults: int) -> str:
    """构造 Airbnb 搜索 URL（用 query 参数而不是拼 slug，更稳定）。"""
    query = quote(building)
    url = (
        "https://www.airbnb.ae/s/homes"
        f"?query={query}"
        f"&checkin={checkin}"
        f"&checkout={checkout}"
        f"&adults={adults}"
        "&room_types%5B%5D=Entire%20home%2Fapt"
    )
    return url


def parse_price_label(label: str):
    """
    解析 Airbnb 的价格 aria-label，例如：
      "ﺩ.ﺇ 1,500 for 6 nights, originally ﺩ.ﺇ 1,701"
      "ﺩ.ﺇ 1,364 for 6 nights"
    返回 (当前总价: float, 晚数: int) 或 None
    """
    m = re.search(r"([\d,]+)\s*for\s*(\d+)\s*night", label, re.IGNORECASE)
    if not m:
        return None
    price = float(m.group(1).replace(",", ""))
    nights = int(m.group(2))
    return price, nights


def extract_title_from_card_text(card_text: str) -> str:
    """
    从卡片的纯文本里用启发式规则挑出房源标题。
    Airbnb 卡片文本大致顺序为：
      [徽章: Superhost/Guest favorite/New]
      "Apartment in XXX"        <- 物业类型+区域，不是标题
      "真正的房源标题"           <- 我们要的
      "4.9x out of 5 average rating, N reviews"
      "N bedroom", "N bed", "N bath"
      "AED x,xxx for N nights..."
      "Free cancellation" / "Pay AED 0 today" 等
    """
    noise_patterns = [
        r"^Superhost$", r"^Guest favorite$", r"^New$", r"^New place to stay$",
        r"^Top guest favorite$",
        r"out of 5 average rating",
        r"^\d+(\.\d+)?\s*\(\d+\)$",
        r"bedroom", r"^\d+\s*bed$", r"bath",
        r"for\s*\d+\s*nights?",
        r"^Pay\s", r"cancellation", r"discount", r"Show price breakdown",
        r"^Apartment in ", r"^Loft in ", r"^Condo in ", r"^Home in ",
        r"^·$", r"^,$",
    ]
    lines = [ln.strip() for ln in card_text.split("\n") if ln.strip()]
    for ln in lines:
        if any(re.search(p, ln, re.IGNORECASE) for p in noise_patterns):
            continue
        # 标题通常长度适中且不是纯数字/符号
        if len(ln) > 3 and not ln.replace(",", "").replace(".", "").isdigit():
            return ln
    return lines[0] if lines else "(未知标题)"


def scrape_listings(page, keyword: str):
    """抓取当前搜索结果页的所有房源，返回 list[dict]。"""
    page.wait_for_selector('[data-testid="card-container"]', timeout=20000)
    cards = page.query_selector_all('[data-testid="card-container"]')

    results = []
    for card in cards:
        # 找价格 aria-label（Airbnb 给屏幕阅读器用的完整价格文案，比可见文本更稳定）
        price_el = card.query_selector('[aria-label*="for"][aria-label*="night"]')
        if not price_el:
            continue
        label = price_el.get_attribute("aria-label") or ""
        parsed = parse_price_label(label)
        if not parsed:
            continue
        total_price, nights = parsed

        title = extract_title_from_card_text(card.inner_text())

        link_el = card.query_selector('a[href*="/rooms/"]')
        href = link_el.get_attribute("href") if link_el else None
        url = f"https://www.airbnb.ae{href}" if href and href.startswith("/") else href

        if keyword.lower() not in title.lower():
            continue

        results.append({
            "title": title,
            "total_price_aed": total_price,
            "nights": nights,
            "avg_nightly_aed": round(total_price / nights, 2) if nights else None,
            "url": url,
        })

    # 按 URL 去重（同一房源可能因为"更多相似日期"版块重复出现）
    seen = set()
    unique_results = []
    for r in results:
        key = r["url"] or r["title"]
        if key not in seen:
            seen.add(key)
            unique_results.append(r)
    return unique_results


def print_table(results, checkin, checkout):
    if not results:
        print("没有找到匹配的房源，请检查日期/关键词，或 Airbnb 页面结构是否变化。")
        return

    results = sorted(results, key=lambda r: r["avg_nightly_aed"])

    print(f"\n查询条件: MAG 318, Business Bay, Dubai | {checkin} → {checkout} | Studio\n")
    print(f"{'房源名称':<55} {'总价(AED)':>12} {'晚数':>6} {'均价/晚(AED)':>14}")
    print("-" * 90)
    for r in results:
        print(f"{r['title'][:53]:<55} {r['total_price_aed']:>12,.0f} {r['nights']:>6} {r['avg_nightly_aed']:>14,.0f}")
    print("-" * 90)
    avg_all = sum(r["avg_nightly_aed"] for r in results) / len(results)
    print(f"{'平均值 (所有房源)':<55} {'':>12} {'':>6} {avg_all:>14,.0f}")


def save_csv(results, path):
    if not results:
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "total_price_aed", "nights", "avg_nightly_aed", "url"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\n已保存 CSV: {path}")


def main():
    parser = argparse.ArgumentParser(description="Airbnb Studio 价格查询 - MAG 318 Business Bay Dubai")
    parser.add_argument("--checkin", required=True, help="入住日期 YYYY-MM-DD")
    parser.add_argument("--checkout", required=True, help="退房日期 YYYY-MM-DD")
    parser.add_argument("--building", default="MAG 318, Business Bay, Dubai, United Arab Emirates")
    parser.add_argument("--keyword", default="studio", help="标题筛选关键词，默认 studio")
    parser.add_argument("--adults", type=int, default=1)
    parser.add_argument("--headless", type=lambda x: x.lower() != "false", default=True)
    parser.add_argument("--csv", default="airbnb_studio_prices.csv")
    args = parser.parse_args()

    # 校验日期
    try:
        d1 = datetime.strptime(args.checkin, "%Y-%m-%d")
        d2 = datetime.strptime(args.checkout, "%Y-%m-%d")
        if d2 <= d1:
            print("错误: checkout 必须晚于 checkin")
            sys.exit(1)
    except ValueError:
        print("错误: 日期格式应为 YYYY-MM-DD")
        sys.exit(1)

    url = build_search_url(args.building, args.checkin, args.checkout, args.adults)
    print(f"正在打开: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)  # 等待动态内容加载

        results = scrape_listings(page, args.keyword)
        browser.close()

    print_table(results, args.checkin, args.checkout)
    save_csv(results, args.csv)


if __name__ == "__main__":
    main()
