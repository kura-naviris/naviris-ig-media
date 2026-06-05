# -*- coding: utf-8 -*-
"""Cloud content factory — runs in GitHub Actions (no Mac needed).
Reads weekly_report.md to bias reel:carousel ratio, picks unused templates from
BANK (avoid repeats via factory_state.json, recycle when exhausted), renders with
the bundled Noto font (engine/reels) + baked BGM, appends to queue.json.
The workflow commits the result. Posting/tracking/refresh all run in the cloud,
so the Mac can stay closed."""
import os, sys, json, shutil, random, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import build as build_carousel
from reels import build_reel, ACCENT

HERE = os.path.dirname(os.path.abspath(__file__))
BGM = os.path.join(HERE, "assets", "bgm.mp3")
STATE = os.path.join(HERE, "factory_state.json")
QUEUE = os.path.join(HERE, "queue.json")
WORK = os.path.join(HERE, "_work")  # temp render dir
PER_WEEK = int(os.environ.get("FACTORY_PER_WEEK", "5"))
LINE = "プロフのリンク → LINEで応募"
TAGS = ("#就活 #就活生 #27卒 #28卒 #長期インターン #営業 #大学生と繋がりたい "
        "#ガクチカ #キャリア #第二新卒 #フリーター #営業インターン #関東 #自己成長")

def cap(hook, body):
    return f"{hook}\n\n{body}\n\n📍関東／光回線の営業インターン（長期・歩合・学歴年齢不問）\n💬応募はプロフィールのLINEから👆\n🔖役に立ったら保存＆シェア\n\n{TAGS}"

