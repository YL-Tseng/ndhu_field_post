import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import urllib3

# 載入 .env 檔案中的環境變數
load_dotenv()

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 從環境變數中讀取帳號和密碼
username = os.getenv('NDHU_USERNAME')
password = os.getenv('NDHU_PASSWORD')

# 檢查是否成功讀取到帳號密碼
if not username or not password:
    print("錯誤：請在 .env 檔案中設定 NDHU_USERNAME 和 NDHU_PASSWORD")
    exit()

# 1. 設定目標 URL
login_url = 'https://sys.ndhu.edu.tw/gc/sportcenter/SportsFields/login.aspx'

# 2. 建立 Session 物件
session = requests.Session()

# 3. 設定初始 Headers (模仿瀏覽器)
headers_get = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-TW,zh;q=0.9',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'upgrade-insecure-requests': '1',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'priority': 'u=0, i',
}

def perform_login():
    """執行登入流程並回傳 session 和登入後的回應。"""
    try:
        # 4. 發送 GET 請求到登入頁面以獲取表單參數和 Cookies
        print(f"[*] 發送 GET 請求到: {login_url}")
        get_request_headers = headers_get.copy()
        if 'cache-control' not in get_request_headers:
            get_request_headers['cache-control'] = 'max-age=0'

        response_get = session.get(login_url, headers=get_request_headers, timeout=15, verify=False)
        response_get.raise_for_status()
        print(f"[*] GET 請求成功，狀態碼: {response_get.status_code}")
        initial_cookies = response_get.cookies.get_dict()
        print(f"[*] 從 GET 請求獲取的初始 Cookies: {initial_cookies}")

        # 5. 解析 HTML 以提取動態表單欄位
        soup = BeautifulSoup(response_get.text, 'html.parser')

        viewstate_tag = soup.find('input', {'name': '__VIEWSTATE'})
        viewstategenerator_tag = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
        eventvalidation_tag = soup.find('input', {'name': '__EVENTVALIDATION'})
        requestverificationtoken_form_tag = soup.find('input', {'name': '__RequestVerificationToken'})
        viewstateencrypted_tag = soup.find('input', {'name': '__VIEWSTATEENCRYPTED'})

        required_tags = {
            "__VIEWSTATE": viewstate_tag,
            "__VIEWSTATEGENERATOR": viewstategenerator_tag,
            "__EVENTVALIDATION": eventvalidation_tag,
            "__RequestVerificationToken": requestverificationtoken_form_tag,
        }

        missing_tags = [name for name, tag in required_tags.items() if tag is None]
        if missing_tags:
            print(f"[!] 無法從登入頁面提取以下必要的表單欄位: {', '.join(missing_tags)}")
            return None, None

        payload = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': viewstate_tag['value'],
            '__VIEWSTATEGENERATOR': viewstategenerator_tag['value'],
            '__VIEWSTATEENCRYPTED': viewstateencrypted_tag['value'] if viewstateencrypted_tag else '',
            '__EVENTVALIDATION': eventvalidation_tag['value'],
            '__RequestVerificationToken': requestverificationtoken_form_tag['value'],
            'ctl00$MainContent$TxtUSERNO': username,
            'ctl00$MainContent$TxtPWD': password,
            'ctl00$MainContent$Button1': '登入'
        }

        payload_to_print = payload.copy()
        if 'ctl00$MainContent$TxtUSERNO' in payload_to_print:
            payload_to_print['ctl00$MainContent$TxtUSERNO'] = '******** (hidden)'
        if 'ctl00$MainContent$TxtPWD' in payload_to_print:
            payload_to_print['ctl00$MainContent$TxtPWD'] = '******** (hidden)'
        
        print("\n[*] 準備好的 Payload (帳密已隱藏):")
        for key, value in payload_to_print.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  {key}: {value[:80]}... (truncated, total length: {len(value)})")
            else:
                print(f"  {key}: {value}")
        print("-" * 30)

        # 6. 準備 POST 請求的 Headers
        headers_post = headers_get.copy()
        headers_post['content-type'] = 'application/x-www-form-urlencoded'
        headers_post['origin'] = 'https://sys.ndhu.edu.tw'
        headers_post['referer'] = login_url
        if 'cache-control' not in headers_post:
            headers_post['cache-control'] = 'max-age=0'

        # 7. 發送 POST 登入請求
        print(f"\n[*] 發送 POST 請求到: {login_url}")
        response_post = session.post(login_url, headers=headers_post, data=payload, timeout=15, allow_redirects=True, verify=False)
        print(f"[*] POST 請求完成")

        # 8. 處理回應
        print(f"[*] POST 請求後，最終 URL: {response_post.url}")
        print(f"[*] 最終狀態碼: {response_post.status_code}")

        if response_post.history:
            print("\n[*] 請求歷史:")
            for i, resp_hist in enumerate(response_post.history):
                print(f"  [{i}] Status: {resp_hist.status_code} {resp_hist.reason} - URL: {resp_hist.url}")
                if resp_hist.status_code == 302:
                    location = resp_hist.headers.get('Location')
                    print(f"      -> Redirected to: {location}")

        if response_post.status_code == 200:
            print("[*] 登入似乎成功。")
            print("\n[*] 重定向後頁面的內容 (前500字元):")
            print(response_post.text[:500])
            return session, response_post, initial_cookies
        elif response_post.status_code == 302 and not response_post.history:
            location = response_post.headers.get('Location')
            print(f"[*] 收到 302 Found (未自動重定向). 重定向目標: {location}")
            return session, response_post, initial_cookies # 仍然回傳，讓呼叫者決定如何處理
        else:
            print(f"[!] 登入可能失敗或發生未知情況。")
            print(f"    最終 URL: {response_post.url}")
            print(f"    最終狀態碼: {response_post.status_code}")
            print("\n[*] 回應內容 (前500字元):")
            print(response_post.text[:500])
            return None, response_post, initial_cookies

    except requests.exceptions.Timeout:
        print(f"[!] 請求超時: {login_url}")
        return None, None, None
    except requests.exceptions.RequestException as e:
        print(f"[!] 請求過程中發生錯誤: {e}")
        return None, None, None
    except Exception as e:
        print(f"[!] 發生未預期錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

if __name__ == '__main__':
    # 這個區塊可以用來測試 login_module.py 是否能獨立運作
    print("正在測試登入模組...")
    active_session, login_response = perform_login()
    if active_session and login_response:
        print("\n[測試] 登入模組測試成功。")
        # 你可以在這裡加入更多基於 login_response 的檢查
        # 例如，檢查 login_response.url 或 login_response.text 的特定內容
    else:
        print("\n[測試] 登入模組測試失敗。")
