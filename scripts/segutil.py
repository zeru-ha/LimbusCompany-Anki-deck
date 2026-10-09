import os, csv, json, re, unicodedata, zhconv

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dict")

# Kengdic: clean Sino-Korean headwords -> hanja candidates
kd = {}
_kp = os.path.join(D, "kengdic.tsv")
if os.path.exists(_kp):
    for r in csv.reader(open(_kp, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if len(r) > 2 and r[1].strip() and r[2].strip():
            kd.setdefault(r[1].replace(" ", ""), []).append(r[2].strip())

# libhangul frequent hanjaeo -> frequency (lower = more frequent)
freq = {}
_fp = os.path.join(D, "libhangul_freq-hanjaeo.txt")
if os.path.exists(_fp):
    for line in open(_fp, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        w, n = line.rsplit(":", 1)
        try:
            freq[w] = int(n)
        except ValueError:
            pass

# 新世纪韩汉词典 (OCR) -> word -> {hanja, body}
XDICT = {}
_xp = os.path.join(D, "xinshiji_dict.json")
if os.path.exists(_xp):
    XDICT = json.load(open(_xp, encoding="utf-8"))

# Naver 韩汉词典 (MDX) -> word -> {pos, senses, ex}
NAVER = {}
_nv = os.path.join(D, "naver_dict.json")
if os.path.exists(_nv):
    NAVER = json.load(open(_nv, encoding="utf-8"))


TAGPOS = {"NNG": "名词", "NNP": "名词", "NR": "数词", "XR": "名词", "NP": "代词",
          "VV": "动词", "VA": "形容词", "MAG": "副词", "MAJ": "副词", "MM": "冠形词"}


def _del_coda(ch):
    o = ord(ch) - 0xAC00
    if 0 <= o < 11172:
        fin = o % 28
        if fin:
            return chr(0xAC00 + (o - fin))
    return None


def naver_entry(word, tag=None):
    want = TAGPOS.get(tag) if tag else None
    cands = []

    def add(x):
        if x and x not in cands:
            cands.append(x)

    add(word); add(word + "다"); add(word + "하다"); add(word + "되다")
    pref = []
    if word.endswith("다") and len(word) >= 2:
        c = _del_coda(word[-2])
        if c:
            pref.append(word[:-2] + c + "다")
            pref.append(word[:-2] + c + "하다")
    for suf in ("니다", "습니다", "는다", "ㄴ다", "다", "요", "네", "까", "죠", "지",
                "서", "고", "면", "야", "해", "는데", "나"):
        if word.endswith(suf) and len(word) > len(suf):
            st = word[:-len(suf)]
            add(st + "다"); add(st + "하다")
            s2 = st[:-1] + _del_coda(st[-1]) if st and _del_coda(st[-1]) else None
            if s2:
                add(s2 + "다"); add(s2 + "하다")
            elif st.endswith(("ㄴ", "ㄹ", "는", "은", "ㅁ")):
                add(st[:-1] + "다"); add(st[:-1] + "하다")
    cands = pref + cands
    first = verbal = None
    for c in cands:
        subs = NAVER.get(c)
        if not subs:
            continue
        if first is None:
            first = (c, subs[0])
        if want:
            for s in subs:
                if want in s.get("pos", ""):
                    return c, s
        if verbal is None:
            for s in subs:
                if "动词" in s.get("pos", "") or "形容词" in s.get("pos", ""):
                    verbal = (c, s)
                    break
    if verbal and word.endswith(("다", "요", "네", "까", "죠", "지", "니다", "야", "해")):
        return verbal
    if first and len(word) >= 2:
        return first
    return None

# 常用助词(JK*) / 词尾(EP,EF,EC,ETM) -> 中文功能
PART = {
    "은": "主题", "는": "主题", "이": "主格", "가": "主格", "께서": "主格(敬)",
    "을": "宾格", "를": "宾格", "에": "到/在", "에서": "在/从", "에게": "给", "한테": "给", "께": "给(敬)",
    "의": "的", "와": "和", "과": "和", "하고": "和", "도": "也", "만": "只", "부터": "从", "까지": "到",
    "로": "往/用", "으로": "往/用", "라고": "叫做", "이라고": "叫做", "라는": "叫做", "이라는": "叫做",
    "보다": "比", "처럼": "像", "같이": "像", "마다": "每", "밖에": "只有", "이나": "或", "나": "或",
    "든지": "无论", "커녕": "别说", "치고": "作为", "으로써": "以", "로서": "作为", "만큼": "如同/程度",
    "안에": "之内", "속에": "之中", "위에": "之上", "밑에": "之下",
}
END = {
    "다": "陈述", "요": "敬体", "네": "呢", "죠": "吧", "까": "吗", "지": "吧",
    "고": "并且", "서": "因为/然后", "면": "如果", "니까": "因为", "지만": "但是", "면서": "一边…一边",
    "러": "为了", "려고": "打算", "게": "让", "도록": "使得", "는데": "背景", "은데": "背景",
    "겠": "将/推测", "았": "过去", "었": "过去", "시": "敬", "신": "敬",
    "ㄴ": "冠形", "ㄹ": "将要", "는": "冠形", "은": "冠形", "을": "冠形", "던": "回忆",
}


def clean_gloss(body, maxlen=60):
    if not body:
        return ""
    s = body.replace("\ufffd", "")
    s = s.split("|")[0]
    s = re.sub(r"[^\u4e00-\u9fff。、，；：·「」]+", "", s)
    s = re.sub(r"^[。、，；：·「」]+", "", s)
    s = s.strip()
    return s[:maxlen].strip()


def word_gloss(surface, tag, zh):
    if tag in ("JKS", "JKC", "JKG", "JKO", "JKB", "JKV", "JKQ", "JC", "JX"):
        return PART.get(surface, "")
    if tag in ("EP", "EF", "EC", "ETM"):
        return END.get(surface, "")
    if tag in ("NNG", "NNP", "NP", "NR", "XR", "VV", "VA", "MAG", "MAJ", "MM"):
        ne = naver_entry(surface, tag)
        if ne:
            senses = ne[1].get("senses") or []
            if senses:
                return " ".join(senses[0].split()[:4])
        if tag in ("NNG", "NNP", "XR"):
            h = pick_hanja(surface, zh)
            if h:
                return h
        de = dict_entry(surface)
        if de:
            g = clean_gloss(de[2], 40)
            if g:
                return g
    return ""


def dict_entry(word, chosen=None):
    for c in (word, word + "다", word + "하다", word + "되다"):
        lst = XDICT.get(c)
        if lst:
            if chosen:
                for e in lst:
                    if chosen in _simp(e.get("hanja", "")) or chosen in _simp(e.get("body", "")[:80]):
                        return c, chosen, e.get("body", "")
            return c, lst[0].get("hanja", ""), lst[0].get("body", "")
    return None


def _simp(s):
    return zhconv.convert(unicodedata.normalize("NFKC", s), "zh-cn")


def pick_hanja(word, zhtext):
    cands = kd.get(word)
    if not cands:
        return None
    zt = zhtext or ""
    best, bestscore, bestf = None, -1, None
    for c in cands:
        sc = _simp(c)
        if not sc:
            continue
        if sc in zt:
            score = len(sc) + 5
        else:
            score = sum(1 for ch in sc if ch in zt)
        f = freq.get(c, 10**12)
        if score > bestscore or (score == bestscore and (bestf is None or f < bestf)):
            bestscore, bestf, best = score, f, sc
    return best


_km = None
def _tagger():
    global _km
    if _km is None:
        from konlpy.tag import Komoran
        _km = Komoran()
    return _km

CONTENT = {"NNG", "NNP", "XR"}


def alternatives(word, chosen):
    cands = kd.get(word)
    if not cands:
        return []
    seen = set()
    res = []
    for c in cands:
        sc = _simp(c)
        if sc and sc != chosen and sc not in seen:
            seen.add(sc)
            res.append((freq.get(c, 10**12), sc))
    res.sort()
    return [s for _, s in res]


def analyze(kr, zh):
    """Return (hanja_annotated, morpheme_seg, supplements, entries, per-eojeol gloss)."""
    km = _tagger()
    toks = km.pos(kr)
    out, glosses, idx = [], [], 0
    supp = {}
    entries = []
    seen = set()
    for eojeol in kr.split(" "):
        if not eojeol:
            out.append(""); glosses.append("")
            continue
        grp, acc = [], 0
        while idx < len(toks) and acc < len(eojeol):
            m, t = toks[idx]
            grp.append((m, t))
            acc += len(m)
            idx += 1
        tags = []
        gs = []
        for m, t in grp:
            h = None
            if t in CONTENT and len(m) >= 2:
                h = pick_hanja(m, zh)
                if h:
                    tags.append(h)
                    alts = alternatives(m, h)
                    if alts:
                        supp[m] = (h, alts[:4])
            if t in ("NNG", "NNP", "NP", "NR", "XR", "VV", "VA", "MAG", "MAJ", "MM") and m not in seen:
                ne = naver_entry(m, t)
                if ne:
                    seen.add(m)
                    ee = ne[1]
                    entries.append({"w": m, "pos": ee.get("pos", ""), "senses": ee.get("senses", []),
                                    "hanja": h or "", "ex": ee.get("ex") or []})
                else:
                    de = dict_entry(m)
                    if de:
                        seen.add(m)
                        entries.append({"w": m, "pos": "", "senses": [clean_gloss(de[2], 80)],
                                        "hanja": de[1], "ex": []})
            g = word_gloss(m, t, zh)
            if g and g not in gs:
                gs.append(g)
        out.append(eojeol + ("(" + "".join(tags) + ")" if tags else ""))
        glosses.append(eojeol + ("(" + "；".join(gs) + ")" if gs else ""))
    annotated = " ".join(out)
    gloss = " ".join(glosses)
    seg = " ".join(
        (m + ("(" + pick_hanja(m, zh) + ")" if (t in CONTENT and len(m) >= 2 and pick_hanja(m, zh)) else "")) + "/" + t
        for m, t in toks
    )
    return annotated, seg, supp, entries, gloss