BANK_REELS = [
 {"id":"r_men1","caption":cap("面接で落ちる人の“口グセ”、知ってる?","「ガクチカが無い」と言う人ほど、行動してないだけ。現場に出れば話せる経験は3週間で作れる。"),
  "beats":[{"kicker":"NAVIRIS","text":"面接で落ちる人の\n“口グセ”知ってる?","size":80,"dur":2.6},
    {"text":"「ガクチカが\n無いんです」","size":92,"dur":2.0},{"text":"それ、経験が無い\nんじゃない。","size":80,"dur":2.0},
    {"text":"“動いてない”だけ。","size":96,"dur":2.0},{"text":"現場に出れば話せる\n経験は3週間で作れる。","size":68,"dur":2.4},
    {"text":"学歴/年齢 不問\n関東の営業インターン","size":66,"color":ACCENT,"dur":2.2},{"kicker":"ENTRY","text":"保存して、就活前に\nプロフのLINEへ。","size":72,"dur":2.4}]},
 {"id":"r_fear1","caption":cap("「断られるの怖い」が一瞬で消える話。","断られても死なない。むしろ“断られ慣れ”は面接でも商談でも一生効く最強スキル。20代で慣れた者勝ち。"),
  "beats":[{"kicker":"NAVIRIS","text":"「断られるの怖い」\nが消える話。","size":80,"dur":2.6},
    {"text":"断られても、\n死なない。","size":96,"dur":2.0},{"text":"むしろ“断られ慣れ”は","size":80,"dur":1.8},
    {"text":"面接も商談も\n一生効く最強スキル。","size":74,"dur":2.2},{"text":"20代で慣れた者勝ち。","size":84,"dur":2.0},
    {"text":"関東・光回線の\n営業インターン","size":70,"color":ACCENT,"dur":2.2},{"kicker":"ENTRY","text":"応募はプロフの\nLINEから。","size":84,"dur":2.2}]},
 {"id":"r_ceo1","caption":cap("20歳で起業して分かった、たった1つのこと。","「若い・無名」は言い訳にならない。年齢でも学歴でもなく、“動いた回数”だけが自分を変える。"),
  "beats":[{"kicker":"NAVIRIS","text":"20歳で起業して\n分かった1つのこと","size":78,"dur":2.6},
    {"text":"「若い」「無名」は","size":86,"dur":1.8},{"text":"言い訳にならない。","size":90,"dur":2.0},
    {"text":"年齢でも学歴でもなく","size":78,"dur":2.0},{"text":"“動いた回数”だけが\n自分を変える。","size":74,"dur":2.4},
    {"text":"一緒に動く仲間募集。\n関東・営業インターン","size":64,"color":ACCENT,"dur":2.2},{"kicker":"ENTRY","text":"プロフのLINEへ。","size":86,"dur":2.2}]},
 {"id":"r_uni1","caption":cap("大学名が就活で意味を失う“瞬間”、教える。","エントリーシートまでは効く。でも面接で問われるのは「何ができるか」。そこから先は学歴ゼロ円。"),
  "beats":[{"kicker":"NAVIRIS","text":"大学名が意味を失う\n“瞬間”教える。","size":78,"dur":2.6},
    {"text":"ESまでは効く。","size":92,"dur":1.8},{"text":"でも面接で問われるのは","size":76,"dur":2.0},
    {"text":"「何ができるか」。","size":88,"dur":2.0},{"text":"そこから先は\n学歴ゼロ円。","size":82,"dur":2.2},
    {"text":"“できる”を作る\n関東・営業インターン","size":66,"color":ACCENT,"dur":2.2},{"kicker":"ENTRY","text":"保存→プロフのLINE。","size":80,"dur":2.2}]},
 {"id":"r_real1","caption":cap("営業インターン、最初の1ヶ月のリアル。","盛らずに言う。最初は断られる。でも型を覚えれば数字はついてくる。歩合だから、やった分だけ返る。"),
  "beats":[{"kicker":"NAVIRIS","text":"営業インターン\n最初の1ヶ月のリアル","size":78,"dur":2.6},
    {"text":"盛らずに言う。","size":92,"dur":1.6},{"text":"最初は、断られる。","size":88,"dur":2.0},
    {"text":"でも型を覚えれば\n数字はついてくる。","size":74,"dur":2.4},{"text":"歩合=やった分だけ返る。","size":72,"dur":2.2},
    {"text":"学歴/年齢 不問・歩合\n関東・営業インターン","size":64,"color":ACCENT,"dur":2.2},{"kicker":"ENTRY","text":"応募はプロフの\nLINEから。","size":84,"dur":2.2}]},
 {"id":"r_ai1","caption":cap("AIに仕事を奪われない20代の共通点。","“人を動かして売る力”はAIに最も奪われにくい。これを現場で持った20代は、どの時代でも強い。"),
  "beats":[{"kicker":"NAVIRIS","text":"AIに奪われない\n20代の共通点。","size":80,"dur":2.6},
    {"text":"答え:","size":110,"dur":1.4},{"text":"“人を動かして\n売る力”を持ってる。","size":74,"dur":2.4},
    {"text":"AIに最も\n奪われにくい。","size":82,"dur":2.2},{"text":"どの時代でも強い。","size":88,"dur":2.0},
    {"text":"現場で鍛える\n関東・営業インターン","size":66,"color":ACCENT,"dur":2.2},{"kicker":"ENTRY","text":"プロフのLINEへ。","size":86,"dur":2.2}]},
]

def _slides(ck, ct, cs, items, cta_t, cta_s):
    s=[{"kind":"cover","kicker":ck,"title":ct,"size":96,"sub":cs}]
    for i,(t,b) in enumerate(items,1):
        s.append({"kind":"content","no":f"{i:02d}","title":t,"body":b})
    s.append({"kind":"cta","kicker":"ENTRY","title":cta_t,"size":72,"sub":cta_s,"button":LINE})
    return s

