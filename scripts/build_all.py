import os, re, sys, json, subprocess, hashlib
sys.path.insert(0, r"D:\scoop\opencode-data\limbus_anki")
from segutil import analyze as seg_analyze, clean_gloss
import genanki

try:
    import config as _cfg
    ROOT = _cfg.ROOT
    MEDIA = _cfg.MEDIA
    KRD = _cfg.KRD
    ZHD = _cfg.ZHD
except Exception:
    ROOT = r"D:\scoop\opencode-data\limbus_anki"
    MEDIA = os.path.join(ROOT, "media")
    KRD = r"E:\Steam\steamapps\common\Limbus Company\LimbusCompany_Data\Assets\Resources_moved\Localize\kr\StoryData"
    ZHD = r"D:\powershellfild\LimbusLocalize_2026100501\LimbusCompany_Data\Lang\LLC_zh-CN\StoryData"
FRAMES = json.load(open(os.path.join(ROOT, "scene_frames.json"), encoding="utf-8"))
MODEL = json.load(open(os.path.join(ROOT, "lapis_model.json"), encoding="utf-8"))
SCENMAN = {}
_sp = os.path.join(ROOT, "audio_manifest.json")
if os.path.exists(_sp):
    SCENMAN = json.load(open(_sp, encoding="utf-8"))

# Korean model -> wiki icon file
ICON = {
 "이상":"icon_Yi_Sang_Story_Icon.png","파우스트":"icon_Faust_Story_Icon.png","프롤로그파우스트":"icon_Faust_Story_Icon.png",
 "돈키호테":"icon_Don_Quixote_Story_Icon.png","료슈":"icon_Ryoshu_Story_Icon.png","뫼르소":"icon_Meursault_Story_Icon.png",
 "홍루":"icon_Hong_Lu_Story_Icon.png","히스클리프":"icon_Heathcliff_Story_Icon.png","이스마엘":"icon_Ishmael_Story_Icon.png",
 "로쟈":"icon_Rodion_Story_Icon.png","싱클레어":"icon_Sinclair_Story_Icon.png","오티스":"icon_Outis_Story_Icon.png",
 "그레고르":"icon_Gregor_Story_Icon.png","단테":"icon_Dante_Story_Icon.png","프롤로그단테":"icon_Dante_Story_Icon.png",
 "프롤로그단테2":"icon_Dante_Story_Icon.png","단테2":"icon_Dante_Story_Icon.png","베르길리우스":"icon_Vergilius_Story_Icon.png",
 "눈이붉은자":"icon_Vergilius_Story_Icon.png","카론":"icon_Charon_Story_Icon.png","표범":"icon_Panther_Story_Icon.png",
 "사자":"icon_Lion_Story_Icon.png","늑대":"icon_Wolf_Story_Icon.png",
}
DANTE = {"단테","프롤로그단테","프롤로그단테2","단테2"}

def esc(s):
    if s is None: return ""
    s = re.sub(r"</?color[^>]*>", "", s)
    s = s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    return s.replace("\t"," ").replace("\r"," ").replace("\n","<br>")

def strip_tags(s): return re.sub(r"</?color[^>]*>", "", s or "")

def icon_for(m):
    fn = ICON.get(m)
    return f'<div class="lc-icon"><img src="{fn}" style="max-height:130px;width:auto"></div>' if fn else ""

NAMES = {1:"Canto I",2:"Canto II",3:"Canto III",4:"Canto IV",5:"Canto V",
         6:"Canto VI",7:"Canto VII",8:"Canto VIII",9:"Canto IX",10:"Canto X",
         11:"Canto XI",12:"Canto XII"}

def chapter_stage(scene):
    num = re.match(r"^S(\d+)", scene).group(1)
    canto = int(num[:2]) if len(num) >= 4 else int(num[0])
    if canto == 0: return "Prologue", None
    if canto == 99: return "Canto X", None
    if canto >= 90: return "Special", None
    return NAMES.get(canto, "Canto %d" % canto), None

