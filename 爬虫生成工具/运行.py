# -*- coding: utf-8 -*-
"""
Auto-generated Spider -- 6 curl(s) / 3 API group(s)
Dependencies: pip install curl_cffi
Run:         python this_file.py
"""

import random, time, json, logging, threading
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urljoin

import curl_cffi.requests as requests

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger("Spider")


class SpiderConfig:
    """Global config --- all knobs here."""

    USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    ]
    MIN_DELAY: float = 1.0
    MAX_DELAY: float = 3.0
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 2.0
    RETRY_STATUS_CODES: Tuple[int, ...] = (429, 500, 502, 503, 504)
    PROXY: Optional[str] = None
    IMPERSONATE: str = "chrome124"
    REQUESTS_PER_SECOND: float = 2.0
    TIMEOUT: int = 30
    DEFAULT_HEADERS: Dict[str, str] = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }


class RateLimiter:
    def __init__(self, rate: float):
        self._interval = 1.0/rate if rate > 0 else 0
        self._lock = threading.Lock(); self._last = 0.0
    def acquire(self):
        if self._interval <= 0: return
        with self._lock:
            now = time.monotonic(); w = self._interval-(now-self._last)
            if w > 0: time.sleep(w); self._last = time.monotonic()
            else: self._last = now


class BaseSpider:
    def __init__(self, config=None):
        self.config = config or SpiderConfig()
        self._limiter = RateLimiter(self.config.REQUESTS_PER_SECOND)
        self._session = None; self._init_session()
    def _init_session(self):
        self._session = requests.Session(impersonate=self.config.IMPERSONATE)
    @property
    def session(self):
        if self._session is None: self._init_session()
        return self._session
    def close(self):
        if self._session: self._session.close(); self._session = None
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def _random_ua(self):
        return random.choice(self.config.USER_AGENTS)
    def _random_delay(self):
        time.sleep(random.uniform(self.config.MIN_DELAY, self.config.MAX_DELAY))
    def _build_kwargs(self, **kw):
        mh = {**self.config.DEFAULT_HEADERS, **kw.pop("headers", {})}
        mh["User-Agent"] = self._random_ua()
        kw["headers"] = mh
        kw["impersonate"] = self.config.IMPERSONATE
        kw.setdefault("timeout", self.config.TIMEOUT)
        if self.config.PROXY:
            kw["proxies"] = {"http": self.config.PROXY, "https": self.config.PROXY}
        return kw
    def request(self, method, url, **kw):
        kw = self._build_kwargs(**kw)
        last_exc = None
        for attempt in range(self.config.MAX_RETRIES + 1):
            try:
                self._limiter.acquire(); self._random_delay()
                resp = self.session.request(method, url, **kw)
                if resp.status_code in self.config.RETRY_STATUS_CODES:
                    if attempt < self.config.MAX_RETRIES:
                        bo = self.config.RETRY_BACKOFF_FACTOR**(attempt+1)
                        log.warning("Retry %d/%d [%s %s] status=%d backoff=%.1fs",
                                    attempt+1, self.config.MAX_RETRIES, method, url, resp.status_code, bo)
                        time.sleep(bo); continue
                resp.raise_for_status(); return resp
            except requests.RequestsError as exc:
                last_exc = exc
                if attempt < self.config.MAX_RETRIES:
                    bo = self.config.RETRY_BACKOFF_FACTOR**(attempt+1)
                    log.warning("Retry %d/%d [%s %s] %s backoff=%.1fs",
                                attempt+1, self.config.MAX_RETRIES, method, url, exc, bo)
                    time.sleep(bo)
                else: raise
        raise last_exc
    def get(self, url, **kw):    return self.request("GET", url, **kw)
    def post(self, url, **kw):   return self.request("POST", url, **kw)


# ============================================================================
# API classes  (auto-generated -- do not edit)
# ============================================================================
class httpbin_org_API(BaseSpider):
    """API -- https://httpbin.org"""
    BASE_URL = "https://httpbin.org"

    def fetch_get(self, page=None, limit=None, sort=None):
        """
        GET https://httpbin.org/get

        Headers:
            Accept: application/json, text/plain, */*
            Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
            Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dummy
            Connection: keep-alive
            Referer: https://httpbin.org/
        Params: {'page': '1', 'limit': '20', 'sort': 'desc'}
        """
        url = urljoin(self.BASE_URL, "/get")

        _headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dummy",
            "Connection": "keep-alive",
            "Referer": "https://httpbin.org/",
        }

        _params = {k: v for k, v in [("page", page), ("limit", limit), ("sort", sort)] if v is not None}

        _cookies = {}

        log.debug("[httpbin_org_API] GET %s", url)
        return self.request("get", url, headers=_headers, params=_params, cookies=_cookies)

    def create_post(self, data: dict = None):
        """
        POST https://httpbin.org/post

        Headers:
            Accept: application/json
            Content-Type: application/json
            Origin: https://httpbin.org
        Body: {"username":"admin","password":"secret123","remember":true}
        """
        url = urljoin(self.BASE_URL, "/post")

        _headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://httpbin.org",
        }

        _params = {}

        _cookies = {}

        log.debug("[httpbin_org_API] POST %s", url)
        return self.request("post", url, headers=_headers, params=_params, cookies=_cookies, json=data)

    def fetch_cookies(self):
        """
        GET https://httpbin.org/cookies

        Headers:
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
        """
        url = urljoin(self.BASE_URL, "/cookies")

        _headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        _params = {}

        _cookies = {}

        log.debug("[httpbin_org_API] GET %s", url)
        return self.request("get", url, headers=_headers, params=_params, cookies=_cookies)


