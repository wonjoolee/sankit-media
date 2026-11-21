"""쓰레드 토큰 받기 — 대표님 컴퓨터에서 한 번만 돌리면 됩니다.

쓰레드는 인스타처럼 '토큰 생성' 버튼이 없습니다. 브라우저로 한 번 승인하고
거기서 나온 code 를 토큰으로 바꾸는 절차가 필요합니다. 그 두 단계를 이 파일이 합니다.

쓰는 법
  1) 승인 주소 만들기
     python3 pipeline/threads_token.py url <THREADS_APP_ID> <REDIRECT_URI>
     → 나온 주소를 브라우저에 붙여 넣고 승인하면 주소창이 ...?code=XXXX#_ 로 바뀝니다.

  2) 그 주소를 통째로 복사해서
     python3 pipeline/threads_token.py token <THREADS_APP_ID> <THREADS_APP_SECRET> <REDIRECT_URI> "<붙여넣은 주소>"
     → 60일짜리 장기 토큰과 사용자 ID가 나옵니다.

  3) 나온 토큰을 GitHub Secrets 의 TH_TOKEN 에 넣으면 끝입니다.

토큰은 비밀번호와 같습니다. 채팅·메일·커밋에 붙여 넣지 마세요.
60일마다 갱신:
  python3 pipeline/threads_token.py refresh <현재 토큰>
"""
import sys, json, urllib.parse, urllib.request, urllib.error

AUTH = "https://threads.com/oauth/authorize"
G = "https://graph.threads.com"
SCOPE = "threads_basic,threads_content_publish"


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit("실패: " + e.read().decode("utf-8", "replace"))


def post(url, data):
    body = urllib.parse.urlencode(data).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit("실패: " + e.read().decode("utf-8", "replace"))


def code_from(s):
    """승인 후 주소창 전체를 붙여 넣어도 되고, code 값만 넣어도 됩니다."""
    if "code=" in s:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(s).query)
        return q.get("code", [""])[0].split("#")[0]
    return s.split("#")[0]


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return

    if a[0] == "url":
        app_id, redirect = a[1], a[2]
        q = urllib.parse.urlencode({"client_id": app_id, "redirect_uri": redirect,
                                    "scope": SCOPE, "response_type": "code"})
        print("\n아래 주소를 브라우저에 붙여 넣고 승인하세요:\n")
        print(AUTH + "?" + q)
        print("\n승인 후 주소창에 보이는 주소를 통째로 복사해 두세요. (code=... 가 들어 있습니다)\n")

    elif a[0] == "token":
        app_id, secret, redirect, raw = a[1], a[2], a[3], a[4]
        code = code_from(raw)
        if not code:
            raise SystemExit("code 를 찾지 못했습니다. 승인 후 주소를 통째로 붙여 넣으세요.")
        short = post(G + "/oauth/access_token",
                     {"client_id": app_id, "client_secret": secret, "code": code,
                      "grant_type": "authorization_code", "redirect_uri": redirect})
        if "access_token" not in short:
            raise SystemExit("단기 토큰 실패: " + json.dumps(short, ensure_ascii=False))
        uid = short.get("user_id", "")
        long_ = get(G + "/access_token?" + urllib.parse.urlencode(
            {"grant_type": "th_exchange_token", "client_secret": secret,
             "access_token": short["access_token"]}))
        tok = long_.get("access_token")
        if not tok:
            raise SystemExit("장기 토큰 실패: " + json.dumps(long_, ensure_ascii=False))
        days = int(long_.get("expires_in", 0)) // 86400
        print("\n=== GitHub Secrets 에 넣을 값 ===\n")
        print("TH_USER_ID :", uid)
        print("TH_TOKEN   :", tok)
        print(f"\n유효기간 약 {days}일. 만료 전에 refresh 로 갱신하세요.")
        print("이 값은 비밀번호와 같습니다. 채팅·메일·커밋에 붙여 넣지 마세요.\n")

    elif a[0] == "refresh":
        r = get(G + "/refresh_access_token?" + urllib.parse.urlencode(
            {"grant_type": "th_refresh_token", "access_token": a[1]}))
        if "access_token" not in r:
            raise SystemExit("갱신 실패: " + json.dumps(r, ensure_ascii=False))
        print("TH_TOKEN :", r["access_token"])
        print("유효기간 약", int(r.get("expires_in", 0)) // 86400, "일")

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