SHORT = {"Prologue","Canto II","Canto III"}  # single subdeck

def audio_for(scene):
    p = os.path.join(ROOT, "asr_out", scene + ".json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8")).get("mapping", {})
    return {}

def wav_of(scene, clip):
    d = os.path.join(ROOT, "tmp", "wav", scene)
    if isinstance(clip, str):
        p = os.path.join(d, clip)
        return p if os.path.exists(p) else None
    for nm in ("%s-%02d.wav" % (scene, clip), "%s-%03d.wav" % (scene, clip)):
        p = os.path.join(d, nm)
        if os.path.exists(p): return p
    return None

def mp3_for(scene, clip):
    if isinstance(clip, str):
        base = clip[:-4] if clip.lower().endswith(".wav") else clip
        name = "LC_%s_%s.mp3" % (scene, base)
    else:
        name = "LC_%s_%03d.mp3" % (scene, clip)
    out = os.path.join(MEDIA, name)
    if not os.path.exists(out):
        w = wav_of(scene, clip)
        if not w: return None
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",w,"-ac","1","-b:a","64k",out], capture_output=True)
    return name if os.path.exists(out) else None

model = genanki.Model(MODEL["model_id"], MODEL["name"],
    fields=[{"name": f} for f in MODEL["fields"]],
    templates=[{"name": t["name"], "qfmt": t["qfmt"], "afmt": t["afmt"]} for t in MODEL["templates"]],
    css=MODEL["css"])

def deck_id(name): return int(hashlib.md5(name.encode()).hexdigest()[:8], 16) % 2000000000 + 100000

info = json.load(open(os.path.join(ROOT, "scene_info.json"), encoding="utf-8"))
main_scenes = sorted([sc for sc in info if re.match(r"^S\d", sc)])

decks = {}
def get_deck(name):
    if name not in decks:
        decks[name] = genanki.Deck(deck_id(name), name)
    return decks[name]