class jsonplaceholder_typicode_com_API(BaseSpider):
    """API -- https://jsonplaceholder.typicode.com"""
    BASE_URL = "https://jsonplaceholder.typicode.com"

    def fetch_posts_comments(self):
        """
        GET https://jsonplaceholder.typicode.com/posts/1/comments

        Headers:
            Accept: application/json
        """
        url = urljoin(self.BASE_URL, "/posts/1/comments")

        _headers = {
            "Accept": "application/json",
        }

        _params = {}

        _cookies = {}

        log.debug("[jsonplaceholder_typicode_com_API] GET %s", url)
        return self.request("get", url, headers=_headers, params=_params, cookies=_cookies)

    def create_posts(self, data: dict = None):
        """
        POST https://jsonplaceholder.typicode.com/posts

        Headers:
            Content-Type: application/json; charset=UTF-8
            Accept: application/json
        Body: {"title":"foo","body":"bar","userId":1}
        """
        url = urljoin(self.BASE_URL, "/posts")

        _headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json",
        }

        _params = {}

        _cookies = {}

        log.debug("[jsonplaceholder_typicode_com_API] POST %s", url)
        return self.request("post", url, headers=_headers, params=_params, cookies=_cookies, json=data)


class www_douyin_com_API(BaseSpider):
    """API -- https://www.douyin.com"""
    BASE_URL = "https://www.douyin.com"

    def create_module_feed(self, device_platform=None, aid=None, channel=None, module_id=None, count=None, refresh_index=None, refer_type=None, pull_type=None, awemePcRecRawData=None, Seo_Flag=None, install_time=None, is_active_tab=None, use_lite_type=None, xigua_user=None, pc_client_type=None, pc_libra_divert=None, update_version_code=None, support_h265=None, support_dash=None, version_code=None, version_name=None, cookie_enabled=None, screen_width=None, screen_height=None, browser_language=None, browser_platform=None, browser_name=None, browser_version=None, browser_online=None, engine_name=None, engine_version=None, os_name=None, os_version=None, cpu_core_num=None, device_memory=None, platform=None, downlink=None, effective_type=None, round_trip_time=None, webid=None, uifid=None, verifyFp=None, fp=None, msToken=None, a_bogus=None):
        """
        POST https://www.douyin.com/aweme/v2/web/module/feed/

        Headers:
            accept: application/json, text/plain, */*
            accept-language: zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7
            cache-control: no-cache
            content-length: 0
            content-type: application/x-www-form-urlencoded; charset=UTF-8
            origin: https://www.douyin.com
            pragma: no-cache
            priority: u=1, i
            referer: https://www.douyin.com/jingxuan
            sec-ch-ua: "Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"
            sec-ch-ua-mobile: ?0
            sec-ch-ua-platform: "Windows"
            sec-fetch-dest: empty
            sec-fetch-mode: cors
            sec-fetch-site: same-origin
            uifid: b684c79658e5909c916769b2e80c406ed39ea89d6c7cce823581f3f595501a343299ddc8f63e5c7099805529485100fff347690eaf60905dc28912a1c87db414ded6f0e7832221c3899bb71c895fdc4531f7a6d7e90a979eb4c65af0a223c4790ff57319e7f7fc803b5fb8b827fe16f32f23913ee4b64cd461f86bf76130970d6f6f9e432e186a40b7553e9bbb2243df1a7fa2bcc86be296799c12ca63ab4056
            x-secsdk-csrf-token: DOWNGRADE
        Params: {'device_platform': 'webapp', 'aid': '6383', 'channel': 'channel_pc_web', 'module_id': '3003101', 'count': '20', 'refresh_index': '6', 'refer_type': '10', 'pull_type': '2', 'awemePcRecRawData': '{"is_xigua_user":0,"danmaku_switch_status":0,"is_client":false}', 'Seo-Flag': '0', 'install_time': '1779000437', 'is_active_tab': 'false', 'use_lite_type': '0', 'xigua_user': '0', 'pc_client_type': '1', 'pc_libra_divert': 'Windows', 'update_version_code': '170400', 'support_h265': '1', 'support_dash': '1', 'version_code': '170400', 'version_name': '17.4.0', 'cookie_enabled': 'true', 'screen_width': '1280', 'screen_height': '720', 'browser_language': 'zh-CN', 'browser_platform': 'Win32', 'browser_name': 'Chrome', 'browser_version': '148.0.0.0', 'browser_online': 'true', 'engine_name': 'Blink', 'engine_version': '148.0.0.0', 'os_name': 'Windows', 'os_version': '10', 'cpu_core_num': '8', 'device_memory': '16', 'platform': 'PC', 'downlink': '10', 'effective_type': '4g', 'round_trip_time': '150', 'webid': '7640748656416785974', 'uifid': 'b684c79658e5909c916769b2e80c406ed39ea89d6c7cce823581f3f595501a343299ddc8f63e5c7099805529485100fff347690eaf60905dc28912a1c87db414ded6f0e7832221c3899bb71c895fdc4531f7a6d7e90a979eb4c65af0a223c4790ff57319e7f7fc803b5fb8b827fe16f32f23913ee4b64cd461f86bf76130970d6f6f9e432e186a40b7553e9bbb2243df1a7fa2bcc86be296799c12ca63ab4056', 'verifyFp': 'verify_mp9exe2i_uAIZq4D2_zJS6_4sLo_957w_7tmoUr0CCIQK', 'fp': 'verify_mp9exe2i_uAIZq4D2_zJS6_4sLo_957w_7tmoUr0CCIQK', 'msToken': 'YXupVmSoGF40lsYnUVU5V7VbLybVSyybMYyTdFTKwWRlsvUDhscPnmrkTXqRs3iTEaAHa71oYhbwqE9KZ1sTAoiU4uKrUIXHZ217lPKwRduWfsttE0sewjt5vrx7pNhjQQvqOJL_RWzouxOpB4AIIlNPDB_ziiqaxMExuWMOikRg', 'a_bogus': 'DXsfg7Wid2mnKVMtmK-wS--l67olNPSyUFiObPKTCxFQahlOLSNfFNSObxFPR249bmBTkoVHDVMAbDVcmGXhZCrpFmhfu/XfAU25nXmogqqkYM48LrmmSLDzqwMO8RUqe527N9y5ls076x5lIqOwWOAa95FiRmYpSqeIdFYybDC8pPyTIo2ftrbAwHy='}
        Cookies: {'enter_pc_once': '1', 'UIFID_TEMP': 'b684c79658e5909c916769b2e80c406ed39ea89d6c7cce823581f3f595501a343299ddc8f63e5c7099805529485100ffbeb77454b5bd416d421f3a2e042f8a0431965d585d2d1c360c1454f9dcee8fd8', 's_v_web_id': 'verify_mp9exe2i_uAIZq4D2_zJS6_4sLo_957w_7tmoUr0CCIQK', 'hevc_supported': 'true', 'fpk1': 'U2FsdGVkX19GyuqB0GEkhBrz00AmJlCeMI0CcQotl+dK8Kyi+TFg2cbTZUujXdSgIHAP8c0UhJp0bwJfXPmZEw==', 'fpk2': 'b87543ecbc0ba610d9f06f9f2c432a46', 'passport_csrf_token': '4b4b96abb4181efa09516ca5a0888a35', 'passport_csrf_token_default': '4b4b96abb4181efa09516ca5a0888a35', 'bd_ticket_guard_client_web_domain': '2', 'SEARCH_UN_LOGIN_PV_CURR_DAY': '%7B%22date%22%3A1779005552185%2C%22count%22%3A4%7D', 'passport_mfa_token': 'Cjf7Iw1B4%2FREbavHMSLEvkVZXPrQws0aWnuUeJhprzsdE0aRnkpq%2BokIb%2FZVA3pqJaXx3pJxk15xGkoKPAAAAAAAAAAAAABQbtE8cqnEUbRjifpFzSRYD3z0bLECRta%2Bv9mmJQM0aQmUkTuiPUeOamBFj%2BCpicsAuRCY2JEOGPax0WwgAiIBA2VXr14%3D', 'd_ticket': 'd356df68c311e7e4d0754ab2c3a131b95c8ef', 'passport_assist_user': 'CkHhyOk8fGFPImcjwhcPYQU9XjkedHFnQxayNsAtL4Vu_m_NDHuiLp8DSuue4bn1Ry6px9REgbagqb9uPsfvJHCipxpKCjwAAAAAAAAAAAAAUG4QODXLnHQhTpqmulAeM73mLcyP6vnhKXq3viZPkpuLc8e7_bbvtNXsC5ZDPNfYcBAQ8NiRDhiJr9ZUIAEiAQO0pKYG', 'n_mh': 'IM1tu_RKX6_8-1LWBmD8Se5mr0FbTF-qfxUidJrOYzQ', 'sid_guard': '295aca0eef73949bcccfa42c8629b697%7C1779005956%7C5184000%7CThu%2C+16-Jul-2026+08%3A19%3A16+GMT', 'uid_tt': '1feb98ad9138656bbe1138f80b4a23b8', 'uid_tt_ss': '1feb98ad9138656bbe1138f80b4a23b8', 'sid_tt': '295aca0eef73949bcccfa42c8629b697', 'sessionid': '295aca0eef73949bcccfa42c8629b697', 'sessionid_ss': '295aca0eef73949bcccfa42c8629b697', 'session_tlb_tag': 'sttt%7C4%7CKVrKDu9zlJvMz6Qshim2l__________YxOUsII353fukwsQeRsRTk4xe_0ZzEPX6-VeAA1WxQW0%3D', 'is_staff_user': 'false', 'has_biz_token': 'false', 'sid_ucp_v1': '1.0.0-KDA4ZDFhZGVlNjc2Yzk2MzEyNmQyMzk3ZDkzMDNkNTA3MjljOWMxMmQKIQiwjoDX4M2KBRCE9KXQBhjvMSAMMK_dgq8GOAdA9AdIBBoCaGwiIDI5NWFjYTBlZWY3Mzk0OWJjY2NmYTQyYzg2MjliNjk3', 'ssid_ucp_v1': '1.0.0-KDA4ZDFhZGVlNjc2Yzk2MzEyNmQyMzk3ZDkzMDNkNTA3MjljOWMxMmQKIQiwjoDX4M2KBRCE9KXQBhjvMSAMMK_dgq8GOAdA9AdIBBoCaGwiIDI5NWFjYTBlZWY3Mzk0OWJjY2NmYTQyYzg2MjliNjk3', '_bd_ticket_crypt_cookie': '63870b4f7df538ee98e1183d90c36da0', '__security_mc_1_s_sdk_sign_data_key_web_protect': 'e54581f8-40af-a48a', '__security_mc_1_s_sdk_cert_key': '67cbbd9c-4354-8732', '__security_mc_1_s_sdk_crypt_sdk': '4bed137d-4b7b-b0d3', '__security_server_data_status': '1', 'login_time': '1779005953677', 'SEARCH_RESULT_LIST_TYPE': '%22single%22', 'UIFID': 'b684c79658e5909c916769b2e80c406ed39ea89d6c7cce823581f3f595501a343299ddc8f63e5c7099805529485100fff347690eaf60905dc28912a1c87db414ded6f0e7832221c3899bb71c895fdc4531f7a6d7e90a979eb4c65af0a223c4790ff57319e7f7fc803b5fb8b827fe16f32f23913ee4b64cd461f86bf76130970d6f6f9e432e186a40b7553e9bbb2243df1a7fa2bcc86be296799c12ca63ab4056', '__ac_nonce': '06a23a4f3003e9a12886d', '__ac_signature': '_02B4Z6wo00f01kZyaGgAAIDDEvVILWiRXqJGUmzAAPvO47', 'device_web_cpu_core': '8', 'device_web_memory_size': '16', 'architecture': 'amd64', 'is_support_rtm_web_ts': '1', 'dy_swidth': '1280', 'dy_sheight': '720', 'stream_recommend_feed_params': '%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1280%2C%5C%22screen_height%5C%22%3A720%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A8%2C%5C%22device_memory%5C%22%3A16%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A150%7D%22', 'SelfTabRedDotControl': '%5B%7B%22id%22%3A%227605199502810548287%22%2C%22u%22%3A47%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227401418628932831266%22%2C%22u%22%3A92%2C%22c%22%3A0%7D%5D', 'bd_ticket_guard_client_data': 'eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCRmNmN0xTem9WS2R5Qkt0R3NsMXdEOUZidmFIL21WVjFPYVBuQnhKMU5XclZseXc4NnozcDBHTGRUQTc3NDRUSDBrY0NzKzMxUnFuSWc5LzNXUmJjakE9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D', 'strategyABtestKey': '%221780720895.462%22', 'ttwid': '1%7CgwKZI35hMLVFoD13h0F697Po62c7gBbtt0fVNvsqm3U%7C1780720895%7C28d16ceaa614d95d2bd2654757b110d5dbe141bc9a7023258168dfb949f0b538', 'publish_badge_show_info': '%220%2C0%2C0%2C1780720896880%22', 'home_can_add_dy_2_desktop': '%221%22', 'odin_tt': 'e2a1a4d33b9811591ad03efa6410b0e1d1b26f3b5a4761cff97702c48203fb590394ad2adf8026ebeebe62eee9d1573c7d53d908fff444d89daff0d52e5338ea', 'biz_trace_id': 'cd91b02e', 'IsDouyinActive': 'true', 'sdk_source_info': '7e276470716a68645a606960273f276364697660272927676c715a6d6069756077273f276364697660272927666d776a68605a607d71606b766c6a6b5a7666776c7571273f275e58272927666a6b766a69605a696c6061273f27636469766027292762696a6764695a7364776c6467696076273f275e582729277672715a646971273f2763646976602729277f6b5a666475273f2763646976602729276d6a6e5a6b6a716c273f2763646976602729276c6b6f5a7f6367273f27636469766027292771273f2733373d30303d343732353d3234272927676c715a75776a716a666a69273f2763646976602778', 'bit_env': '_Hao8zgCoGW-IGnRgD52bSZzqyKO8M38HeluyN2hGgNUhOrH_UQBSmhnxiMXZhnNWgOKGq8pfCiBpjorP6mCLlC_qZMbmjhQnnIGG7cf2EOYCDwXyUGqQ8ShnSQQbZVg4Yki1ZzBzOVtXO7gWpl6ge0I7znJeL9J1s9GYZccrbwLnEH5EU7IORE1AdMjvNv9MOmF-LMJP3bdVSrjLPYYF5xwM4DK9TyhCCQqzC-ekvjTOLAh_32nryHWK8JwAyb_MI6OCqU1K3yqyaYU1YRDU1EGgF_He8sWRVKQlJj3n1QMVwL7dLzwcKj-mYesktJQJpS6CKvVL_OAk37lkMDB02NWIuFoBkKUDHILIawNkcCUgSkVKovmsl_w9ukX9DVaEyQ_mbXlm9tGPR9YN_zh55wnh4ZHt6mutaWr-rnpOQLVwSATQJIJx7D_fHvUPJri3cGDFHHPDWLi21Hq5IuARuRBnQhpONTM761hFfoUDZAgZTz331uYmR2G2Pdf1n4v', 'gulu_source_res': 'eyJwX2luIjoiYzI2YmJhYzE0ZTUwZDg3M2I0OGE2ZmEwMGJiODE4NzA5MzQ3N2ZhODY1MmFkYmNjODJkZDcyOWQxOTJhZjhlNCJ9', 'passport_auth_mix_state': 'tnyqfukqvkkpal801swjidl8rjand8ej', 'bd_ticket_guard_client_data_v2': 'eyJyZWVfcHVibGljX2tleSI6IkJGY2Y3TFN6b1ZLZHlCS3RHc2wxd0Q5RmJ2YUgvbVZWMU9hUG5CeEoxTldyVmx5dzg2ejNwMEdMZFRBNzc0NFRIMGtjQ3MrMzFScW5JZzkvM1dSYmNqQT0iLCJ0c19zaWduIjoidHMuMi43ZTkyN2Y5MTE4NmViMjlkZTMxNGE4ZDBhZWEzY2ZjMDlkOWM0MDI0ODBiNTdjMjY4ZjFjNmIxOTQxY2FmOGE1YzRmYmU4N2QyMzE5Y2YwNTMxODYyNGNlZGExNDkxMWNhNDA2ZGVkYmViZWRkYjJlMzBmY2U4ZDRmYTAyNTc1ZCIsInJlcV9jb250ZW50Ijoic2VjX3RzIiwicmVxX3NpZ24iOiJvMnEwY01HcFJYSXlxanZPZkJqUWlTTnVrSmozUEJMdjUyeHFkUUNFUlVJPSIsInNlY190cyI6IiNvdEZlVHBNeCtFWTl3WVlUZTBDVXBTT0NOc0dmOTE0VFhWdkJJeHhLdUVudzQ1djJzU1J4b09GUklkd0YifQ%3D%3D', 'is_dash_user': '1'}
        """
        url = urljoin(self.BASE_URL, "/aweme/v2/web/module/feed/")

        _headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "no-cache",
            "content-length": "0",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://www.douyin.com",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://www.douyin.com/jingxuan",
            "sec-ch-ua": "\"Chromium\";v=\"148\", \"Google Chrome\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "uifid": "b684c79658e5909c916769b2e80c406ed39ea89d6c7cce823581f3f595501a343299ddc8f63e5c7099805529485100fff347690eaf60905dc28912a1c87db414ded6f0e7832221c3899bb71c895fdc4531f7a6d7e90a979eb4c65af0a223c4790ff57319e7f7fc803b5fb8b827fe16f32f23913ee4b64cd461f86bf76130970d6f6f9e432e186a40b7553e9bbb2243df1a7fa2bcc86be296799c12ca63ab4056",
            "x-secsdk-csrf-token": "DOWNGRADE",
        }

        _params = {k: v for k, v in [("device_platform", device_platform), ("aid", aid), ("channel", channel), ("module_id", module_id), ("count", count), ("refresh_index", refresh_index), ("refer_type", refer_type), ("pull_type", pull_type), ("awemePcRecRawData", awemePcRecRawData), ("Seo-Flag", Seo_Flag), ("install_time", install_time), ("is_active_tab", is_active_tab), ("use_lite_type", use_lite_type), ("xigua_user", xigua_user), ("pc_client_type", pc_client_type), ("pc_libra_divert", pc_libra_divert), ("update_version_code", update_version_code), ("support_h265", support_h265), ("support_dash", support_dash), ("version_code", version_code), ("version_name", version_name), ("cookie_enabled", cookie_enabled), ("screen_width", screen_width), ("screen_height", screen_height), ("browser_language", browser_language), ("browser_platform", browser_platform), ("browser_name", browser_name), ("browser_version", browser_version), ("browser_online", browser_online), ("engine_name", engine_name), ("engine_version", engine_version), ("os_name", os_name), ("os_version", os_version), ("cpu_core_num", cpu_core_num), ("device_memory", device_memory), ("platform", platform), ("downlink", downlink), ("effective_type", effective_type), ("round_trip_time", round_trip_time), ("webid", webid), ("uifid", uifid), ("verifyFp", verifyFp), ("fp", fp), ("msToken", msToken), ("a_bogus", a_bogus)] if v is not None}

        _cookies = {
            "enter_pc_once": "1",
            "UIFID_TEMP": "b684c79658e5909c916769b2e80c406ed39ea89d6c7cce823581f3f595501a343299ddc8f63e5c7099805529485100ffbeb77454b5bd416d421f3a2e042f8a0431965d585d2d1c360c1454f9dcee8fd8",
            "s_v_web_id": "verify_mp9exe2i_uAIZq4D2_zJS6_4sLo_957w_7tmoUr0CCIQK",
            "hevc_supported": "true",
            "fpk1": "U2FsdGVkX19GyuqB0GEkhBrz00AmJlCeMI0CcQotl+dK8Kyi+TFg2cbTZUujXdSgIHAP8c0UhJp0bwJfXPmZEw==",
            "fpk2": "b87543ecbc0ba610d9f06f9f2c432a46",
            "passport_csrf_token": "4b4b96abb4181efa09516ca5a0888a35",
            "passport_csrf_token_default": "4b4b96abb4181efa09516ca5a0888a35",
            "bd_ticket_guard_client_web_domain": "2",
            "SEARCH_UN_LOGIN_PV_CURR_DAY": "%7B%22date%22%3A1779005552185%2C%22count%22%3A4%7D",
            "passport_mfa_token": "Cjf7Iw1B4%2FREbavHMSLEvkVZXPrQws0aWnuUeJhprzsdE0aRnkpq%2BokIb%2FZVA3pqJaXx3pJxk15xGkoKPAAAAAAAAAAAAABQbtE8cqnEUbRjifpFzSRYD3z0bLECRta%2Bv9mmJQM0aQmUkTuiPUeOamBFj%2BCpicsAuRCY2JEOGPax0WwgAiIBA2VXr14%3D",
            "d_ticket": "d356df68c311e7e4d0754ab2c3a131b95c8ef",
            "passport_assist_user": "CkHhyOk8fGFPImcjwhcPYQU9XjkedHFnQxayNsAtL4Vu_m_NDHuiLp8DSuue4bn1Ry6px9REgbagqb9uPsfvJHCipxpKCjwAAAAAAAAAAAAAUG4QODXLnHQhTpqmulAeM73mLcyP6vnhKXq3viZPkpuLc8e7_bbvtNXsC5ZDPNfYcBAQ8NiRDhiJr9ZUIAEiAQO0pKYG",
            "n_mh": "IM1tu_RKX6_8-1LWBmD8Se5mr0FbTF-qfxUidJrOYzQ",
            "sid_guard": "295aca0eef73949bcccfa42c8629b697%7C1779005956%7C5184000%7CThu%2C+16-Jul-2026+08%3A19%3A16+GMT",
            "uid_tt": "1feb98ad9138656bbe1138f80b4a23b8",
            "uid_tt_ss": "1feb98ad9138656bbe1138f80b4a23b8",
            "sid_tt": "295aca0eef73949bcccfa42c8629b697",
            "sessionid": "295aca0eef73949bcccfa42c8629b697",
            "sessionid_ss": "295aca0eef73949bcccfa42c8629b697",
            "session_tlb_tag": "sttt%7C4%7CKVrKDu9zlJvMz6Qshim2l__________YxOUsII353fukwsQeRsRTk4xe_0ZzEPX6-VeAA1WxQW0%3D",
            "is_staff_user": "false",
            "has_biz_token": "false",
            "sid_ucp_v1": "1.0.0-KDA4ZDFhZGVlNjc2Yzk2MzEyNmQyMzk3ZDkzMDNkNTA3MjljOWMxMmQKIQiwjoDX4M2KBRCE9KXQBhjvMSAMMK_dgq8GOAdA9AdIBBoCaGwiIDI5NWFjYTBlZWY3Mzk0OWJjY2NmYTQyYzg2MjliNjk3",
            "ssid_ucp_v1": "1.0.0-KDA4ZDFhZGVlNjc2Yzk2MzEyNmQyMzk3ZDkzMDNkNTA3MjljOWMxMmQKIQiwjoDX4M2KBRCE9KXQBhjvMSAMMK_dgq8GOAdA9AdIBBoCaGwiIDI5NWFjYTBlZWY3Mzk0OWJjY2NmYTQyYzg2MjliNjk3",
            "_bd_ticket_crypt_cookie": "63870b4f7df538ee98e1183d90c36da0",
            "__security_mc_1_s_sdk_sign_data_key_web_protect": "e54581f8-40af-a48a",
            "__security_mc_1_s_sdk_cert_key": "67cbbd9c-4354-8732",
            "__security_mc_1_s_sdk_crypt_sdk": "4bed137d-4b7b-b0d3",
            "__security_server_data_status": "1",
            "login_time": "1779005953677",
            "SEARCH_RESULT_LIST_TYPE": "%22single%22",
            "UIFID": "b684c79658e5909c916769b2e80c406ed39ea89d6c7cce823581f3f595501a343299ddc8f63e5c7099805529485100fff347690eaf60905dc28912a1c87db414ded6f0e7832221c3899bb71c895fdc4531f7a6d7e90a979eb4c65af0a223c4790ff57319e7f7fc803b5fb8b827fe16f32f23913ee4b64cd461f86bf76130970d6f6f9e432e186a40b7553e9bbb2243df1a7fa2bcc86be296799c12ca63ab4056",
            "__ac_nonce": "06a23a4f3003e9a12886d",
            "__ac_signature": "_02B4Z6wo00f01kZyaGgAAIDDEvVILWiRXqJGUmzAAPvO47",
            "device_web_cpu_core": "8",
            "device_web_memory_size": "16",
            "architecture": "amd64",
            "is_support_rtm_web_ts": "1",
            "dy_swidth": "1280",
            "dy_sheight": "720",
            "stream_recommend_feed_params": "%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1280%2C%5C%22screen_height%5C%22%3A720%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A8%2C%5C%22device_memory%5C%22%3A16%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A150%7D%22",
            "SelfTabRedDotControl": "%5B%7B%22id%22%3A%227605199502810548287%22%2C%22u%22%3A47%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227401418628932831266%22%2C%22u%22%3A92%2C%22c%22%3A0%7D%5D",
            "bd_ticket_guard_client_data": "eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCRmNmN0xTem9WS2R5Qkt0R3NsMXdEOUZidmFIL21WVjFPYVBuQnhKMU5XclZseXc4NnozcDBHTGRUQTc3NDRUSDBrY0NzKzMxUnFuSWc5LzNXUmJjakE9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D",
            "strategyABtestKey": "%221780720895.462%22",
            "ttwid": "1%7CgwKZI35hMLVFoD13h0F697Po62c7gBbtt0fVNvsqm3U%7C1780720895%7C28d16ceaa614d95d2bd2654757b110d5dbe141bc9a7023258168dfb949f0b538",
            "publish_badge_show_info": "%220%2C0%2C0%2C1780720896880%22",
            "home_can_add_dy_2_desktop": "%221%22",
            "odin_tt": "e2a1a4d33b9811591ad03efa6410b0e1d1b26f3b5a4761cff97702c48203fb590394ad2adf8026ebeebe62eee9d1573c7d53d908fff444d89daff0d52e5338ea",
            "biz_trace_id": "cd91b02e",
            "IsDouyinActive": "true",
            "sdk_source_info": "7e276470716a68645a606960273f276364697660272927676c715a6d6069756077273f276364697660272927666d776a68605a607d71606b766c6a6b5a7666776c7571273f275e58272927666a6b766a69605a696c6061273f27636469766027292762696a6764695a7364776c6467696076273f275e582729277672715a646971273f2763646976602729277f6b5a666475273f2763646976602729276d6a6e5a6b6a716c273f2763646976602729276c6b6f5a7f6367273f27636469766027292771273f2733373d30303d343732353d3234272927676c715a75776a716a666a69273f2763646976602778",
            "bit_env": "_Hao8zgCoGW-IGnRgD52bSZzqyKO8M38HeluyN2hGgNUhOrH_UQBSmhnxiMXZhnNWgOKGq8pfCiBpjorP6mCLlC_qZMbmjhQnnIGG7cf2EOYCDwXyUGqQ8ShnSQQbZVg4Yki1ZzBzOVtXO7gWpl6ge0I7znJeL9J1s9GYZccrbwLnEH5EU7IORE1AdMjvNv9MOmF-LMJP3bdVSrjLPYYF5xwM4DK9TyhCCQqzC-ekvjTOLAh_32nryHWK8JwAyb_MI6OCqU1K3yqyaYU1YRDU1EGgF_He8sWRVKQlJj3n1QMVwL7dLzwcKj-mYesktJQJpS6CKvVL_OAk37lkMDB02NWIuFoBkKUDHILIawNkcCUgSkVKovmsl_w9ukX9DVaEyQ_mbXlm9tGPR9YN_zh55wnh4ZHt6mutaWr-rnpOQLVwSATQJIJx7D_fHvUPJri3cGDFHHPDWLi21Hq5IuARuRBnQhpONTM761hFfoUDZAgZTz331uYmR2G2Pdf1n4v",
            "gulu_source_res": "eyJwX2luIjoiYzI2YmJhYzE0ZTUwZDg3M2I0OGE2ZmEwMGJiODE4NzA5MzQ3N2ZhODY1MmFkYmNjODJkZDcyOWQxOTJhZjhlNCJ9",
            "passport_auth_mix_state": "tnyqfukqvkkpal801swjidl8rjand8ej",
            "bd_ticket_guard_client_data_v2": "eyJyZWVfcHVibGljX2tleSI6IkJGY2Y3TFN6b1ZLZHlCS3RHc2wxd0Q5RmJ2YUgvbVZWMU9hUG5CeEoxTldyVmx5dzg2ejNwMEdMZFRBNzc0NFRIMGtjQ3MrMzFScW5JZzkvM1dSYmNqQT0iLCJ0c19zaWduIjoidHMuMi43ZTkyN2Y5MTE4NmViMjlkZTMxNGE4ZDBhZWEzY2ZjMDlkOWM0MDI0ODBiNTdjMjY4ZjFjNmIxOTQxY2FmOGE1YzRmYmU4N2QyMzE5Y2YwNTMxODYyNGNlZGExNDkxMWNhNDA2ZGVkYmViZWRkYjJlMzBmY2U4ZDRmYTAyNTc1ZCIsInJlcV9jb250ZW50Ijoic2VjX3RzIiwicmVxX3NpZ24iOiJvMnEwY01HcFJYSXlxanZPZkJqUWlTTnVrSmozUEJMdjUyeHFkUUNFUlVJPSIsInNlY190cyI6IiNvdEZlVHBNeCtFWTl3WVlUZTBDVXBTT0NOc0dmOTE0VFhWdkJJeHhLdUVudzQ1djJzU1J4b09GUklkd0YifQ%3D%3D",
            "is_dash_user": "1",
        }

        log.debug("[www_douyin_com_API] POST %s", url)
        return self.request("post", url, headers=_headers, params=_params, cookies=_cookies)



