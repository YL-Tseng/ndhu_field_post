from login_module import perform_login
from captcha_service import get_captcha as get_external_captcha # Renaming to avoid confusion
from gemini_service import get_text_from_image_gemini
from booking_service import trigger_add_application_form, make_booking_post_request, _extract_aspnet_form_params
import os
from dotenv import load_dotenv
import urllib.parse

# Time slots mapping based on user's guide
TIME_SLOTS_MAPPING = {
    "06": "[申請]06~08", "07": "[申請]07~09", "08": "[申請]08~10", "09": "[申請]09~11",
    "10": "[申請]10~12", "11": "[申請]11~13", "12": "[申請]12~14", "13": "[申請]13~15",
    "14": "[申請]14~16", "15": "[申請]15~17", "16": "[申請]16~17", "17": "[申請]17~19",
    "18": "[申請]18~19", "19": "[申請]19~21", "20": "[申請]20~21", "21": "[申請]21~23",
    "22": "[申請]22~23"
}

# Venue codes mapping based on user's guide
VENUE_CODES_MAPPING = {
    "ARO0A": "ARO0A柔道教室A", "BSB0A": "BSB0A棒球場", "BSK02": "BSK02高爾夫球場",
    "BSK0A": "BSK0A籃球場A", "BSK0B": "BSK0B籃球場B", "BSK0C": "BSK0C籃球場C",
    "BSK0D": "BSK0D籃球場D", "BSK0E": "BSK0E籃球場E", "BSK0F": "BSK0F籃球場F",
    "BSK0G": "BSK0G籃球場I (K書中心)", "BSK0H": "BSK0H籃球場J (k書中心)",
    "BSK0J": "BSK0J籃球場L (集賢館場地)", "BSK0K": "BSK0K籃球場K (集賢館場地)",
    "BSKR1": "BSKR1籃球場G (原R1)", "BSKR2": "BSKR2籃球場H (原R2)", "GYM0A": "GYM0A韻律教室",
    "PLA0A": "PLA0A體育室前廣場", "SFT0B": "SFT0B志學門壘球場1", "TNS0G": "TNS0G網球場G",
    "TNS0H": "TNS0H網球場H", "TRK0A": "TRK0A田徑場", "VOL0A": "VOL0A排球場A-女",
    "VOL0B": "VOL0B排球場B-男", "VOL0C": "VOL0C排球場C-女", "VOL0D": "VOL0D排球場D-男",
    "VOL0E": "VOL0E排球場E-女", "VOL0F": "VOL0F排球場F-男", "VOL0G": "VOL0G排球場G-女",
    "VOL0H": "VOL0H排球場H-男", "VOL0J": "VOL0J排球場L-女 (集賢館場地)",
    "VOL0K": "VOL0K排球場K-男 (集賢館場地)", "VOLR1": "VOLR1排球場I-女 (原R1)",
    "VOLR2": "VOLR2排球場J-男 (原R2)", "XDNCE": "XDNCE壽豐館-舞蹈教室",
    "XGMB1": "XGMB1壽館場B-羽1", "XGMB2": "XGMB2壽館場B-羽2", "XGMB3": "XGMB3壽館場B-羽3",
    "XGMB4": "XGMB4壽館場B-羽4", "XGMC1": "XGMC1壽館場C-排1", "XGMC2": "XGMC2壽館場C-排2",
    "XGMC3": "XGMC3壽館場C-排3", "XGMC4": "XGMC4壽館場C-排4", "XGYMA": "XGYMA壽館場A-籃球",
    "XTKDO": "XTKDO壽豐館-跆拳道教室", "XTNA1": "XTNA1網球場1", "XTNA2": "XTNA2網球場2",
    "XTNB1": "XTNB1網球場3", "XTNB2": "XTNB2網球場4", "XTNB3": "XTNB3網球場5",
    "XTNB4": "XTNB4網球場6 (紅土)", "XTNB5": "XTNB5網球場7 (紅土)",
    "XTT0W": "XTT0W壽豐體育館桌球室全部"
}