BANK_CAR = [
 {"id":"c_gakuchika","caption":cap("就活で評価される“ガクチカ”の作り方。","資格集めより、語れる行動を1つ作る。営業インターンは数字で語れる最強のガクチカになる。"),
  "slides":_slides("NAVIRIS / 就活","評価される\nガクチカの作り方","資格集めより、\n語れる行動を1つ。",
   [("数字で語れ","「頑張った」はゼロ点。「◯件→◯件に改善」と数字で語れる経験を作る。"),
    ("過程を語れ","結果より、どう試行錯誤したか。営業は断られて改善する過程そのものがガクチカ。"),
    ("再現性を示せ","「型を作って後輩も伸ばした」まで言えると一気に強い。"),
    ("だから現場","語れる行動は現場でしか作れない。関東・光回線の営業インターンで3週間あれば十分。")],
   "語れる経験を、\nここで作らない?","学歴・年齢・経験 不問。\nまず話を聞くだけでOK。")},
 {"id":"c_naze","caption":cap("Navirisが“学歴を見ない”理由。","現場では大学名は1円にもならない。問われるのは「誰を動かせるか」。だから誰にでもフェア。"),
  "slides":_slides("NAVIRIS / 会社の世界観","なぜ学歴を\n見ないのか","現場では\n大学名は1円にもならない。",
   [("問われるのは1つ","「誰を動かせるか」。これだけ。出身校は関係ない。"),
    ("だからフェア","誰にでも同じチャンス。成果がそのまま評価とお金になる。"),
    ("歩合の意味","年功序列じゃない。出した分だけ返る。20代で“自分で稼ぐ”を経験できる。"),
    ("必要なのは1つ","スキルは後からつく。要るのは「変わる覚悟」だけ。")],
   "本気で変えたい\n人だけ来て。","学歴・年齢・経験 不問。\n話を聞くだけでもOK。")},
 {"id":"c_type","caption":cap("未経験から営業で結果を出す“型”。","センスじゃない。型を覚えて場数を踏むだけ。3週間で別人になれる再現性のある技術。"),
  "slides":_slides("NAVIRIS / インターンのリアル","未経験から\n結果を出す型","センスじゃない、\n型と量だけ。",
   [("まず真似る","先輩トークを丸コピ。考えるより先に口に出す。"),
    ("断られlog","断られた理由をメモ。次で1つ直す。これだけで刺さり出す。"),
    ("成功を再現","刺さった型を言語化して繰り返す。運じゃなく技術にする。"),
    ("3週間で別人","ここまで全部、現場で3週間あればいける。誰でも。")],
   "この型を、\n体で覚えにこない?","学歴・年齢・経験 不問。\nまず話を聞くだけでOK。")},
]

def latest_report():
    p=os.path.join(HERE,"weekly_report.md")
    return open(p).read() if os.path.exists(p) else ""

def main():
    os.makedirs(WORK, exist_ok=True)
    report=latest_report()
    n_reels=min(4 if ("リール比率を上げる" in report or not report) else 3, PER_WEEK)
    n_car=max(0, PER_WEEK-n_reels)
    state=json.load(open(STATE)) if os.path.exists(STATE) else {"used":[]}
    used=set(state["used"])
    week=datetime.date.today().strftime("%Y%m%d")

    reels=[r for r in BANK_REELS if r["id"] not in used] or BANK_REELS[:]
    cars=[c for c in BANK_CAR if c["id"] not in used] or BANK_CAR[:]
    random.shuffle(reels); random.shuffle(cars)
    pick_r=reels[:n_reels]; pick_c=cars[:n_car]

    q=json.load(open(QUEUE)); qids={p["id"] for p in q["posts"]}
    added=[]
    for i,r in enumerate(pick_r,1):
        pid=f"r_{week}_{i}"
        if pid in qids: continue
        out=os.path.join(WORK,f"{pid}.mp4")
        build_reel(r["beats"], out, audio=BGM)
        dest=os.path.join(HERE,"media",pid); os.makedirs(dest,exist_ok=True)
        shutil.copy2(out, os.path.join(dest,f"{pid}.mp4"))
        q["posts"].append({"id":pid,"type":"reel","subdir":pid,"files":[f"media/{pid}/{pid}.mp4"],"caption":r["caption"],"posted":False})
        used.add(r["id"]); added.append(pid)
    for i,c in enumerate(pick_c,1):
        pid=f"c_{week}_{i}"
        if pid in qids: continue
        outdir=os.path.join(WORK,pid)
        paths=build_carousel(c["slides"], outdir, pid)
        dest=os.path.join(HERE,"media",pid); os.makedirs(dest,exist_ok=True)
        rels=[]
        for p in paths:
            shutil.copy2(p, os.path.join(dest, os.path.basename(p)))
            rels.append(f"media/{pid}/{os.path.basename(p)}")
        q["posts"].append({"id":pid,"type":"carousel","subdir":pid,"files":rels,"caption":c["caption"],"posted":False})
        used.add(c["id"]); added.append(pid)

    json.dump(q, open(QUEUE,"w"), indent=2, ensure_ascii=False)
    json.dump({"used":list(used)}, open(STATE,"w"), indent=2, ensure_ascii=False)
    shutil.rmtree(WORK, ignore_errors=True)
    print(f"generated {len(added)}: {added} (reels={n_reels},carousels={n_car})")

if __name__ == "__main__":
    main()