# ============================================================================
# SpiderClient
# ============================================================================

class SpiderClient:
    def __init__(self, config=None):
        self.config = config or SpiderConfig()
        self.api_httpbin_org = httpbin_org_API(self.config)
        self.api_jsonplaceholder_typicode_com = jsonplaceholder_typicode_com_API(self.config)
        self.api_www_douyin_com = www_douyin_com_API(self.config)
    def close(self):
        self.api_httpbin_org.close()
        self.api_jsonplaceholder_typicode_com.close()
        self.api_www_douyin_com.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()


# ============================================================================
# main
# ============================================================================

def main():
    """Run all APIs once for verification. Comment out unwanted calls."""
    config = SpiderConfig()
    # config.PROXY = "http://127.0.0.1:7890"
    # config.IMPERSONATE = "firefox120"
    with SpiderClient(config) as spider:
        # ── GET https://httpbin.org/get ──
        resp = spider.api_httpbin_org.fetch_get(page="1", limit="20", sort="desc")
        log.info("fetch_get -> status=%d", resp.status_code)
        log.info("  body: %s", resp.text)

        # ── GET https://jsonplaceholder.typicode.com/posts/1/comments ──
        resp = spider.api_jsonplaceholder_typicode_com.fetch_posts_comments()
        log.info("fetch_posts_comments -> status=%d", resp.status_code)
        log.info("  body: %s", resp.text)

        # ── POST https://www.douyin.com/aweme/v2/web/module/feed/ ──
        resp = spider.api_www_douyin_com.create_module_feed(device_platform="webapp", aid="6383", channel="channel_pc_web", module_id="3003101", count="20", refresh_index="6", refer_type="10", pull_type="2", awemePcRecRawData="{\"is_xigua_user\":0,\"danmaku_switch_status\":0,\"is_client\":false}", Seo_Flag="0", install_time="1779000437", is_active_tab="false", use_lite_type="0", xigua_user="0", pc_client_type="1", pc_libra_divert="Windows", update_version_code="170400", support_h265="1", support_dash="1", version_code="170400", version_name="17.4.0", cookie_enabled="true", screen_width="1280", screen_height="720", browser_language="zh-CN", browser_platform="Win32", browser_name="Chrome", browser_version="148.0.0.0", browser_online="true", engine_name="Blink", engine_version="148.0.0.0", os_name="Windows", os_version="10", cpu_core_num="8", device_memory="16", platform="PC", downlink="10", effective_type="4g", round_trip_time="150", webid="7640748656416785974", uifid="b684c79658e5909c916769b2e80c406ed39ea89d6c7cce823581f3f595501a343299ddc8f63e5c7099805529485100fff347690eaf60905dc28912a1c87db414ded6f0e7832221c3899bb71c895fdc4531f7a6d7e90a979eb4c65af0a223c4790ff57319e7f7fc803b5fb8b827fe16f32f23913ee4b64cd461f86bf76130970d6f6f9e432e186a40b7553e9bbb2243df1a7fa2bcc86be296799c12ca63ab4056", verifyFp="verify_mp9exe2i_uAIZq4D2_zJS6_4sLo_957w_7tmoUr0CCIQK", fp="verify_mp9exe2i_uAIZq4D2_zJS6_4sLo_957w_7tmoUr0CCIQK", msToken="YXupVmSoGF40lsYnUVU5V7VbLybVSyybMYyTdFTKwWRlsvUDhscPnmrkTXqRs3iTEaAHa71oYhbwqE9KZ1sTAoiU4uKrUIXHZ217lPKwRduWfsttE0sewjt5vrx7pNhjQQvqOJL_RWzouxOpB4AIIlNPDB_ziiqaxMExuWMOikRg", a_bogus="DXsfg7Wid2mnKVMtmK-wS--l67olNPSyUFiObPKTCxFQahlOLSNfFNSObxFPR249bmBTkoVHDVMAbDVcmGXhZCrpFmhfu/XfAU25nXmogqqkYM48LrmmSLDzqwMO8RUqe527N9y5ls076x5lIqOwWOAa95FiRmYpSqeIdFYybDC8pPyTIo2ftrbAwHy=")
        log.info("create_module_feed -> status=%d", resp.status_code)
        log.info("  body: %s", resp.text)

    log.info("All requests completed successfully.")


if __name__ == "__main__":
    main()
