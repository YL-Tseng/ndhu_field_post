import requests
from bs4 import BeautifulSoup
import urllib.parse

# Base URL for the sports facility booking page
BASE_URL = "https://sys.ndhu.edu.tw/gc/sportcenter/SportsFields/Default.aspx"

# Headers that might be common for GET and POST requests
COMMON_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Google Chrome\";v=\"126\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}

def _extract_aspnet_form_params(html_content):
    """Helper function to extract ASP.NET form parameters and user details from HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    params = {}

    # Standard ASP.NET parameters
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})
    if viewstate: params["__VIEWSTATE"] = viewstate['value']
    
    viewstategenerator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
    if viewstategenerator: params["__VIEWSTATEGENERATOR"] = viewstategenerator['value']
    
    eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})
    if eventvalidation: params["__EVENTVALIDATION"] = eventvalidation['value']
    
    requestverificationtoken_form = soup.find('input', {'name': '__RequestVerificationToken'})
    if requestverificationtoken_form: params["__RequestVerificationToken"] = requestverificationtoken_form['value']
    
    # ToolkitScriptManager HiddenField
    toolkit_script_manager_field = soup.find('input', {'name': 'MainContent_ToolkitScriptManager1_HiddenField'})
    if toolkit_script_manager_field and toolkit_script_manager_field.get('value') is not None:
        params["MainContent_ToolkitScriptManager1_HiddenField_Value"] = toolkit_script_manager_field['value']
    else:
        # Try finding by ID as a fallback, though name is more common for form submission
        toolkit_script_manager_field_by_id = soup.find('input', {'id': 'MainContent_ToolkitScriptManager1_HiddenField'})
        if toolkit_script_manager_field_by_id and toolkit_script_manager_field_by_id.get('value') is not None:
            params["MainContent_ToolkitScriptManager1_HiddenField_Value"] = toolkit_script_manager_field_by_id['value']
        else:
            print("Warning: MainContent_ToolkitScriptManager1_HiddenField not found in HTML.")


    # Booking specific parameters
    hf_encrypted_ymdh_tag = soup.find('input', {'name': 'ctl00$MainContent$hfEncryptedYMDH'})
    if hf_encrypted_ymdh_tag and hf_encrypted_ymdh_tag.get('value') is not None:
        params["ctl00$MainContent$hfEncryptedYMDH"] = hf_encrypted_ymdh_tag['value']
        
    app_ymdh_tag = soup.find('input', {'name': 'ctl00$MainContent$AppYMDH'})
    if app_ymdh_tag and app_ymdh_tag.get('value') is not None:
        params["ctl00$MainContent$AppYMDH"] = app_ymdh_tag['value']
    elif "ctl00$MainContent$hfEncryptedYMDH" in params: 
        params["ctl00$MainContent$AppYMDH"] = params["ctl00$MainContent$hfEncryptedYMDH"]

    # Captcha related parameters
    hf_captcha_id_tag = soup.find('input', {'name': 'ctl00$MainContent$hfCaptchaId'})
    if hf_captcha_id_tag and hf_captcha_id_tag.get('value') is not None:
        params["ctl00$MainContent$hfCaptchaId"] = hf_captcha_id_tag['value']
        
    hf_captcha_image_base64_tag = soup.find('input', {'name': 'ctl00$MainContent$hfCaptchaImageBase64'})
    if hf_captcha_image_base64_tag and hf_captcha_image_base64_tag.get('value') is not None:
        params["ctl00$MainContent$hfCaptchaImageBase64"] = hf_captcha_image_base64_tag['value']

    # User details that might be pre-filled in the form
    app_dept_textbox = soup.find('input', {'name': 'ctl00$MainContent$AppDeptTextBox'})
    if app_dept_textbox and app_dept_textbox.get('value') is not None:
        params["AppDeptTextBox_Value"] = app_dept_textbox['value']
        
    email_textbox = soup.find('input', {'name': 'ctl00$MainContent$EmailTextBox'})
    if email_textbox and email_textbox.get('value') is not None:
        params["EmailTextBox_Value"] = email_textbox['value']
        
    phone_textbox = soup.find('input', {'name': 'ctl00$MainContent$PhoneTextBox'})
    if phone_textbox and phone_textbox.get('value') is not None:
        params["PhoneTextBox_Value"] = phone_textbox['value']
    
    # Date textbox (TextBox1)
    date_textbox = soup.find('input', {'name': 'ctl00$MainContent$TextBox1'})
    if date_textbox and date_textbox.get('value') is not None:
        params["TextBox1_Value"] = date_textbox['value']


    # Check for essential ASP.NET params
    required_asp_params = ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION", "__RequestVerificationToken", "MainContent_ToolkitScriptManager1_HiddenField_Value"]
    if not all(k in params for k in required_asp_params):
        missing = [k for k in required_asp_params if k not in params]
        print(f"Warning: Could not find all required ASP.NET/Toolkit form parameters. Missing: {missing}. Found: {list(params.keys())}")

    return params

def get_initial_page_and_cookies(session_cookies):
    """
    Performs a GET request to the booking page to retrieve initial form parameters and cookies.
    This is a preparatory step.
    """
    print("[get_initial_page_and_cookies] Fetching initial page...")
    headers = COMMON_HEADERS.copy()
    headers["Sec-Fetch-User"] = "?1" 
    headers["Priority"] = "u=0, i"   
    
    current_cookies = session_cookies.copy()

    try:
        response = requests.get(BASE_URL, headers=headers, cookies=current_cookies, timeout=10, verify=False)
        response.raise_for_status()
        
        form_params = _extract_aspnet_form_params(response.text)
        current_cookies.update(response.cookies.get_dict())
        
        print(f"[get_initial_page_and_cookies] Successfully fetched. Cookies updated: {response.cookies.get_dict()}")
        return response.text, form_params, current_cookies
    except requests.exceptions.RequestException as e:
        print(f"Error during initial GET request: {e}")
        return None, None, current_cookies

def trigger_add_application_form(session_cookies_after_login):
    """
    Simulates clicking the '新增申請' (Add Application) button.
    This typically refreshes the form and may present a CAPTCHA and pre-fill user data.
    """
    print("\n[trigger_add_application_form] Starting 'Add Application' POST simulation...")
    
    print("[trigger_add_application_form] Step 1: Performing GET to refresh ASP.NET parameters...")
    get_headers = COMMON_HEADERS.copy()
    get_headers["Referer"] = BASE_URL 
    get_headers["Sec-Fetch-User"] = "?1" 
    get_headers["Priority"] = "u=0, i"

    current_cookies = session_cookies_after_login.copy()

    try:
        response_get = requests.get(BASE_URL, headers=get_headers, cookies=current_cookies, timeout=10, verify=False)
        response_get.raise_for_status()
        print("[trigger_add_application_form] GET request successful.")
        current_cookies.update(response_get.cookies.get_dict())
        print(f"[trigger_add_application_form] Cookies after GET: {current_cookies}")
        
        params_from_get = _extract_aspnet_form_params(response_get.text)
        required_params_for_add_app = [
            "__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION", 
            "__RequestVerificationToken", "MainContent_ToolkitScriptManager1_HiddenField_Value"
        ]
        if not all(k in params_from_get for k in required_params_for_add_app):
            missing_params = [k for k in required_params_for_add_app if k not in params_from_get]
            print(f"[trigger_add_application_form] Error: Missing critical ASP.NET/Toolkit parameters after GET: {missing_params}")
            return None, current_cookies, None
        print("[trigger_add_application_form] Successfully extracted ASP.NET/Toolkit parameters from GET response.")

    except requests.exceptions.RequestException as e:
        print(f"[trigger_add_application_form] Error during pre-POST GET request: {e}")
        return None, current_cookies, None

    # Use the dynamically extracted ToolkitScriptManager value from the GET response
    toolkit_script_manager_value_add_app = params_from_get["MainContent_ToolkitScriptManager1_HiddenField_Value"]

    payload = {
        "MainContent_ToolkitScriptManager1_HiddenField": toolkit_script_manager_value_add_app,
        "__EVENTTARGET": "", "__EVENTARGUMENT": "", "__LASTFOCUS": "", # Corrected: "__EVENTARGUMENT"
        "__VIEWSTATE": params_from_get["__VIEWSTATE"],
        "__VIEWSTATEGENERATOR": params_from_get["__VIEWSTATEGENERATOR"],
        "__VIEWSTATEENCRYPTED": "",
        "__EVENTVALIDATION": params_from_get["__EVENTVALIDATION"],
        "__RequestVerificationToken": params_from_get["__RequestVerificationToken"],
        "ctl00$MainContent$hfEncryptedYMDH": "", "ctl00$MainContent$hfPlainYMDH": "",
        "ctl00$MainContent$hfCaptchaId": "", "ctl00$MainContent$hfCaptchaImageBase64": "",
        "ctl00$MainContent$hfCaptchaValue": "", "ctl00$MainContent$hfCaptchaErrMsg": "",
        "ctl00$MainContent$Button2": "新增申請",
        "ctl00$MainContent$LoadAppNO": "", "ctl00$MainContent$LoadKind": "",
        "ctl00$MainContent$drpkind": "請選擇", "ctl00$MainContent$DropDownList1": "請選擇",
        "ctl00$MainContent$TextBox1": params_from_get.get("TextBox1_Value", "2025/06/02"), 
    }
    
    # The date for "Add Application" POST might be fixed as per curl, or could be dynamic.
    # The curl example used "2025/06/02". If params_from_get['TextBox1_Value'] is available and desired, it's used.
    # Otherwise, it falls back to the curl's default.
    # Let's stick to the curl's default for this specific POST unless explicitly told otherwise.
    payload["ctl00$MainContent$TextBox1"] = "2025/06/02" # As per user's curl for "新增申請"

    print("[trigger_add_application_form] Step 2: POST Payload prepared.")
    # print(f"Payload for Add Application POST: {payload}") # For debugging
    
    post_headers = COMMON_HEADERS.copy()
    post_headers.update({
        "Cache-Control": "max-age=0", "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://sys.ndhu.edu.tw", "Referer": BASE_URL,
        "Sec-Fetch-User": "?1", "Priority": "u=0, i"
    })
    
    print("[trigger_add_application_form] Step 3: Sending POST request...")
    try:
        response_post = requests.post(BASE_URL, headers=post_headers, cookies=current_cookies, data=payload, timeout=15, verify=False)
        response_post.raise_for_status()
        print(f"[trigger_add_application_form] 'Add Application' POST successful. Status: {response_post.status_code}")
        
        current_cookies.update(response_post.cookies.get_dict())
        print(f"[trigger_add_application_form] Cookies after POST: {current_cookies}")

        new_form_params_from_post_html = _extract_aspnet_form_params(response_post.text)
        # Check for essential params in the *new* form state for the *next* request
        required_params_for_final_booking = [
            "__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION", 
            "__RequestVerificationToken", "MainContent_ToolkitScriptManager1_HiddenField_Value"
        ]
        if not all(k in new_form_params_from_post_html for k in required_params_for_final_booking):
            missing_final_params = [k for k in required_params_for_final_booking if k not in new_form_params_from_post_html]
            print(f"[trigger_add_application_form] Warning: Missing critical ASP.NET/Toolkit parameters from 'Add Application' POST response HTML (for next step): {missing_final_params}")
        else:
            print("[trigger_add_application_form] Successfully extracted new ASP.NET/Toolkit parameters from POST response HTML.")
        
        return response_post, current_cookies, new_form_params_from_post_html

    except requests.exceptions.RequestException as e:
        print(f"[trigger_add_application_form] Error during 'Add Application' POST request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}, Text (first 300): {e.response.text[:300]}...")
        return None, current_cookies, None

def make_booking_post_request(session_cookies, form_parameters, booking_details, captcha_details):
    """
    Makes the POST request to book a sports facility (final submission).
    `form_parameters` should now contain `MainContent_ToolkitScriptManager1_HiddenField_Value`
    extracted from the response of `trigger_add_application_form`.
    """
    print("\n[make_booking_post_request] Starting final booking POST...")
    post_headers = COMMON_HEADERS.copy()
    post_headers.update({
        "Cache-Control": "max-age=0", "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://sys.ndhu.edu.tw", "Referer": BASE_URL,
        "Sec-Fetch-User": "?1", "Priority": "u=0, i"
    })

    # Dynamically get the ToolkitScriptManager value from the previous step's form parameters
    toolkit_script_manager_final_booking = form_parameters.get("MainContent_ToolkitScriptManager1_HiddenField_Value")
    if not toolkit_script_manager_final_booking:
        print("CRITICAL ERROR: 'MainContent_ToolkitScriptManager1_HiddenField_Value' not found in form_parameters for final booking. This request will likely fail.")
        # return None # Optionally, prevent the request

    payload = {
        "MainContent_ToolkitScriptManager1_HiddenField": toolkit_script_manager_final_booking,
        "__EVENTTARGET": "ctl00$MainContent$AppPCData", "__EVENTARGUMENT": "", "__LASTFOCUS": "",
        "__VIEWSTATE": form_parameters.get("__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": form_parameters.get("__VIEWSTATEGENERATOR"),
        "__VIEWSTATEENCRYPTED": "",
        "__EVENTVALIDATION": form_parameters.get("__EVENTVALIDATION"),
        "__RequestVerificationToken": form_parameters.get("__RequestVerificationToken"),
        
        "ctl00$MainContent$hfEncryptedYMDH": form_parameters.get("ctl00$MainContent$hfEncryptedYMDH", ""), 
        "ctl00$MainContent$AppYMDH": form_parameters.get("ctl00$MainContent$AppYMDH", ""), 

        "ctl00$MainContent$hfPlainYMDH": booking_details["time_slot_plain"],
        "ctl00$MainContent$hfCaptchaId": captcha_details["hfCaptchaId"],
        "ctl00$MainContent$hfCaptchaImageBase64": form_parameters.get("ctl00$MainContent$hfCaptchaImageBase64", ""),
        "ctl00$MainContent$hfCaptchaValue": captcha_details["hfCaptchaValue"],
        "ctl00$MainContent$hfCaptchaErrMsg": "",
        
        "ctl00$MainContent$AppDeptTextBox": booking_details["department"],
        "ctl00$MainContent$EmailTextBox": booking_details["email"],
        "ctl00$MainContent$PhoneTextBox": booking_details["phone"],
        "ctl00$MainContent$BHDDL1": booking_details["start_hour"],
        "ctl00$MainContent$EHDDL1": booking_details["end_hour"],
        "ctl00$MainContent$ReasonTextBox1": booking_details.get("reason", ""),
        "ctl00$MainContent$NoteTextBox1": booking_details.get("note", ""),
        "ctl00$MainContent$NoteTextBox": "", 
        "ctl00$MainContent$LoadAppNO": "", "ctl00$MainContent$LoadKind": "",
        "ctl00$MainContent$drpkind": "請選擇", # This might need to be set based on venue type
        "ctl00$MainContent$DropDownList1": booking_details["venue_code"], # Venue code
        "ctl00$MainContent$TextBox1": booking_details["date"], # Date for the booking
    }
    print(f"[make_booking_post_request] Payload prepared. VIEWSTATE (first 30): {payload.get('__VIEWSTATE', '')[:30]}...")
    # print(f"Final booking payload: {payload}") # For debugging

    try:
        response = requests.post(BASE_URL, headers=post_headers, cookies=session_cookies, data=payload, timeout=15, verify=False)
        response.raise_for_status()
        print(f"[make_booking_post_request] Final booking POST successful. Status: {response.status_code}")
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error during final booking POST request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}, Text (first 300): {e.response.text[:300]}...")
        return None

if __name__ == '__main__':
    print("Testing booking_service.py (individual functions)...")
    mock_session_cookies_after_login = {
        "ASP.NET_SessionId": "your_session_id_here_LOGIN", ".ASPXAUTH": "your_auth_cookie_here_LOGIN",
        "lang_code": "tw", "ARRAffinity": "some_affinity_LOGIN", 
        "__RequestVerificationToken_L0dDL1NQT1JUQ0VOVEVSL1Nwb3J0c0ZpZWxkcw2": "token_cookie_LOGIN"
    }

    print("\n--- Testing get_initial_page_and_cookies (extracts initial ToolkitScriptManager) ---")
    initial_html, initial_params_for_add_app, cookies_after_initial_get = get_initial_page_and_cookies(mock_session_cookies_after_login)
    if initial_html and initial_params_for_add_app:
        print("get_initial_page_and_cookies: Success.")
        print(f"  Initial VIEWSTATE (first 30): {initial_params_for_add_app.get('__VIEWSTATE', '')[:30]}...")
        print(f"  Initial ToolkitScriptManager (first 30): {initial_params_for_add_app.get('MainContent_ToolkitScriptManager1_HiddenField_Value', '')[:30]}...")
        print(f"  Cookies after initial GET: {cookies_after_initial_get}")
    else:
        print("get_initial_page_and_cookies: Failed.")

    print("\n--- Testing trigger_add_application_form (uses ToolkitScriptManager from previous GET, extracts new one) ---")
    # For this test to be more realistic, trigger_add_application_form should use initial_params_for_add_app
    # However, its internal GET will fetch its own params. The key is that _extract_aspnet_form_params works.
    add_app_response, cookies_after_add_app, params_from_add_app_html = trigger_add_application_form(cookies_after_initial_get or mock_session_cookies_after_login)

    if add_app_response and params_from_add_app_html:
        print("trigger_add_application_form: Success.")
        print(f"  Response Status: {add_app_response.status_code}")
        print(f"  Cookies after 'Add Application' POST: {cookies_after_add_app}")
        print(f"  New VIEWSTATE from POST HTML (first 30): {params_from_add_app_html.get('__VIEWSTATE', '')[:30]}...")
        print(f"  New ToolkitScriptManager from POST HTML (first 30): {params_from_add_app_html.get('MainContent_ToolkitScriptManager1_HiddenField_Value', '')[:30]}...")
        print(f"  New CaptchaID from POST HTML: {params_from_add_app_html.get('ctl00$MainContent$hfCaptchaId')}")
        
        if params_from_add_app_html.get('ctl00$MainContent$hfCaptchaId') and params_from_add_app_html.get('MainContent_ToolkitScriptManager1_HiddenField_Value'):
            mock_booking_details = {
                "date": "2025/08/01", "time_slot_plain": "[申請]10~12", "start_hour": "10", "end_hour": "12",
                "venue_code": "BSK0A", 
                "department": params_from_add_app_html.get('AppDeptTextBox_Value', "測試系"), 
                "email": params_from_add_app_html.get('EmailTextBox_Value', "test@example.com"), 
                "phone": params_from_add_app_html.get('PhoneTextBox_Value', "0900000000")
            }
            mock_captcha_details_final = {
                "hfCaptchaId": params_from_add_app_html['ctl00$MainContent$hfCaptchaId'],
                "hfCaptchaValue": "MANUAL_CAPTCHA_INPUT" 
            }
            
            print("\n--- Testing make_booking_post_request (uses ToolkitScriptManager from trigger_add_application_form response) ---")
            
            final_booking_response = make_booking_post_request(
                cookies_after_add_app, 
                params_from_add_app_html, # These params now include the new ToolkitScriptManager
                mock_booking_details, 
                mock_captcha_details_final
            )

            if final_booking_response:
                print("make_booking_post_request: Success (request sent).")
                print(f"  Response Status: {final_booking_response.status_code}")
            else:
                print("make_booking_post_request: Failed (or critical param missing).")
        else:
            print("Skipping final booking test: Captcha ID or ToolkitScriptManager not found in 'Add Application' response HTML.")
    else:
        print("trigger_add_application_form: Failed.")

    print("\nTesting finished.")
