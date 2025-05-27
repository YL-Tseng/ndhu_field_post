import requests
import json
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_captcha():
    """
    向指定的 URL 發送 GET 請求以獲取驗證碼。

    Returns:
        tuple: 包含 (imageBase64, captchaId) 的元組，如果成功。
               如果失敗，則回傳 (None, None)。
    """
    captcha_url = 'https://web.ndhu.edu.tw/INC/SysCaptcha/api/Captcha/Generate'
    headers = {
        'accept': '*/*',
        'accept-language': 'zh-TW,zh;q=0.9',
        'origin': 'https://sys.ndhu.edu.tw',
        'priority': 'u=1, i',
        'referer': 'https://sys.ndhu.edu.tw/',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
    }

    try:
        print(f"[*] 正在向 {captcha_url} 發送 GET 請求以獲取驗證碼...")
        response = requests.get(captcha_url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()  # 如果請求失敗 (狀態碼 4xx 或 5xx)，會拋出異常
        
        print(f"[*] GET 請求成功，狀態碼: {response.status_code}")
        
        data = response.json()
        
        if data.get("success"):
            image_base64 = data.get("imageBase64")
            captcha_id = data.get("captchaId")
            print(f"[*] 成功獲取驗證碼 ID: {captcha_id}")
            # print(f"[*] Base64 圖片資料 (前100字元): {image_base64[:100]}...")
            return image_base64, captcha_id
        else:
            print("[!] 獲取驗證碼失敗，伺服器回應 success: false。")
            print(f"    回應內容: {data}")
            return None, None

    except requests.exceptions.Timeout:
        print(f"[!] 請求超時: {captcha_url}")
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"[!] 請求過程中發生錯誤: {e}")
        return None, None
    except json.JSONDecodeError:
        print(f"[!] 解析 JSON 回應失敗。")
        print(f"    回應文字 (前200字元): {response.text[:200]}")
        return None, None
    except Exception as e:
        print(f"[!] 獲取驗證碼時發生未預期錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == '__main__':
    print("正在測試獲取驗證碼功能...")
    image_data, c_id = get_captcha()
    if image_data and c_id:
        print("\n[測試] 驗證碼獲取成功。")
        print(f"  Captcha ID: {c_id}")
        print(f"  Image Base64 (前50字元): {image_data[:50]}...")
        
        # 選擇性：將 base64 圖片儲存到檔案
        # import base64
        # try:
        #     if image_data.startswith('data:image/jpeg;base64,'):
        #         img_content = base64.b64decode(image_data.split(',')[1])
        #         with open("captcha_image.jpg", "wb") as f:
        #             f.write(img_content)
        #         print("[測試] 驗證碼圖片已儲存為 captcha_image.jpg")
        #     else:
        #         print("[測試] 圖片資料格式不正確，無法儲存。")
        # except Exception as e:
        #     print(f"[測試] 儲存圖片時發生錯誤: {e}")
            
    else:
        print("\n[測試] 驗證碼獲取失敗。")
