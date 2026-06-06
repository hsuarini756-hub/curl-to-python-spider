# -*- coding: utf-8 -*-
"""curl_parse.py -- parse curls.txt -> result_spider.txt

Supports: bash/zsh curl + Windows cmd ^ escape + multi-line ^ continuation
Usage:   python curl_parse.py [curls.txt] [output]
"""

import shlex, re, json, os, sys
from collections import OrderedDict
from urllib.parse import urlparse, parse_qs

# ── Windows cmd caret-escape ──────────────────────────────────────────────

def unescape_cmd_caret(line: str) -> str:
    """Remove Windows cmd ^ escapes and Chrome DevTools URL percent-encoding artifacts."""
    if "^" not in line:
        return line

    # Step 1: char-by-char scan
    result = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "^" and i + 1 < len(line):
            nxt = line[i + 1]
            if nxt == "^":
                result.append("^"); i += 2; continue
            if not nxt.isalnum() and nxt not in (" ", "\t", "\r", "\n"):
                result.append(nxt); i += 2; continue
            result.append(ch); i += 1; continue
        result.append(ch); i += 1

    line2 = "".join(result)

    # Step 2: URL percent-encoding fixup
    # Chrome DevTools cmd inserts ^ before % in URL-encoded chars: %^%2F / ^%^5B / ^%7B
    line2 = re.sub(r'\^%([0-9A-Fa-f]{2})', r'%\1', line2)
    line2 = re.sub(r'%\^%([0-9A-Fa-f]{2})', r'%\1', line2)
    line2 = re.sub(r'\^%\^([0-9A-Fa-f]{2})', r'%\1', line2)
    line2 = re.sub(r'\^%', '%', line2)
    line2 = re.sub(r'\^(?!$)', '', line2)

    return line2


def join_cmd_continuations(raw_text: str) -> list:
    """Join cmd continuation lines (ending with ^)."""
    lines = []
    buf = ""
    for raw in raw_text.splitlines(keepends=False):
        s = raw.rstrip("\n\r")
        if s.rstrip().endswith("^") and not s.rstrip().endswith("^^"):
            buf += s.rstrip()[:-1] + " "
        else:
            buf += s; lines.append(buf); buf = ""
    if buf: lines.append(buf)
    return lines


# ── curl parser ───────────────────────────────────────────────────────────

def parse_curl_line(line: str) -> dict:
    """Parse one curl command -> structured dict."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    line = unescape_cmd_caret(line)
    try:
        tokens = shlex.split(line, posix=True)
    except ValueError:
        tokens = shlex.split(line + "'", posix=True)

    r = OrderedDict(method="GET", url="", headers=OrderedDict(),
                    params=OrderedDict(), data=None, cookies=OrderedDict())
    i, mf = 0, False
    while i < len(tokens):
        t = tokens[i]
        if t == "curl": i += 1; continue
        if t in ("-X", "--request"):
            i += 1
            if i < len(tokens): r["method"] = tokens[i].upper(); mf = True
            i += 1; continue
        if t in ("-H", "--header"):
            i += 1
            if i < len(tokens):
                hl = tokens[i]
                if ":" in hl:
                    k, v = hl.split(":", 1)
                    kl = k.strip().lower()
                    if kl not in ("user-agent", "cookie"):
                        r["headers"][k.strip()] = v.strip()
            i += 1; continue
        if t in ("-d", "--data", "--data-raw", "--data-binary"):
            i += 1
            if i < len(tokens): r["data"] = tokens[i]
            if not mf: r["method"] = "POST"
            i += 1; continue
        if t in ("-b", "--cookie"):
            i += 1
            if i < len(tokens):
                cs = tokens[i]
                if "=" in cs:
                    for p in cs.split(";"):
                        p = p.strip()
                        if "=" in p:
                            k, v = p.split("=", 1)
                            r["cookies"][k.strip()] = v.strip()
            i += 1; continue
        if t in ("-G", "--get"): r["method"] = "GET"; i += 1; continue
        if t in ("--compressed","-k","--insecure","--silent","-s","-L","--location","-v","--verbose","--http1.1","--http2"): i += 1; continue
        if t.startswith(("http://", "https://")): r["url"] = t; i += 1; continue
        if not t.startswith("-") and not r["url"]: r["url"] = t
        i += 1

    if "?" in r["url"]:
        base, qs = r["url"].split("?", 1)
        r["url"] = base
        for k, vlist in parse_qs(qs).items():
            r["params"][k] = vlist[0] if len(vlist) == 1 else vlist
    return r


def sanitize_param(key: str) -> str:
    """Sanitize a URL query parameter key into a valid Python identifier."""
    # Replace non-alnum chars (except _) with underscore
    key = re.sub(r"[^a-zA-Z0-9_]", "_", key)
    # Must not start with digit
    if key[0].isdigit():
        key = "_" + key
    return key


def guess_method_name(parsed: dict) -> str:
    path = urlparse(parsed["url"]).path.strip("/")
    method = parsed["method"].lower()
    segs = [s for s in path.split("/") if s and not s.isdigit()]
    if not segs: segs = ["index"]
    res = "_".join(segs[-2:]) if len(segs) >= 2 else segs[-1]
    res = re.sub(r"[^a-zA-Z0-9_]", "_", res)
    pfx = {"get":"fetch","post":"create","put":"update","delete":"delete","patch":"patch"}.get(method, method)
    name = f"{pfx}_{res}" if res != "index" else pfx
    return re.sub(r"_+", "_", name).strip("_")


# ── Content-Type classification ──────────────────────────────────────────

def classify_body(headers: dict, data: str) -> str:
    """Classify request body type: 'json' | 'form' | 'text' | None."""
    if not data:
        return None
    ct = ""
    for k, v in headers.items():
        if k.lower() == "content-type":
            ct = v.lower(); break
    if "json" in ct:
        return "json"
    if "x-www-form-urlencoded" in ct or "form" in ct:
        return "form"
    # Try to detect by content
    stripped = data.strip()
    if stripped.startswith(("{", "[")):
        try:
            json.loads(stripped)
            return "json"
        except:
            pass
    if "=" in stripped and "{" not in stripped:
        return "form"
    return "text"


# ── Safe Python string literal ────────────────────────────────────────────

def py_str(s: str) -> str:
    """Escape for Python double-quoted string literal."""
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return s


# ── Spider template ───────────────────────────────────────────────────────

SPIDER_TPL = r'''# -*- coding: utf-8 -*-
"""
Auto-generated Spider -- __CMD_COUNT__ curl(s) / __GROUP_COUNT__ API group(s)
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
__API_CLASSES__


