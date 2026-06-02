# -*- coding: utf-8 -*-
"""Daily snapshot for growth review.
- growth.csv : account-level followers + media_count (the headline number)
- posts.csv  : per-post likes/comments/permalink time-series
Runs in GitHub Actions (token from env secrets). No insights scope needed
(reach/saves/shares require Meta app review — see notes). like_count,
comments_count and permalink are available with instagram_business_basic."""
import os, csv, json, datetime, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TOK = os.environ["IG_ACCESS_TOKEN"]
UID = os.environ["IG_USER_ID"]
B = "https://graph.instagram.com/v23.0"
DATE = datetime.datetime.utcnow().strftime("%Y-%m-%d")

def g(path, params):
    params["access_token"] = TOK
    with urllib.request.urlopen(B + "/" + path + "?" + urllib.parse.urlencode(params)) as r:
        return json.loads(r.read())

# account-level
acct = g(UID, {"fields": "followers_count,media_count,username"})
gpath = os.path.join(HERE, "growth.csv")
new = not os.path.exists(gpath)
with open(gpath, "a", newline="") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["date_utc", "followers", "media_count", "username"])
    w.writerow([DATE, acct.get("followers_count", ""), acct.get("media_count", ""),
                acct.get("username", "")])
print("followers:", acct.get("followers_count"), "media:", acct.get("media_count"))

# per-post
media = g("me/media", {"fields": "id,media_type,like_count,comments_count,permalink,timestamp",
                       "limit": "50"})
ppath = os.path.join(HERE, "posts.csv")
newp = not os.path.exists(ppath)
with open(ppath, "a", newline="") as f:
    w = csv.writer(f)
    if newp:
        w.writerow(["date_utc", "media_id", "media_type", "likes", "comments",
                    "permalink", "posted_at"])
    for m in media.get("data", []):
        w.writerow([DATE, m["id"], m.get("media_type", ""), m.get("like_count", ""),
                    m.get("comments_count", ""), m.get("permalink", ""), m.get("timestamp", "")])
print("logged", len(media.get("data", [])), "posts")
