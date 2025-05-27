import os
import json
from dotenv import load_dotenv
from openai import OpenAI, APIError, APITimeoutError, APIConnectionError

# 載入 .env 檔案中的環境變數
load_dotenv()

# 從環境變數中讀取 API 金鑰
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# ------------------------------------------------------------------------------
# OCR 系統提示 (可在此修改)
# ------------------------------------------------------------------------------
SYSTEM_PROMPT_FOR_OCR = """你是一個圖片文字辨識工具，將接收傳進來的base64，並且取出裡面的文字，不會有任何空格，以json格式回覆：
{
"respond": "text_from_image_recognition"
}"""
# ------------------------------------------------------------------------------

# 檢查 API 金鑰是否存在
if not GEMINI_API_KEY:
    print("錯誤：請在 .env 檔案中設定 GEMINI_API_KEY")

# 初始化 OpenAI client
# 如果 GEMINI_API_KEY 未設定，client 仍然會被初始化，但在呼叫時會失敗
client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

def get_text_from_image_gemini(base64_image_data: str,
                               model_name: str = "gemini-2.5-flash-preview-05-20"):
    """
    使用 Gemini API (透過 OpenAI 函式庫) 從 Base64 圖片資料中提取文字。

    Args:
        base64_image_data (str): Base64 編碼的圖片資料 (包含 data URI 前綴，例如 "data:image/jpeg;base64,...").
        model_name (str, optional): 要使用的模型名稱。
                                    預設為 "gemini-2.5-flash-preview-05-20"。
                                    注意：此模型可能需要支援視覺輸入。

    Returns:
        str: 辨識出的文字，如果成功。
             如果失敗或 AI 回應格式不符，則回傳 None。
    """
    if not GEMINI_API_KEY:
        print("[!] Gemini API 金鑰未設定。請檢查 .env 檔案。")
        return None

    if not base64_image_data:
        print("[!] 未提供 Base64 圖片資料。")
        return None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_FOR_OCR},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "請辨識這張圖片中的文字，並嚴格按照系統提示的JSON格式回覆。"},
                {
                    "type": "image_url",
                    "image_url": {"url": base64_image_data} # Base64 data URI
                },
            ],
        },
    ]

    try:
        print(f"[*] 正在使用 OpenAI 函式庫向 Gemini API (模型: {model_name}) 發送圖片辨識請求...")
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            # max_tokens=150 # 根據需要調整，確保 JSON 回應完整
        )
        
        print(f"[*] API 請求成功。")
        
        if response.choices and len(response.choices) > 0:
            ai_message = response.choices[0].message
            if ai_message and ai_message.content:
                ai_response_content = ai_message.content
                print(f"[*] AI 原始回覆內容: {ai_response_content}")
                try:
                    # 嘗試解析 AI 回應的 JSON
                    # Gemini 可能會在 JSON 外面包裝 ```json ... ```，需要移除
                    cleaned_content = ai_response_content.strip()
                    if cleaned_content.startswith("```json"):
                        cleaned_content = cleaned_content[len("```json"):].strip()
                    if cleaned_content.endswith("```"):
                        cleaned_content = cleaned_content[:-len("```")].strip()
                    
                    parsed_json = json.loads(cleaned_content)
                    extracted_text = parsed_json.get("respond")
                    if extracted_text is not None:
                        return extracted_text
                    else:
                        print("[!] AI 回應的 JSON 中未找到 'respond' 欄位。")
                        print(f"    解析後的 JSON: {parsed_json}")
                        return None
                except json.JSONDecodeError:
                    print("[!] AI 回應不是有效的 JSON 格式，或清理後仍無法解析。")
                    print(f"    清理前的 AI 回應內容: {ai_response_content}")
                    return None
            else:
                print("[!] API 回應中未找到有效的訊息內容。")
                print(f"    完整回應: {response}")
                return None
        else:
            print("[!] API 回應中未找到 'choices'。")
            print(f"    完整回應: {response}")
            return None

    except APITimeoutError:
        print(f"[!] 請求超時。")
        return None
    except APIConnectionError as conn_err:
        print(f"[!] 連線錯誤: {conn_err}")
        return None
    except APIError as api_err:
        print(f"[!] Gemini API 錯誤 (狀態碼: {api_err.status_code if hasattr(api_err, 'status_code') else 'N/A'})")
        error_body = api_err.body if hasattr(api_err, 'body') else {}
        error_message = error_body.get('error', {}).get('message', str(api_err)) if isinstance(error_body, dict) else str(api_err)
        print(f"    錯誤訊息: {error_message}")
        # print(f"    完整錯誤物件: {api_err}")
        return None
    except Exception as e:
        print(f"[!] 呼叫 Gemini API 進行圖片辨識時發生未預期錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    print("正在測試使用 Gemini API 進行圖片文字辨識功能...")
    
    if not GEMINI_API_KEY:
        print("無法進行測試，因為 GEMINI_API_KEY 未在 .env 中設定。")
    else:
        # 為了測試，我們需要 captcha_service.py 中的 get_captcha
        # 這假設 captcha_service.py 與此檔案在同一目錄或 Python PATH 中
        try:
            from captcha_service import get_captcha
            print("\n[*] 正在從 captcha_service 獲取測試驗證碼圖片...")
            captcha_b64_data, captcha_id = get_captcha()

            if captcha_b64_data and captcha_id:
                print(f"[*] 成功獲取驗證碼圖片 (ID: {captcha_id})。")
                # print(f"    Base64 圖片資料 (前60字元): {captcha_b64_data[:60]}...")
                
                print("\n[*] 正在使用 Gemini API 進行文字辨識...")
                extracted_text = get_text_from_image_gemini(captcha_b64_data)
                
                if extracted_text is not None: # 即使是空字串也算成功
                    print("\n[測試] Gemini API 文字辨識完成。")
                    print(f"  辨識出的文字: \"{extracted_text}\"")
                else:
                    print("\n[測試] Gemini API 文字辨識失敗或未回傳預期格式的內容。")
            else:
                print("[!] 無法獲取測試驗證碼圖片，跳過 Gemini API 辨識測試。")
        
        except ImportError:
            print("[!] 無法導入 captcha_service。請確保該檔案存在且在 Python PATH 中。")
            print("    將使用一個固定的 Base64 範例圖片進行測試 (如果有的話)。")
            # 你可以在這裡放一個固定的 Base64 圖片字串來測試，如果 captcha_service 不可用
            # example_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA..."
            # if 'example_b64' in locals():
            #     extracted_text = get_text_from_image_gemini(example_b64)
            #     # ... 處理結果 ...
            # else:
            print("    沒有可用的範例圖片，測試無法繼續。")
        except Exception as e:
            print(f"[!] 測試過程中發生錯誤: {e}")
