# -*- coding: utf-8 -*-
"""Append a daily snapshot of follower/media counts to growth.csv.
Runs in GitHub Actions (token from env secrets). Lets us obsess over the
follower number and review week-over-week. No extra permission needed
(followers_count is available with instagram_business_basic)."""
import os, csv, json, datetime, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "growth.csv")
TOK = os.environ["IG_ACCESS_TOKEN"]
UID = os.environ["IG_USER_ID"]

url = "https://graph.instagram.com/v23.0/" + UID + "?" + urllib.parse.urlencode(
    {"fields": "followers_count,media_count,username", "access_token": TOK})
with urllib.request.urlopen(url) as r:
    d = json.loads(r.read())

date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
row = [date, d.get("followers_count", ""), d.get("media_count", ""), d.get("username", "")]

new = not os.path.exists(CSV)
with open(CSV, "a", newline="") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["date_utc", "followers", "media_count", "username"])
    w.writerow(row)
print("tracked:", row)
