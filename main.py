from login_module import perform_login

def main():
    print("主程式開始執行...")
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
    else:
        print("\n[主程式] 登入失敗或模組未回傳有效的 session/response。")

if __name__ == '__main__':
    main()
