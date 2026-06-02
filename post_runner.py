# -*- coding: utf-8 -*-
"""Runs inside GitHub Actions (cloud). Publishes the next pending post.

Media files are ALREADY committed in this repo under media/<subdir>/, so we just
build their public raw URLs and call the Instagram API. Token comes from env
secrets (IG_ACCESS_TOKEN, IG_USER_ID). On success, marks the item posted in
queue.json (the workflow commits that change back).

Set DRY_RUN=1 to create the media container without publishing (safe test).
"""
import os, sys, json, datetime
import publisher

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, "queue.json")
OWNER, REPO, BRANCH = "kura-naviris", "naviris-ig-media", "main"
RAW = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}"
DRY = os.environ.get("DRY_RUN") == "1"

def log(m): print(f"{datetime.datetime.now().isoformat(timespec='seconds')} {m}", flush=True)

def main():
    with open(QUEUE) as f:
        q = json.load(f)
    pending = [p for p in q["posts"] if not p.get("posted")]
    if not pending:
        log("no pending posts — nothing to do")
        return 0
    post = pending[0]
    pid, ptype = post["id"], post["type"]
    for rel in post["files"]:
        if not os.path.exists(os.path.join(HERE, rel)):
            log(f"ERROR [{pid}] missing in repo: {rel}")
            return 1
    urls = [f"{RAW}/{rel}" for rel in post["files"]]
    cap = post.get("caption", "")
    log(f"START [{pid}] type={ptype} dry={DRY} media={len(urls)}")

    if DRY:
        c = publisher._cfg(); t = c["access_token"]; ig = c["ig_user_id"]
        r = publisher._post(f"{ig}/media", {"image_url": urls[0], "caption": cap,
                                            "access_token": t})
        log(f"  DRY container only (not published): {r}")
        return 0

    if ptype == "carousel":
        res = publisher.post_carousel(urls, cap)
    elif ptype == "image":
        res = publisher.post_image(urls[0], cap)
    elif ptype == "reel":
        res = publisher.post_reel(urls[0], cap, cover_url=post.get("cover_url"))
    else:
        log(f"ERROR [{pid}] unknown type {ptype}"); return 1

    post["posted"] = True
    post["published_id"] = res.get("id")
    post["published_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    with open(QUEUE, "w") as f:
        json.dump(q, f, indent=2, ensure_ascii=False)
    left = sum(1 for p in q["posts"] if not p.get("posted"))
    log(f"DONE [{pid}] published id={res.get('id')} | {left} left")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"FATAL {type(e).__name__}: {e}")
        sys.exit(1)
