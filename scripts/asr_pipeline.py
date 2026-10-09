import os, re, sys, json, struct, subprocess, wave
import numpy as np, difflib
from faster_whisper import WhisperModel

try:
    import config as _cfg
    ROOT = _cfg.ROOT
    BANKDIR = _cfg.BANKDIR
    KRD = _cfg.KRD
except Exception:
    ROOT = r"D:\scoop\opencode-data\limbus_anki"
    BANKDIR = r"E:\Steam\steamapps\common\Limbus Company\LimbusCompany_Data\StreamingAssets\Assets\Sound\FMODBuilds\Desktop"
    KRD = r"E:\Steam\steamapps\common\Limbus Company\LimbusCompany_Data\Assets\Resources_moved\Localize\kr\StoryData"
TMP = os.path.join(ROOT, "tmp")
DANTE = {"단테", "프롤로그단테", "프롤로그단테2", "단테2"}
OUTDIR = os.path.join(ROOT, "asr_out")
os.makedirs(OUTDIR, exist_ok=True)

_model = None
def model():
    global _model
    if _model is None:
        _model = WhisperModel("small", device="cuda", compute_type="float16")
    return _model

def extract_fsb(bankpath, outpath):
    d = open(bankpath, "rb").read()
    off = d.find(b"FSB5")
    if off < 0: return False
    ver, num, hdr, nt, ds, mode = struct.unpack_from("<6I", d, off + 4)
    open(outpath, "wb").write(d[off:off + 60 + hdr + nt + ds])
    return True

def ensure_wavs(scene):
    wdir = os.path.join(TMP, "wav", scene)
    if os.path.isdir(wdir) and any(f.endswith(".wav") for f in os.listdir(wdir)):
        return wdir
    bank = os.path.join(BANKDIR, scene + ".assets.bank")
    if not os.path.exists(bank):
        return None
    fsb = os.path.join(TMP, scene + ".fsb")
    if not extract_fsb(bank, fsb):
        return None
    os.makedirs(wdir, exist_ok=True)
    subprocess.run(["vgmstream-cli", "-i", "-S", "0", "-o", os.path.join(wdir, "?n.wav"), fsb],
                   capture_output=True)
    return wdir

def load16k(path):
    w = wave.open(path); sr = w.getframerate(); ch = w.getnchannels()
    d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1: d = d.reshape(-1, ch).mean(axis=1)
    if sr != 16000:
        idx = np.linspace(0, len(d) - 1, int(len(d) * 16000 / sr)).astype(int); d = d[idx]
    return d

def norm(s): return re.sub(r"[^0-9A-Za-z\uac00-\ud7a3]", "", s or "")

def run(scene):
    out = os.path.join(OUTDIR, scene + ".json")
    if os.path.exists(out):
        return json.load(open(out, encoding="utf-8"))
    wdir = ensure_wavs(scene)
    if not wdir:
        res = {"scene": scene, "error": "no bank"}
        json.dump(res, open(out, "w", encoding="utf-8")); return res
    kr = json.load(open(os.path.join(KRD, "KR_" + scene + ".json"), encoding="utf-8"))["dataList"]
    cand = [i for i, e in enumerate(kr)
            if (e.get("model") or e.get("teller") or e.get("title"))
            and e.get("model") not in DANTE and norm(e.get("content"))]
    clips = []
    for f in os.listdir(wdir):
        m = re.match(r"(.+)-(\d+)\.wav$", f)
        if m:
            clips.append((int(m.group(2)), f))
    clips.sort()
    clipfiles = [f for _, f in clips]
    asr = {}
    for f in clipfiles:
        segs, _ = model().transcribe(load16k(os.path.join(wdir, f)),
                                     language="ko", beam_size=1, vad_filter=False)
        asr[f] = norm(" ".join(s.text for s in segs))
    texts = [norm(kr[i].get("content")) for i in cand]
    K, M = len(clipfiles), len(cand)
    NEG = -1e9
    dp = [[NEG] * (M + 1) for _ in range(K + 1)]
    bk = [[None] * (M + 1) for _ in range(K + 1)]
    dp[0][0] = 0
    for j in range(1, M + 1):
        dp[0][j] = 0; bk[0][j] = (0, j - 1, 0)
    for i in range(1, K + 1):
        dp[i][0] = 0; bk[i][0] = (i - 1, 0, 0)
    for i in range(1, K + 1):
        for j in range(1, M + 1):
            # skip clip i
            best, act = dp[i-1][j], (i-1, j, 0)
            # skip line j
            if dp[i][j-1] > best:
                best, act = dp[i][j-1], (i, j-1, 0)
            # clip i covers lines [k..j]
            for k in range(j, max(0, j - 3) - 1, -1):
                if dp[i-1][k-1] <= NEG:
                    continue
                r = difflib.SequenceMatcher(None, asr[clipfiles[i-1]], "".join(texts[k-1:j])).ratio()
                if dp[i-1][k-1] + r > best:
                    best, act = dp[i-1][k-1] + r, (i-1, k-1, 1)
            dp[i][j] = best; bk[i][j] = act
    mapping = {}
    i, j = K, M
    while i > 0 or j > 0:
        pi, pj, act = bk[i][j]
        if act == 1:
            for t in range(pj, j):
                mapping[str(cand[t])] = clipfiles[i-1]
        i, j = pi, pj
    res = {"scene": scene, "mapping": mapping, "asr": asr}
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    return res

if __name__ == "__main__":
    for sc in sys.argv[1:]:
        r = run(sc)
        print(sc, "mapped", len(r.get("mapping", {})), flush=True)
