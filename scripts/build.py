import os, re, json, struct, subprocess, shutil, sys

GAME = r"E:\Steam\steamapps\common\Limbus Company\LimbusCompany_Data"
KRDIR = os.path.join(GAME, r"Assets\Resources_moved\Localize\kr\StoryData")
PATCH = r"D:\powershellfild\LimbusLocalize_2026100501\LimbusCompany_Data\Lang\LLC_zh-CN\StoryData"
BANKDIR = os.path.join(GAME, r"StreamingAssets\Assets\Sound\FMODBuilds\Desktop")

ROOT = r"D:\scoop\opencode-data\limbus_anki"
MEDIA = os.path.join(ROOT, "media")
TMP = os.path.join(ROOT, "tmp")
for d in (ROOT, MEDIA, TMP):
    os.makedirs(d, exist_ok=True)

VGM = "vgmstream-cli"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from segutil import analyze as seg_analyze
except Exception as _e:
    print("segutil unavailable:", _e)
    def seg_analyze(kr, zh):
        return "", "", {}, [], ""

import json as _json
FRAMES = {}
_fp = os.path.join(ROOT, "scene_frames.json")
if os.path.exists(_fp):
    FRAMES = _json.load(open(_fp, encoding="utf-8"))

AUDIO_MAP = {}
_ap = os.path.join(ROOT, "audio_map.json")
if os.path.exists(_ap):
    AUDIO_MAP = _json.load(open(_ap, encoding="utf-8"))

DANTE = {"단테", "프롤로그단테", "프롤로그단테2"}
TICK = os.path.join(ROOT, "tick.wav")


def _syll(s):
    return sum(1 for ch in s if 0xAC00 <= ord(ch) <= 0xD7A3)


def make_tick(mp3path, dur):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1",
                        "-i", TICK, "-t", f"{dur:.2f}", "-b:a", "96k", mp3path],
                       capture_output=True)
    return r.returncode == 0

def load(scene, zh=False):
    d = PATCH if zh else KRDIR
    fn = (scene + ".json") if zh else ("KR_" + scene + ".json")
    p = os.path.join(d, fn)
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))["dataList"]

def strip_tags(s):
    if not s:
        return ""
    return re.sub(r"</?color[^>]*>", "", s)

def esc(s):
    if s is None:
        return ""
    s = strip_tags(s)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s.replace("\t", " ").replace("\r", " ").replace("\n", "<br>")

def extract_fsb(bankpath, outpath):
    data = open(bankpath, "rb").read()
    off = data.find(b"FSB5")
    if off < 0:
        return False
    ver, num, hdr, nametbl, dsize, mode = struct.unpack_from("<6I", data, off + 4)
    total = 60 + hdr + nametbl + dsize
    open(outpath, "wb").write(data[off:off + total])
    return True

def bank_to_wavs(scene, wavdir):
    bank = os.path.join(BANKDIR, scene + ".assets.bank")
    if not os.path.exists(bank):
        return {}
    fsb = os.path.join(TMP, scene + ".fsb")
    if not extract_fsb(bank, fsb):
        return {}
    if os.path.isdir(wavdir):
        shutil.rmtree(wavdir)
    os.makedirs(wavdir, exist_ok=True)
    subprocess.run([VGM, "-i", "-S", "0", "-o", os.path.join(wavdir, "?n.wav"), fsb],
                   capture_output=True)
    out = {}
    pat = re.compile(re.escape(scene) + r"-(\d{1,3})\.wav$", re.I)
    for f in os.listdir(wavdir):
        m = pat.match(f)
        if m:
            out[int(m.group(1))] = os.path.join(wavdir, f)
    return out

ICON_MAP = {
    "그레고르": "icon_Gregor_Story_Icon.png",
    "눈이붉은자": "icon_Vergilius_Story_Icon.png",
    "늑대": "icon_Wolf_Story_Icon.png",
    "로쟈": "icon_Rodion_Story_Icon.png",
    "사자": "icon_Lion_Story_Icon.png",
    "이상": "icon_Yi_Sang_Story_Icon.png",
    "이스마엘": "icon_Ishmael_Story_Icon.png",
    "파우스트": "icon_Faust_Story_Icon.png",
    "프롤로그파우스트": "icon_Faust_Story_Icon.png",
    "표범": "icon_Panther_Story_Icon.png",
    "단테": "icon_Dante_Story_Icon.png",
    "프롤로그단테": "icon_Dante_Story_Icon.png",
    "프롤로그단테2": "icon_Dante_Story_Icon.png",
    "오티스": "icon_Outis_Story_Icon.png",
    "히스클리프": "icon_Heathcliff_Story_Icon.png",
    "돈키호테": "icon_Don_Quixote_Story_Icon.png",
    "료슈": "icon_Ryoshu_Story_Icon.png",
    "뫼르소": "icon_Meursault_Story_Icon.png",
    "싱클레어": "icon_Sinclair_Story_Icon.png",
    "카론": "icon_Charon_Story_Icon.png",
    "베르길리우스": "icon_Vergilius_Story_Icon.png",
    "홍루": "icon_Hong_Lu_Story_Icon.png",
    "???": "icon_Other_Story_Icon.png",
}


def icon_for(model):
    if not model:
        return ""
    fn = ICON_MAP.get(model)
    if not fn:
        return ""
    return f'<div class="lc-icon"><img src="{fn}" style="max-height:130px;width:auto"></div>'


def wav_to_mp3(wav, mp3):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "96k", mp3],
                       capture_output=True)
    return r.returncode == 0