def main():
    load_dotenv()  # Load environment variables from .env file
    print("主程式開始執行...")

    user_department_env = os.getenv("USER_DEPARTMENT", "材料科學與工程學系")
    user_email_env = os.getenv("USER_EMAIL", "your_email@gms.ndhu.edu.tw") # PLEASE REPLACE
    user_phone_env = os.getenv("USER_PHONE", "0912345678") # PLEASE REPLACE

    # 執行登入
    active_session, login_response, initial_login_cookies = perform_login()

    if not (active_session and login_response):
        print("\n[主程式] 登入失敗或模組未回傳有效的 session/response。")
        return

    print("\n[主程式] 登入成功。")
    current_cookies = active_session.cookies.get_dict()
    if initial_login_cookies:
        current_cookies.update(initial_login_cookies)
    print(f"  登入後 Cookies: {current_cookies}")

    # --- Step 1: Trigger "Add Application" form to get latest parameters and pre-filled data ---
    print("\n[主程式] Step 1: 觸發「新增申請」表單...")
    add_app_response, cookies_after_add_app, form_params_after_add_app = trigger_add_application_form(current_cookies)

    if not (add_app_response and form_params_after_add_app):
        print("[主程式] 觸發「新增申請」表單失敗。無法繼續。")
        return
    
    print("[主程式] 成功觸發「新增申請」表單。")
    current_cookies = cookies_after_add_app # Update cookies
    current_form_params = form_params_after_add_app # These are the most up-to-date params

    # Extract user details from the form if available, otherwise use .env
    form_department = current_form_params.get("AppDeptTextBox_Value", user_department_env)
    form_email = current_form_params.get("EmailTextBox_Value", user_email_env)
    form_phone = current_form_params.get("PhoneTextBox_Value", user_phone_env)

    print(f"  從表單讀取到的系所: '{form_department}' (環境變數為: '{user_department_env}')")
    print(f"  從表單讀取到的Email: '{form_email}' (環境變數為: '{user_email_env}')")
    print(f"  從表單讀取到的電話: '{form_phone}' (環境變數為: '{user_phone_env}')")
    
    # Use form values if they exist, otherwise fallback to .env (or you can choose to always use .env)
    final_user_department = form_department if form_department else user_department_env
    final_user_email = form_email if form_email else user_email_env
    final_user_phone = form_phone if form_phone else user_phone_env
    
    # --- Step 2: Get CAPTCHA from the refreshed form (if present) or external service ---
    # The CAPTCHA might now be part of form_params_after_add_app
    captcha_id_from_form = current_form_params.get("ctl00$MainContent$hfCaptchaId")
    captcha_image_base64_from_form = current_form_params.get("ctl00$MainContent$hfCaptchaImageBase64")
    
    recognized_text = None
    actual_captcha_id_for_submission = None

    if captcha_id_from_form and captcha_image_base64_from_form:
        print("\n[主程式] Step 2: 偵測到表單內嵌驗證碼。")
        print(f"  表單內嵌 Captcha ID: {captcha_id_from_form}")
        # The image might be 'data:image/jpeg;base64,ActualDataHere' or just 'ActualDataHere'
        if ',' in captcha_image_base64_from_form:
            captcha_image_base64_data_only = captcha_image_base64_from_form.split(',', 1)[1]
        else:
            captcha_image_base64_data_only = captcha_image_base64_from_form
        
        print("\n[主程式] 正在使用 Gemini API 辨識內嵌驗證碼文字...")
        recognized_text = get_text_from_image_gemini(captcha_image_base64_data_only)
        actual_captcha_id_for_submission = captcha_id_from_form
    else:
        print("\n[主程式] Step 2: 表單未包含驗證碼圖片/ID，嘗試從外部服務獲取驗證碼...")
        # This path might be less common if "Add Application" always provides one.
        ext_captcha_image_base64, ext_captcha_id, ext_captcha_cookies = get_external_captcha(current_cookies)
        if ext_captcha_image_base64 and ext_captcha_id:
            print("  成功從外部服務獲取驗證碼。")
            print(f"    External Captcha ID: {ext_captcha_id}")
            if ext_captcha_cookies:
                current_cookies.update(ext_captcha_cookies)
                print(f"    Cookies after external CAPTCHA GET: {current_cookies}")
            
            print("\n[主程式] 正在使用 Gemini API 辨識外部驗證碼文字...")
            recognized_text = get_text_from_image_gemini(ext_captcha_image_base64) # Assuming it's already base64 data
            actual_captcha_id_for_submission = ext_captcha_id
        else:
            print("[主程式] 從外部服務獲取驗證碼失敗。")

    if recognized_text is None or actual_captcha_id_for_submission is None:
        print("\n[主程式] 驗證碼處理失敗 (未獲取到圖片/ID 或辨識失敗)。無法繼續預約。")
        return

    print("\n[主程式] 驗證碼辨識完成。")
    print(f"  辨識出的文字: \"{recognized_text}\"")
    print(f"  將用於提交的 Captcha ID: {actual_captcha_id_for_submission}")

    # --- Step 3: Prepare and Make Final Booking ---
    print("\n[主程式] Step 3: 開始最終預約流程...")

    # Define Booking Details (example - make this dynamic later)
    target_start_hour_key = "06"  # 時段為06
    target_venue_key = "VOL0C"    # 場地為VOL0C
    target_date = "2025/06/05"  # 日期為2025/06/05

    time_slot_plain = TIME_SLOTS_MAPPING.get(target_start_hour_key)
    actual_start_hour, actual_end_hour = None, None
    if time_slot_plain:
        try:
            parts = time_slot_plain.split(']')[1].split('~')
            actual_start_hour = parts[0]
            actual_end_hour = parts[1]
        except (IndexError, AttributeError) as e:
            print(f"  錯誤：無法從 \"{time_slot_plain}\" 解析開始/結束時間。錯誤: {e}")
            time_slot_plain = None 

    if not time_slot_plain or not VENUE_CODES_MAPPING.get(target_venue_key):
        print(f"  錯誤：無效的開始時間索引 '{target_start_hour_key}' 或場地索引 '{target_venue_key}'。跳過預約。")
    else:
        booking_details = {
            "date": target_date,
            "time_slot_plain": time_slot_plain, # This is "hfPlainYMDH"
            "start_hour": actual_start_hour,    # This is "BHDDL1"
            "end_hour": actual_end_hour,        # This is "EHDDL1"
            "venue_code": target_venue_key,     # This is "DropDownList1"
            "department": final_user_department,
            "email": final_user_email,
            "phone": final_user_phone,
            "reason": "運動", # Example reason
            "note": "自動預約測試" # Example note
        }
        print(f"  預約詳細資料: {booking_details}")

        captcha_details_for_booking = {
            "hfCaptchaId": actual_captcha_id_for_submission,
            "hfCaptchaValue": recognized_text
        }

        # Ensure hfEncryptedYMDH and AppYMDH are correctly populated for the final POST
        # The first curl example for final booking had specific values for these.
        # If they are not in current_form_params (e.g. after "Add Application"), we might need a strategy.
        # For now, make_booking_post_request uses fallbacks from the original curl if not found in form_parameters.
        # Let's ensure what we pass to make_booking_post_request is what we intend.
        # The `current_form_params` (from `trigger_add_application_form`) should be the most relevant.
        
        # The `hfEncryptedYMDH` and `AppYMDH` for the *final* booking payload
        # are often related to the *selected* date/time/venue, not just static values.
        # The first curl example showed "vZP1eU%2BZCOVm%2FbjOJHqI0HrBsJf%2FUaFiPmYxh%2FLfDHoK58yb0gGJoQ%3D%3D"
        # This value might be generated by client-side JS based on selections.
        # For now, we rely on `make_booking_post_request` to use what's in `current_form_params`
        # or its hardcoded fallback. This is a potential point of failure if the server expects a specific
        # encrypted value for the chosen slot that isn't present in `current_form_params`.
        # The `hfPlainYMDH` is what we construct (e.g., "[申請]09~11").
        
        # The `ctl00$MainContent$hfEncryptedYMDH` and `ctl00$MainContent$AppYMDH` in the *payload*
        # for the final booking seem to be related to the *selected* time slot.
        # The example from the first curl: "vZP1eU%2BZCOVm%2FbjOJHqI0HrBsJf%2FUaFiPmYxh%2FLfDHoK58yb0gGJoQ%3D%3D"
        # This needs to be correctly generated or found.
        # For now, we will pass current_form_params, and make_booking_post_request will use its values
        # or fallbacks. This is a known complex part.
        # The `hfPlainYMDH` is correctly set from `booking_details`.

        print("\n  發送最終預約 POST 請求...")
        post_response = make_booking_post_request(
            session_cookies=current_cookies,
            form_parameters=current_form_params, # Use params from "Add Application" response
            booking_details=booking_details,
            captcha_details=captcha_details_for_booking
        )

        if post_response:
            print("  最終預約 POST 請求已發送。")
            print(f"    回應狀態碼: {post_response.status_code}")
            response_text_preview = post_response.text.replace('\n', ' ').replace('\r', '')[:1000] # Increased preview length
            print(f"    回應內容 (前1000字元預覽):\n    {response_text_preview}...")
            
            # Check for multiple success indicators
            success_indicators = [
                "預約成功", 
                "成功借用",
                '<td align="center" style="white-space:nowrap;">VOL0C</td>' # Specific check for VOL0C
            ]
            failure_indicators = ["失敗", "錯誤", "已被預約", "無法借用"]

            if any(indicator in post_response.text for indicator in success_indicators):
                print("\n[主程式] 預約可能成功！請檢查回應內容確認。")
            elif any(indicator in post_response.text for indicator in failure_indicators):
                print("\n[主程式] 預約可能失敗或場地已被預約/無法借用。請檢查回應內容。")
            else:
                print("\n[主程式] 預約狀態不確定。請手動檢查回應內容。")
        else:
            print("  最終預約 POST 請求失敗 (模組回傳 None)。")
    # --- Booking Process Ends Here ---

if __name__ == '__main__':
    main()
# Removed redundant main block, the one above is the correct one.
