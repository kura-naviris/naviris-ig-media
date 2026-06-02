# -*- coding: utf-8 -*-
"""Naviris Instagram auto-publisher via the Instagram API (Instagram Login flavor).
Zero-touch posting of carousels and reels using a long-lived Instagram token.

Endpoint base: https://graph.instagram.com  (NOT graph.facebook.com)
No Facebook Page required. Token obtained via Instagram Business Login.

Config: naviris-instagram/.secrets/ig.json  (keep private)
  { "ig_user_id": "26184...", "access_token": "IGAA...", "api": "instagram_login" }

Media must be reachable at PUBLIC https URLs (Instagram fetches them server-side).
Long-lived tokens last 60 days; refresh with refresh_token() before expiry.
"""
import os, json, time, urllib.parse, urllib.request

GRAPH = "https://graph.instagram.com/v23.0"
HERE = os.path.dirname(__file__)
CFG_PATH = os.path.join(HERE, ".secrets", "ig.json")

def _cfg():
    # In CI (GitHub Actions) read from env secrets; locally read .secrets/ig.json.
    tok = os.environ.get("IG_ACCESS_TOKEN")
    uid = os.environ.get("IG_USER_ID")
    if tok and uid:
        return {"access_token": tok, "ig_user_id": uid}
    with open(CFG_PATH) as f:
        return json.load(f)

def _post(path, params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{GRAPH}/{path}", data=data, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def _get(path, params):
    url = f"{GRAPH}/{path}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url) as r:
        return json.loads(r.read())

def _publish(token, ig_id, creation_id):
    return _post(f"{ig_id}/media_publish",
                 {"creation_id": creation_id, "access_token": token})

def post_carousel(image_urls, caption):
    """image_urls: list of public https PNG/JPG URLs (2-10). Returns published id."""
    c = _cfg(); token = c["access_token"]; ig = c["ig_user_id"]
    children = []
    for u in image_urls:
        res = _post(f"{ig}/media", {"image_url": u, "is_carousel_item": "true",
                                    "access_token": token})
        children.append(res["id"])
    cont = _post(f"{ig}/media", {"media_type": "CAROUSEL",
                                 "children": ",".join(children),
                                 "caption": caption, "access_token": token})
    time.sleep(3)
    return _publish(token, ig, cont["id"])

def post_image(image_url, caption):
    """Single image post. image_url: public https PNG/JPG. Returns published id."""
    c = _cfg(); token = c["access_token"]; ig = c["ig_user_id"]
    cont = _post(f"{ig}/media", {"image_url": image_url, "caption": caption,
                                 "access_token": token})
    time.sleep(3)
    return _publish(token, ig, cont["id"])

def post_reel(video_url, caption, cover_url=None, share_to_feed=True, timeout=300):
    """video_url: public https mp4 (vertical 9:16). Polls until FINISHED then publishes."""
    c = _cfg(); token = c["access_token"]; ig = c["ig_user_id"]
    params = {"media_type": "REELS", "video_url": video_url, "caption": caption,
              "share_to_feed": "true" if share_to_feed else "false",
              "access_token": token}
    if cover_url:
        params["cover_url"] = cover_url
    cont = _post(f"{ig}/media", params)
    cid = cont["id"]
    waited = 0
    while waited < timeout:
        st = _get(cid, {"fields": "status_code", "access_token": token})
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") == "ERROR":
            raise RuntimeError(f"Reel processing error: {st}")
        time.sleep(5); waited += 5
    return _publish(token, ig, cid)

def whoami():
    """Sanity check: returns the IG account this token controls."""
    c = _cfg(); token = c["access_token"]; ig = c["ig_user_id"]
    return _get(ig, {"fields": "user_id,username,account_type,media_count,followers_count",
                     "access_token": token})

def refresh_token():
    """Refresh the long-lived token (extends another 60 days). Updates ig.json.
    Run roughly monthly via cron; no Instagram login or app secret needed."""
    c = _cfg(); token = c["access_token"]
    r = _get("refresh_access_token", {"grant_type": "ig_refresh_token",
                                      "access_token": token})
    c["access_token"] = r["access_token"]
    with open(CFG_PATH, "w") as f:
        json.dump(c, f, indent=2, ensure_ascii=False)
    return {"refreshed": True, "expires_in_days": round(r.get("expires_in", 0) / 86400, 1)}

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "whoami":
        print(json.dumps(whoami(), ensure_ascii=False, indent=2))
    elif cmd == "refresh":
        print(json.dumps(refresh_token(), ensure_ascii=False, indent=2))
    else:
        print("usage: python3 publisher.py [whoami|refresh]")
