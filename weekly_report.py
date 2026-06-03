# -*- coding: utf-8 -*-
"""Weekly growth digest -> weekly_report.md.
Turns growth.csv + posts.csv into an actionable summary so content can be
iterated toward what works (the core of 'auto-virality': find winners, double
down). Runs in GitHub Actions weekly. No insights scope needed."""
import os, csv, datetime
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

def read(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return list(csv.DictReader(f))

growth = read(os.path.join(HERE, "growth.csv"))
posts = read(os.path.join(HERE, "posts.csv"))
today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

# --- followers ---
foll_now = int(growth[-1]["followers"]) if growth else 0
# value ~7 days ago (or earliest)
prior = growth[max(0, len(growth) - 8)] if growth else None
foll_prior = int(prior["followers"]) if prior else foll_now
delta7 = foll_now - foll_prior

# --- per-post latest snapshot + engagement ranking ---
latest = {}
for r in posts:
    latest[r["media_id"]] = r  # later rows overwrite -> newest
def eng(r):
    try:
        return int(r["likes"] or 0) + int(r["comments"] or 0)
    except ValueError:
        return 0
ranked = sorted(latest.values(), key=eng, reverse=True)

# reel vs carousel average engagement
by_type = defaultdict(list)
for r in latest.values():
    by_type[r["media_type"]].append(eng(r))
def avg(xs):
    return round(sum(xs) / len(xs), 1) if xs else 0

lines = []
lines.append(f"# Naviris IG 週次レポート ({today} UTC)\n")
lines.append(f"## フォロワー\n- 現在: **{foll_now}**\n- 直近7日の増減: **{'+' if delta7>=0 else ''}{delta7}**\n")
lines.append("## 投稿パフォーマンス (いいね+コメント順)\n")
lines.append("| 順位 | 種別 | エンゲージ | リンク |\n|---|---|---|---|")
for i, r in enumerate(ranked[:8], 1):
    lines.append(f"| {i} | {r['media_type']} | {eng(r)} | {r['permalink']} |")
lines.append("")
lines.append("## タイプ別 平均エンゲージ\n")
for t, xs in by_type.items():
    lines.append(f"- {t}: 平均 {avg(xs)}（{len(xs)}件）")
lines.append("")
# simple auto-recommendation
reel_avg = avg(by_type.get("VIDEO", []))
car_avg = avg(by_type.get("CAROUSEL_ALBUM", []) + by_type.get("IMAGE", []))
rec = []
if reel_avg >= car_avg:
    rec.append(f"リール(平均{reel_avg}) ≥ カルーセル(平均{car_avg}) → **リール比率を上げる**。")
else:
    rec.append(f"カルーセル(平均{car_avg}) > リール(平均{reel_avg}) → カルーセルの切り口を強化。")
if ranked:
    rec.append(f"最も伸びた投稿: {ranked[0]['permalink']}（{ranked[0]['media_type']}）→ **このフック/テーマの派生を増産**。")
if delta7 <= 0:
    rec.append("フォロワー増減が鈍い → フック(最初の3秒)を短く強く、保存/シェアCTAを前倒し。")
lines.append("## 次アクション(自動提案)\n" + "\n".join(f"- {r}" for r in rec) + "\n")

with open(os.path.join(HERE, "weekly_report.md"), "w") as f:
    f.write("\n".join(lines))
print(f"followers={foll_now} delta7={delta7} ranked={len(ranked)} -> weekly_report.md")
