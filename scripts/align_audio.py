import os, re, json

TMP = r"D:\scoop\opencode-data\limbus_anki\tmp\wav"
ROOT = r"D:\scoop\opencode-data\limbus_anki"
KRD = r"E:\Steam\steamapps\common\Limbus Company\LimbusCompany_Data\Assets\Resources_moved\Localize\kr\StoryData"
DANTE = {"단테", "프롤로그단테", "프롤로그단테2"}

def wav_durs(scene):
    d = {}
    dirp = os.path.join(TMP, scene)
    if not os.path.isdir(dirp):
        return d
    for f in os.listdir(dirp):
        m = re.match(re.escape(scene) + r"-(\d+)\.wav$", f)
        if m:
            d[int(m.group(1))] = (os.path.getsize(os.path.join(dirp, f)) - 44) / (48000 * 2)
    return d

def line_len(s):
    return sum(1 for ch in s if 0xAC00 <= ord(ch) <= 0xD7A3)

def align(scene):
    durs = wav_durs(scene)
    kr = json.load(open(os.path.join(KRD, "KR_" + scene + ".json"), encoding="utf-8"))["dataList"]
    clips = sorted(durs)
    if not clips:
        return {}, kr
    # spoken/dialogue lines: have a speaker (model or teller/title),
    # not Dante, and have actual syllables (skip "……！"-only SFX lines)
    match_idx = [i for i, e in enumerate(kr)
                 if (e.get("model") or e.get("teller") or e.get("title"))
                 and e.get("model") not in DANTE
                 and line_len(e.get("content") or "") >= 1]
    D = [durs[c] for c in clips]
    L = [max(line_len(kr[i].get("content") or ""), 2) for i in match_idx]
    K, M = len(D), len(L)
    if M == 0:
        return {}, kr
    alpha = sum(D) / max(1, sum(L))
    gap = 1000000
    NEG = float("-inf")
    f = [[NEG] * (M + 1) for _ in range(K + 1)]
    back = [[None] * (M + 1) for _ in range(K + 1)]
    f[0][0] = 0
    for i in range(1, K + 1):
        f[i][0] = f[i-1][0] - gap; back[i][0] = (i-1, 0, 0)
    for j in range(1, M + 1):
        f[0][j] = f[0][j-1] - gap; back[0][j] = (0, j-1, 0)
    for i in range(1, K + 1):
        for j in range(1, M + 1):
            best = f[i-1][j] - gap; act = (i-1, j, 0)
            if f[i][j-1] - gap > best:
                best = f[i][j-1] - gap; act = (i, j-1, 0)
            sim = -abs(D[i-1] / alpha - L[j-1])
            if f[i-1][j-1] + sim > best:
                best = f[i-1][j-1] + sim; act = (i-1, j-1, 1)
            f[i][j] = best; back[i][j] = act
    i, j = K, M
    m = {}
    while i > 0 or j > 0:
        pi, pj, act = back[i][j]
        if act == 1:
            m[match_idx[j-1]] = clips[i-1]
        i, j = pi, pj
    return m, kr

scenes = ["S001A", "S001B", "S002B", "S003A", "S003B", "S004A", "S004B"]
out = {}
for sc in scenes:
    m, kr = align(sc)
    out[sc] = {str(k): v for k, v in m.items()}
    print(f"== {sc}: {len(m)} clips mapped")
json.dump(out, open(os.path.join(ROOT, "audio_map.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# checks
kr = json.load(open(os.path.join(KRD, "KR_S001A.json"), encoding="utf-8"))["dataList"]
id2idx = {e.get("id"): i for i, e in enumerate(kr) if e.get("id") is not None}
print("id14 (user's Dante line) ->", out["S001A"].get(str(id2idx.get(14))))
for idx_s, clip in sorted(out["S001A"].items(), key=lambda x: int(x[0]))[:8]:
    i = int(idx_s)
    print(f"  line[{i}] {kr[i].get('model')} <- S001A-{clip:02d}  {(kr[i].get('content') or '')[:26]}")
