import os
import re
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://cis.ncu.edu.tw"
INDEX_URL = f"{BASE_URL}/iNCU/publicService/activityQuery"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def main():
    # 建立以日期命名的歷史資料夾，如：backups/2026/08/2026-08-18
    today = datetime.utcnow().strftime("%Y-%m-%d")
    year_month = datetime.utcnow().strftime("%Y/%m")
    backup_dir = os.path.join("backups", year_month, today)
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs("backups", exist_ok=True)

    print(f"正在抓取活動清單首頁: {INDEX_URL}")
    response = requests.get(INDEX_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    index_html = response.text

    # 1. 儲存首頁歷史檔與 latest.html
    index_file = os.path.join(backup_dir, "index.html")
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(index_html)
    with open("backups/latest.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    # 2. 解析首頁內所有的活動詳細頁面連結 (例如 /iNCU/publicService/activityQuery/1962)
    soup = BeautifulSoup(index_html, "html.parser")
    activity_ids = set()
    
    # 比對所有包含 activityQuery/數字 的 href
    for a in soup.find_all("a", href=True):
        match = re.search(r"activityQuery/(\d+)", a["href"])
        if match:
            activity_ids.add(match.group(1))

    print(f"找到 {len(activity_ids)} 個活動詳細頁面: {sorted(list(activity_ids))}")

    # 3. 逐一下載各活動詳細頁面
    details_dir = os.path.join(backup_dir, "activities")
    os.makedirs(details_dir, exist_ok=True)

    for act_id in sorted(activity_ids):
        act_url = f"{INDEX_URL}/{act_id}"
        print(f"正在備份活動 #{act_id} -> {act_url}")
        try:
            act_res = requests.get(act_url, headers=HEADERS, timeout=20)
            if act_res.status_code == 200:
                with open(os.path.join(details_dir, f"{act_id}.html"), "w", encoding="utf-8") as f:
                    f.write(act_res.text)
            else:
                print(f"無法下載 #{act_id}，狀態碼: {act_res.status_code}")
        except Exception as e:
            print(f"下載 #{act_id} 失敗: {e}")
        
        # 禮貌性延遲，避免對目標伺服器造成過大負擔
        time.sleep(0.5)

    print("備份完成！")

if __name__ == "__main__":
    main()