# ============================================================================
# SpiderClient
# ============================================================================

class SpiderClient:
    def __init__(self, config=None):
        self.config = config or SpiderConfig()
__CLIENT_INIT__
    def close(self):
__CLIENT_CLOSE__
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
__MAIN_EXAMPLES__
    log.info("All requests completed successfully.")


if __name__ == "__main__":
    main()
'''


# ── Code generation ───────────────────────────────────────────────────────

def gen_api_class(host_key: str, apis: list) -> str:
    cn = f"{host_key.replace('.','_').replace('-','_')}_API"
    parsed = urlparse(apis[0]["url"])
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    out = [
        f"class {cn}(BaseSpider):",
        f'    """API -- {base_url}"""',
        f'    BASE_URL = "{base_url}"',
        "",
    ]
    used = set()
    for api in apis:
        path = urlparse(api["url"]).path
        mn = guess_method_name(api)
        orig = mn; c2 = 2
        while mn in used: mn = f"{orig}_{c2}"; c2 += 1
        used.add(mn)
        hm = api["method"].lower()

        # Method params from query string
        raw_param_keys = list(api["params"].keys())
        param_keys = [sanitize_param(k) for k in raw_param_keys]
        pps = ["self"] + [f"{k}=None" for k in param_keys]

        # Body handling: detect content-type and decide json= / data= / nothing
        body_type = classify_body(api["headers"], api.get("data", "") or "")
        body_param = ""
        if body_type == "json":
            pps.append("data: dict = None")
            body_param = "json=data"
        elif body_type == "form":
            pps.append("data: str = None")
            body_param = "data=data"
        elif body_type == "text":
            pps.append("data: str = None")
            body_param = "data=data"

        ps = ", ".join(pps)

        # Docstring
        dl = [f'        """', f"        {api['method']} {api['url']}"]
        if api["headers"]:
            dl.append(""); dl.append("        Headers:")
            for k, v in api["headers"].items(): dl.append(f"            {k}: {v}")
        if api["params"]: dl.append(f"        Params: {dict(api['params'])}")
        if api["data"]: dl.append(f"        Body: {api['data'][:120]}")
        if api["cookies"]: dl.append(f"        Cookies: {dict(api['cookies'])}")
        dl.append('        """')

        # Method body
        bl = [f'        url = urljoin(self.BASE_URL, "{path}")', ""]
        if api["headers"]:
            bl.append("        _headers = {")
            for k, v in api["headers"].items():
                bl.append(f'            "{k}": "{py_str(v)}",')
            bl.append("        }")
        else:
            bl.append("        _headers = {}")
        bl.append("")

        if api["params"]:
            pi_pairs = ", ".join([f'("{raw_param_keys[i]}", {param_keys[i]})' for i in range(len(param_keys))])
            bl.append(f"        _params = {{k: v for k, v in [{pi_pairs}] if v is not None}}")
        else:
            bl.append("        _params = {}")
        bl.append("")

        if api["cookies"]:
            bl.append("        _cookies = {")
            for k, v in api["cookies"].items():
                bl.append(f'            "{k}": "{py_str(v)}",')
            bl.append("        }")
        else:
            bl.append("        _cookies = {}")
        bl.append("")

        bl.append(f'        log.debug("[{cn}] {hm.upper()} %s", url)')
        ckw = ["headers=_headers", "params=_params", "cookies=_cookies"]
        if body_param: ckw.append(body_param)
        bl.append(f'        return self.request("{hm}", url, {", ".join(ckw)})')

        out.append(f"    def {mn}({ps}):")
        out.extend(dl); out.extend(bl); out.append("")

    return "\n".join(out)


def generate(parsed: list, out_path: str):
    groups = OrderedDict()
    for cmd in parsed:
        host = urlparse(cmd["url"]).netloc.replace(".", "_").replace("-", "_")
        if not host: continue
        groups.setdefault(host, []).append(cmd)

    acls = []; c_init = []; c_close = []; mex = []
    for hk, aps in groups.items():
        acls.append(gen_api_class(hk, aps))
        an = f"api_{hk}"; cn = f"{hk}_API"
        c_init.append(f"        self.{an} = {cn}(self.config)")
        c_close.append(f"        self.{an}.close()")

        # Build runnable example for the first endpoint
        first = aps[0]
        fm = guess_method_name(first)
        mex.append(f"        # ── {first['method']} {first['url']} ──")

        # Build kwargs
        kws = []
        if first.get("params"):
            for k, v in first["params"].items():
                val = v if isinstance(v, str) else v[0]
                safe_k = sanitize_param(k)
                kws.append(f'{safe_k}="{py_str(val)}"')
        if first.get("data"):
            body_type = classify_body(first["headers"], first["data"])
            if body_type == "json":
                kws.append(f"data={first['data']}")
            else:
                kws.append(f'data="{py_str(first["data"])}"')

        call = f"spider.{an}.{fm}({', '.join(kws)})"
        mex.append(f"        resp = {call}")
        mex.append(f'        log.info("{fm} -> status=%d", resp.status_code)')
        mex.append(f'        log.info("  body: %s", resp.text)')
        mex.append("")

    result = SPIDER_TPL
    result = result.replace("__CMD_COUNT__", str(len(parsed)))
    result = result.replace("__GROUP_COUNT__", str(len(groups)))
    result = result.replace("__API_CLASSES__", "\n\n".join(acls))
    result = result.replace("__CLIENT_INIT__", "\n".join(c_init) if c_init else "        pass")
    result = result.replace("__CLIENT_CLOSE__", "\n".join(c_close) if c_close else "        pass")
    result = result.replace("__MAIN_EXAMPLES__", "\n".join(mex) if mex else "        pass")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\nGenerated: {out_path}")
    print(f"  Commands: {len(parsed)}  Groups: {len(groups)}")
    for hk, aps in groups.items():
        print(f"    [{hk}] {len(aps)} endpoint(s)")


# ── main ──────────────────────────────────────────────────────────────────

def main():
    bd = os.path.dirname(os.path.abspath(__file__))
    inp = os.environ.get("CURLS_INPUT", os.path.join(bd, "curls.txt"))
    outp = os.environ.get("SPIDER_OUTPUT", os.path.join(bd, "result_spider.txt"))
    if len(sys.argv) >= 2: inp = sys.argv[1]
    if len(sys.argv) >= 3: outp = sys.argv[2]
    inp = os.path.abspath(inp); outp = os.path.abspath(outp)

    if not os.path.exists(inp):
        print(f"Error: {inp} not found"); sys.exit(1)

    raw_text = open(inp, encoding="utf-8").read()
    joined = join_cmd_continuations(raw_text)

    parsed = []
    for ln, line in enumerate(joined, 1):
        line = line.strip()
        if not line or line.startswith("#"): continue
        try:
            r = parse_curl_line(line)
            if r and r["url"]:
                parsed.append(r)
                print(f"  [{ln}] {r['method']:6s} {r['url']}")
            else:
                print(f"  [{ln}] SKIP")
        except Exception as e:
            print(f"  [{ln}] ERROR: {e}")

    if not parsed:
        print("Error: no valid curl commands"); sys.exit(1)

    print(f"\nParsed {len(parsed)} command(s). Generating...\n")
    generate(parsed, outp)


if __name__ == "__main__":
    main()