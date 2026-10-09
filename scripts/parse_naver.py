import sys, types, re, json, html, os
sys.modules["lzo"] = types.ModuleType("lzo")
sys.modules["lzo"].decompress = lambda *a, **k: (_ for _ in ()).throw(NotImplementedError("lzo"))
from readmdict import MDX

MDX_PATH = r"D:\Download\_Zenload\Naver韩汉汉韩词典.mdx"
OUT = r"D:\scoop\opencode-data\limbus_anki\dict\naver_dict.json"
try:
    import config as _cfg
    if _cfg.MDX:
        MDX_PATH = _cfg.MDX
    OUT = os.path.join(_cfg.ROOT, "dict", "naver_dict.json")
except Exception:
    pass

HANGUL = re.compile(r"[\uac00-\ud7a3]")
LATIN = re.compile(r"[A-Za-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü·]")
POSMAP = {"동사": "动词", "형용사": "形容词", "명사": "名词", "부사": "副词", "조사": "助词",
          "어미": "词尾", "관형사": "冠形词", "감탄사": "感叹词", "대명사": "代词", "수사": "数词",
          "접사": "词缀", "의존명사": "依存名词", "품사": "词性", "불완전명사": "不完全名词"}


def strip_tags(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"[\s\u00a0]+", " ", s).strip()


def clean_zh(s):
    s = LATIN.sub("", s)
    s = HANGUL.sub("", s)
    s = re.sub(r"^\s*\(\d+\)\s*", "", s)
    s = re.sub(r"[·\.]", " ", s)
    s = re.sub(r"[【】\[\]]", " ", s)
    s = re.sub(r"[‧’‘“”\"'「」『』〈〉《》～~・]", " ", s)
    s = re.sub(r"[\s\u00a0]+", " ", s).strip()
    s = re.sub(r"^[。、，,;；:：]+", "", s).strip()
    s = re.sub(r"[。、，,;；:：\s]+$", "", s).strip()
    return s


def parse_pos(raw):
    toks = []
    for t in re.split(r"[\s\[\]<>/]+", raw):
        t = t.strip()
        if t:
            toks.append(POSMAP.get(t, ""))
    return "".join(dict.fromkeys(t for t in toks if t))


def parse_seg(body):
    chunks = re.split(r"<p>|<br\s*/?>", body)
    pos_raw = ""
    ko_ex, zh_ex, senses = [], [], []
    for ch in chunks:
        if not ch.strip():
            continue
        if "color=red" in ch:
            pos_raw += " " + strip_tags(ch)
        elif "color=darkblue" in ch:
            ko_ex.append(strip_tags(ch))
        elif "color=black" in ch:
            zh_ex.append(strip_tags(ch))
        elif "color=blue" in ch:
            continue
        else:
            t = strip_tags(ch)
            if not t:
                continue
            if len(HANGUL.findall(t)) > len(re.findall(r"[\u4e00-\u9fff]", t)):
                continue
            c = clean_zh(t)
            if c:
                senses.append(c)
    ex = [[a, b] for a, b in zip(ko_ex, zh_ex)][:2]
    return {"pos": parse_pos(pos_raw), "senses": senses[:8], "ex": ex}


def parse(htmlstr):
    parts = re.split(r"<font color=blue[^>]*>", htmlstr)
    subs = []
    for seg in parts[1:]:
        m = re.match(r"(.*?)</font>(.*)", seg, re.S)
        body = m.group(2) if m else seg
        e = parse_seg(body)
        if e["senses"]:
            subs.append(e)
    return subs or None


mdx = MDX(MDX_PATH)
data = {}
for key, val in mdx.items():
    w = key.decode("utf-8", "replace").strip()
    if not HANGUL.search(w) or w in data:
        continue
    try:
        subs = parse(val.decode("utf-8", "replace"))
    except Exception:
        continue
    if subs:
        data[w] = subs

json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
print("entries:", len(data))
out = open(r"D:\scoop\opencode-data\limbus_anki\logs\naver_sample.txt", "w", encoding="utf-8")
for w in ["이", "선물", "가다", "있다"]:
    out.write("%s -> %s\n" % (w, json.dumps(data.get(w, []), ensure_ascii=False)))
out.close()
