# hugely relied on https://github.com/md-y/mangadex-full-api for formatting requests

import random
import requests
import urllib
import json

from lxml import html
from bs4 import BeautifulSoup as bs

class DexAPI:
    @staticmethod
    def parse_cookie(cookie_str, further_parse = True):
        cookie_split = cookie_str.split(';')
        cookie = {}
        for itm in cookie_split:
            itm_split = itm.split('=')
            for i in range(len(itm_split)):
                itm_split[i] = itm_split[i].strip()
            if "__ddg1" == itm_split[0]:
                cookie['__ddg1'] = itm_split[1]
            elif "domain" == itm_split[0]:
                tmp = itm_split[1].split(',')
                for i in range(len(tmp)):
                    tmp[i] = tmp[i].strip()
                if(len(tmp) == 2):
                    cookie['domain'] = tmp[0]
                    cookie['rememberme_name'] = tmp[1]
                    cookie['rememberme_id'] = itm_split[2]
                else:
                    cookie['domain'] = itm_split[1]
            elif "path" == itm_split[0]:
                cookie['path'] = itm_split[1]
            elif "Max-Age" == itm_split[0]:
                cookie['max-age'] = itm_split[1]
            elif "expires" == itm_split[0]:
                cookie['expires'] = itm_split[1]
            elif "Expires" == itm_split[0]:
                tmp = itm_split[1].split(',')
                for i in range(len(tmp)):
                    tmp[i] = tmp[i].strip()
                cookie['session_name'] = tmp[-1]
                cookie['session_id'] = itm_split[2]
        if(not further_parse):
            return cookie

        req_cookies = {cookie['session_name']: cookie['session_id']}
        if 'rememberme_name' in cookie:
            req_cookies[cookie['rememberme_name']] = cookie['rememberme_id']
        req_cookies['mangadex_h_toggle'] = 1

        return req_cookies

    
    def create_boundary(self):
        self.boundary = "mfa" + str(random.randint(0, 1001))
        return self
    
    # requires a mangadex username and password
    def __init__(self, uname, password, remember = False, auto_login = True):
        self.payload = {
            "login_username": uname,
            "login_password": password,
            "remember_me": 1 if remember else 0
        }
        self.create_boundary()
        if auto_login:
            self.login()
    
    def login(self):
        headers = {
            "referer": "https://mangadex.org/login",
            "Access-Control-Allow-Origin": "*",
            "User-Agent": "mangadex-full-api",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "multipart/form-data; boundary=" + self.boundary
        }
        
        payload_str = ""
        for k, v in self.payload.items():
            payload_str += "--" + self.boundary + "\n"
            payload_str += "Content-Disposition: form-data; name=\"" + str(k) + "\"\n"
            payload_str += "\n"
            payload_str += str(v) +"\n"
        payload_str += "--" + self.boundary + "--"


        response = requests.post("https://mangadex.org/ajax/actions.ajax.php?function=login", 
            data=payload_str, headers=headers)

        self.cookie = self.parse_cookie(response.headers['Set-Cookie'])
        return self
    
    def quick_search(self, title):
        headers = {
            "User-Agent": "mangadex-full-api",
            "Cookie": "",
            "Access-Control-Allow-Origin": "*"
        }
        
        for k, v in self.cookie.items():
            headers['Cookie'] += str(k) + "=" + str(v) + "; "
        
        search = requests.get("https://mangadex.org/quick_search/" + urllib.parse.quote_plus(title), headers=headers)
        
        if 'Set-Cookie' in search.headers:
            self.cookie = self.parse_cookie(search.headers['Set-Cookie'])

        if "<!-- login_container -->" in search.text:
            raise Exception("Not Logged In...")

        page = bs(search.text, 'lxml')
        find = page.find('div', attrs={'class': 'manga-entry'})
        if find:
            return find["data-id"]
        
        return None

    def info(self, id):
        info_json = requests.get("https://mangadex.org/api/manga/" + str(id)).text
        info = json.loads(info_json)
        return info
