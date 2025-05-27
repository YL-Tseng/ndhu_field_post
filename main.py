from login_module import perform_login
from captcha_service import get_captcha
from gemini_service import get_text_from_image_gemini

def main():
    print("主程式開始執行...")

    # 執行登入
    active_session, login_response = perform_login()

    if active_session and login_response:
        print("\n[主程式] 登入成功。")
        # 在這裡，你可以使用 active_session 進行後續需要登入狀態的操作
        # 例如：
        # print(f"登入後取得的 Session Cookies: {active_session.cookies.get_dict()}")
        # print(f"登入後最終頁面 URL: {login_response.url}")

        # 如果需要，可以將登入後頁面的內容保存或進一步處理
        # with open("main_retrieved_page.html", "w", encoding="utf-8") as f:
        #     f.write(login_response.text)
        # print("登入後頁面內容已儲存到 main_retrieved_page.html")

        # 獲取驗證碼
        print("\n[主程式] 正在嘗試獲取驗證碼...")
        captcha_image_data, captcha_id = get_captcha()

        if captcha_image_data and captcha_id:
            print("\n[主程式] 成功獲取驗證碼。")
            print(f"  Captcha ID: {captcha_id}")
            # print(f"  Image Base64 (前50字元): {captcha_image_data[:50]}...")

            # 使用 Gemini 辨識驗證碼
            print("\n[主程式] 正在使用 Gemini API 辨識驗證碼文字...")
            recognized_text = get_text_from_image_gemini(captcha_image_data)

            if recognized_text is not None: # 即使是空字串也算成功
                print("\n[主程式] 驗證碼辨識完成。")
                print(f"  辨識出的文字: \"{recognized_text}\"")
                # 在這裡，你可以使用 recognized_text 進行後續操作，例如提交表單
            else:
                print("\n[主程式] 驗證碼辨識失敗或未回傳預期格式的內容。")
        
        else:
            print("\n[主程式] 獲取驗證碼失敗。")

    else:
        print("\n[主程式] 登入失敗或模組未回傳有效的 session/response。")

if __name__ == '__main__':
    main()