notes = 0
used_media = set()
for sc in main_scenes:
    krp = os.path.join(KRD, "KR_" + sc + ".json")
    zhp = os.path.join(ZHD, sc + ".json")
    if not (os.path.exists(krp) and os.path.exists(zhp)): continue
    kr = json.load(open(krp, encoding="utf-8"))["dataList"]
    zh = json.load(open(zhp, encoding="utf-8"))["dataList"]
    if not isinstance(kr, list):
        print("BADKR", sc, type(kr).__name__); continue
    if not isinstance(zh, list):
        print("BADZH", sc, type(zh).__name__); zh = []
    chap, stage = chapter_stage(sc)
    if chap in SHORT or not stage:
        deck_name = "Limbus Company Anki::" + chap
    else:
        deck_name = "Limbus Company Anki::%s::%s" % (chap, stage)
    amap = audio_for(sc)
    frames = FRAMES.get(sc, {})
    for i, e in enumerate(kr):
        if not isinstance(e, dict):
            continue
        z = zh[i] if isinstance(zh, list) and i < len(zh) else {}
        if not isinstance(z, dict):
            z = {}
        krtext = strip_tags(e.get("content") or "")
        zhtext = strip_tags(z.get("content") or "")
        if not krtext.strip() and not zhtext.strip(): continue
        try: annotated, segline, supp, entries, gloss = seg_analyze(krtext, zhtext)
        except Exception: annotated, segline, supp, entries, gloss = "", "", {}, [], ""
        seg_html = ""
        if annotated.strip():
            seg_html = ('<hr><div style="font-size:0.85em;line-height:1.8"><b>逐词</b>：%s<br><b>汉字</b>：%s<br><b>分词</b>：%s</div>'
                        % (esc(gloss), esc(annotated), esc(segline)))
        maindef = '<div style="font-size:17px;line-height:1.7">%s%s</div>' % (esc(zhtext), seg_html)
        supp_html = ""
        if supp:
            items = [ '%s(%s) → %s' % (esc(w), esc(c), "、".join(esc(a) for a in alts)) for w,(c,alts) in supp.items() ]
            supp_html = '<hr><div style="font-size:0.9em"><b>其他义项</b><br>' + "<br>".join(items) + "</div>"
        dict_html = ""
        if entries:
            items = []
            for en in entries:
                w = en["w"]; hj = en.get("hanja", ""); pos = en.get("pos", "")
                senses = en.get("senses", [])
                title = esc(w) + (("(%s)" % esc(hj)) if hj else "") + (
                    (" <span style='color:#999'>[%s]</span>" % esc(pos)) if pos else "")
                body = "；".join(esc(s) for s in senses[:6])
                exhtml = ""
                ex = en.get("ex") or []
                if ex:
                    eko, ezh = ex[0]
                    exhtml = ('<div style="color:#999;margin-left:1em;font-size:0.92em">例：%s<br>%s</div>'
                              % (esc(eko), esc(ezh)))
                items.append('<div style="margin-top:6px"><b>%s</b> %s%s</div>' % (title, body, exhtml))
            dict_html = '<hr><div style="font-size:0.9em;line-height:1.7"><b>词典</b>' + "".join(items) + "</div>"
        speaker = e.get("teller") or e.get("title") or ""
        if e.get("model"): speaker = (e["model"] + "｜" + speaker) if speaker else e["model"]
        src = "%s#%s" % (sc, e.get("id"))
        foot = ('<hr><div style="font-size:0.78em;color:#999">来源：%s　|　发现错误请到 GitHub Issues 反馈</div>'
                % esc(src))
        glos = '<div style="font-size:17px;line-height:1.7">%s%s%s%s</div>' % (esc(speaker), supp_html, dict_html, foot)
        expr = '<span style="font-size:32px;line-height:1.6">%s</span>' % esc(krtext)
        picture = ""
        fr = frames.get(str(i))
        if fr:
            picture = '<img src="frame_%s" style="max-width:100%%">' % fr
            used_media.add("frame_%s" % fr)
        audio = ""
        smclip = SCENMAN.get(sc, {}).get(str(i))
        if smclip:
            audio = "[sound:%s]" % smclip
        else:
            clip = amap.get(str(i))
            if clip is not None:
                mp = mp3_for(sc, clip)
                if mp: audio = "[sound:%s]" % mp
        if not audio and e.get("model") in DANTE:
            dur = max(0.8, sum(1 for c in krtext if 0xAC00 <= ord(c) <= 0xD7A3) * 0.24)
            tick = os.path.join(MEDIA, "LC_%s_tick_%03d.mp3" % (sc, i))
            if not os.path.exists(tick):
                subprocess.run(["ffmpeg","-y","-loglevel","error","-stream_loop","-1","-i",
                                os.path.join(ROOT,"tick.wav"),"-t","%.2f"%dur,"-b:a","96k",tick], capture_output=True)
            if os.path.exists(tick): audio = "[sound:%s]" % os.path.basename(tick)
        if audio: used_media.add(audio[len("[sound:"):-1])
        iconfn = ICON.get(e.get("model"))
        if iconfn: used_media.add(iconfn)
        fields = [expr,"","",audio,"",maindef,"","","","",picture,glos,icon_for(e.get("model")),
                  "","","","","","","", esc("%s#%s"%(sc,e.get("id")))]
        get_deck(deck_name).add_note(genanki.Note(model=model, fields=fields,
                                                  tags=["Limbus", chap.replace(" ", ""), sc]))
        notes += 1

media = []
seen = set()
for f in sorted(used_media):
    p = os.path.join(MEDIA, f)
    if f.lower().endswith((".mp3", ".png")) and f not in seen and os.path.exists(p):
        seen.add(f); media.append(p)

pkg = genanki.Package(list(decks.values()))
pkg.media_files = media
outpkg = os.path.join(ROOT, "Limbus_Company_Anki.apkg")
pkg.write_to_file(outpkg)
print("notes", notes, "decks", len(decks), "media", len(media), "->", outpkg, os.path.getsize(outpkg))
for n in sorted(decks): print("  deck:", n)