def build_group(scenes):
    kr_all, zh_all, scene_of, idx_of = [], [], [], []
    for sc in scenes:
        kr = load(sc)
        zh = load(sc, zh=True)
        if kr is None:
            print("  !! missing", sc); continue
        for i, e in enumerate(kr):
            kr_all.append(e)
            zh_all.append(zh[i] if (zh and i < len(zh)) else {})
            scene_of.append(sc)
            idx_of.append(i)

    wavs = {}
    for sc in scenes:
        got = bank_to_wavs(sc, os.path.join(TMP, "wav", sc))
        if got:
            mx = max(got)
            offset = (min(got) - 1) if min(got) >= 6 else 0
            for nn, w in got.items():
                wavs[(sc, nn)] = w
            wavs[("__offset__", sc)] = offset

    alpha_by_scene = {}
    for sc in scenes:
        kr_sc = load(sc) or []
        td = 0.0; ts = 0
        for idx_s, clip in AUDIO_MAP.get(sc, {}).items():
            w = wavs.get((sc, clip)); i = int(idx_s)
            if w and 0 <= i < len(kr_sc):
                td += (os.path.getsize(w) - 44) / (48000 * 2)
                ts += max(_syll(kr_sc[i].get("content") or ""), 1)
        alpha_by_scene[sc] = td / ts if ts else 0.24

    rows = []
    audio_n = 0
    for pos, (e, z, sc, sidx) in enumerate(zip(kr_all, zh_all, scene_of, idx_of)):
        krtext = strip_tags(e.get("content") or "")
        zhtext = strip_tags(z.get("content") or "")
        if not krtext.strip() and not zhtext.strip():
            continue
        clipnum = AUDIO_MAP.get(sc, {}).get(str(sidx))
        audio_field = ""
        if clipnum is not None:
            w = wavs.get((sc, clipnum))
            if w:
                mp3name = f"LC_{sc}_{clipnum:03d}.mp3"
                mp3path = os.path.join(MEDIA, mp3name)
                if not os.path.exists(mp3path):
                    wav_to_mp3(w, mp3path)
                if os.path.exists(mp3path):
                    audio_field = f"[sound:{mp3name}]"
                    audio_n += 1
        if not audio_field and e.get("model") in DANTE:
            dur = max(0.8, _syll(krtext) * alpha_by_scene.get(sc, 0.24))
            mp3name = f"LC_{sc}_tick_{sidx:03d}.mp3"
            mp3path = os.path.join(MEDIA, mp3name)
            if not os.path.exists(mp3path):
                make_tick(mp3path, dur)
            if os.path.exists(mp3path):
                audio_field = f"[sound:{mp3name}]"
                audio_n += 1
        speaker = e.get("teller") or e.get("title") or ""
        if e.get("model"):
            speaker = (e.get("model") + "｜" + speaker) if speaker else e.get("model")
        place = e.get("place", "")
        glossary = speaker + (f" @ {place}" if place else "")
        frame = FRAMES.get(sc, {}).get(str(sidx))
        picture = f'<img src="frame_{frame}" style="max-width:100%">' if frame else ""
        try:
            annotated, segline, supp, entries, gloss = seg_analyze(krtext, zhtext)
        except Exception:
            annotated, segline, supp, entries, gloss = "", "", {}, [], ""
        seg_html = ""
        if annotated.strip():
            seg_html = ('<hr><div style="font-size:0.85em;line-height:1.7">'
                        f'<b>汉字</b>：{esc(annotated)}<br>'
                        f'<b>分词</b>：{esc(segline)}</div>')
        maindef = esc(zhtext) + seg_html
        supp_html = ""
        if supp:
            items = []
            for w, (chosen, alts) in supp.items():
                items.append(f'{esc(w)}({esc(chosen)}) → ' + "、".join(esc(a) for a in alts))
            supp_html = ('<hr><div style="font-size:0.9em"><b>其他义项</b><br>'
                         + "<br>".join(items) + "</div>")
        dict_html = ""
        if entries:
            items = []
            for en in entries:
                if isinstance(en, dict):
                    head = esc(en["w"]) + (f"({esc(en['hanja'])})" if en.get("hanja") else "")
                    body = "；".join(esc(s) for s in en.get("senses", [])[:6])
                else:
                    w, hj, body = en
                    head = esc(w) + (f"({esc(hj)})" if hj else "")
                    body = esc(body)
                items.append(f'<div style="margin-top:6px"><b>{head}</b> {body}</div>')
            dict_html = '<hr><div style="font-size:0.9em;line-height:1.6"><b>词典</b>' + "".join(items) + "</div>"
        glos = esc(glossary) + supp_html + dict_html
        expr_html = f'<span style="font-size:32px;line-height:1.6">{esc(krtext)}</span>'
        maindef = f'<div style="font-size:17px;line-height:1.7">{maindef}</div>'
        glos = f'<div style="font-size:17px;line-height:1.7">{glos}</div>'
        fields = [
            expr_html, "", "", audio_field, "", maindef, "",
            "", "", "", picture, glos, icon_for(e.get("model")),
            "", "", "", "", "", "", "",
            esc(f"{sc}#{e.get('id')}"),
            f"Limbus Prologue {sc}",
        ]
        rows.append("\t".join(fields))
    return rows, audio_n

def main():
    groups = [["S001A"], ["S001B"], ["S002B"], ["S003A"], ["S003B"], ["S004A", "S004B"]]
    allrows = []
    audios = 0
    for g in groups:
        r, a = build_group(g)
        print(f"  {g}: {len(r)} notes, {a} audio")
        allrows += r
        audios += a
    out = os.path.join(ROOT, "Limbus_Prologue.txt")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("#separator:tab\n#html:true\n#notetype:Lapis\n")
        f.write("#deck:Limbus Company::Prologue\n#tags column:22\n")
        f.write("\n".join(allrows) + "\n")
    print("TOTAL", len(allrows), "notes,", audios, "audio ->", out)

if __name__ == "__main__":
    main()
