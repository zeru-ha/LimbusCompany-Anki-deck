import mmap, re, json, os, sys, subprocess, struct, ctypes, time
from ctypes import wintypes

ROOT = r"D:\scoop\opencode-data\limbus_anki"
KRD = r"E:\Steam\steamapps\common\Limbus Company\LimbusCompany_Data\Assets\Resources_moved\Localize\kr\StoryData"
BANKDIR = r"E:\Steam\steamapps\common\Limbus Company\LimbusCompany_Data\StreamingAssets\Assets\Sound\FMODBuilds\Desktop"
SC = os.path.join(ROOT, "scenarios")
TMPW = os.path.join(ROOT, "tmp", "wav")
MEDIA = os.path.join(ROOT, "media")
DUMP = os.path.join(ROOT, "cap.dmp")
for d in (SC, TMPW, MEDIA):
    os.makedirs(d, exist_ok=True)

def get_pid():
    p = subprocess.run(["powershell", "-NoProfile", "-Command",
        "(Get-Process LimbusCompany -ErrorAction SilentlyContinue | Sort-Object StartTime | Select-Object -Last 1).Id"],
        capture_output=True, text=True)
    t = p.stdout.strip()
    return int(t) if t.isdigit() else None

def dump_proc(pid, out):
    if os.path.exists(out):
        try: os.remove(out)
        except Exception: pass
    k32 = ctypes.WinDLL("kernel32", use_last_error=True); dbg = ctypes.WinDLL("dbghelp", use_last_error=True)
    h = k32.OpenProcess(0x1F0FFF, False, pid)
    fh = k32.CreateFileW(out, 0x40000000, 0, None, 2, 0x80, None)
    flags = 0x2 | 0x8 | 0x4
    ok = dbg.MiniDumpWriteDump(h, pid, fh, flags, None, None, None)
    k32.CloseHandle(fh); k32.CloseHandle(h)
    return os.path.exists(out) and os.path.getsize(out) > 0

def scan_scenarios(dump):
    pat = b'{"dataList":[{"id":'
    CAP = 2_000_000
    kr_files = [f[3:-5] for f in os.listdir(KRD) if f.startswith("KR_") and f.endswith(".json")]
    f = open(dump, "rb"); mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    s = 0; cnt = 0; found = {}
    while True:
        i = mm.find(pat, s)
        if i < 0 or cnt > 800:
            break
        depth = 0; j = i; end = min(len(mm), i + CAP)
        while j < end:
            c = mm[j]
            if c == 0x7b: depth += 1
            elif c == 0x7d:
                depth -= 1
                if depth == 0: break
            j += 1
        if depth == 0:
            try:
                js = mm[i:j+1].decode("utf-8", "replace")
                d = json.loads(js)
                scn = d.get("dataList", [])
                voices = [e.get("voice") for e in scn if isinstance(e.get("voice"), str)]
                if not voices:
                    cnt += 1; s = i + 10; continue
                pref = None
                m = re.match(r"(S\d{3,4})V?[-_]", voices[0])
                if m: pref = m.group(1)
                else:
                    m = re.match(r"(\dD\d{3})", voices[0])
                    if m: pref = m.group(1)
                # find matching KR scene by prefix + id overlap
                best = None; bestscore = -1
                scn_ids = set(e.get("id") for e in scn if isinstance(e.get("id"), int))
                for kf in kr_files:
                    if pref and not (kf.startswith(pref) or kf[:len(pref)] == pref):
                        continue
                    try:
                        kr = json.load(open(os.path.join(KRD, "KR_" + kf + ".json"), encoding="utf-8"))["dataList"]
                    except Exception:
                        continue
                    kids = set(e.get("id") for e in kr if isinstance(e.get("id"), int))
                    score = len(kids & scn_ids)
                    if score > bestscore:
                        bestscore = score; best = kf
                if best and bestscore > 0 and best not in found:
                    open(os.path.join(SC, best + ".json"), "w", encoding="utf-8").write(js)
                    found[best] = len(voices)
            except Exception:
                pass
        cnt += 1; s = i + 10
    mm.close()
    return found

def extract_fsb(bankpath, outpath):
    d = open(bankpath, "rb").read(); off = d.find(b"FSB5")
    if off < 0: return False
    ver, num, hdr, nt, ds, mode = struct.unpack_from("<6I", d, off + 4)
    open(outpath, "wb").write(d[off:off + 60 + hdr + nt + ds]); return True

def ensure_wavs(scene):
    wdir = os.path.join(TMPW, scene)
    if os.path.isdir(wdir) and any(f.endswith(".wav") for f in os.listdir(wdir)):
        return wdir
    bank = os.path.join(BANKDIR, scene + ".assets.bank")
    if not os.path.exists(bank):
        return None
    fsb = os.path.join(ROOT, "tmp", scene + ".fsb")
    if not extract_fsb(bank, fsb):
        return None
    os.makedirs(wdir, exist_ok=True)
    subprocess.run(["vgmstream-cli", "-i", "-S", "0", "-o", os.path.join(wdir, "?n.wav"), fsb], capture_output=True)
    return wdir

def find_wav(scene, clipname):
    wdir = os.path.join(TMPW, scene)
    p = os.path.join(wdir, clipname + ".wav")
    return p if os.path.exists(p) else None

def main():
    pid = get_pid()
    if not pid:
        print("game not running"); return
    print("pid", pid)
    if not dump_proc(pid, DUMP):
        print("dump failed"); return
    print("dump MB", int(os.path.getsize(DUMP) / 1048576))
    found = scan_scenarios(DUMP)
    print("scenarios found this round:", sorted(found))

    # build scenario_map
    smap = {}
    if os.path.exists(os.path.join(ROOT, "scenario_map.json")):
        smap = json.load(open(os.path.join(ROOT, "scenario_map.json"), encoding="utf-8"))
    for scene in found:
        krp = os.path.join(KRD, "KR_" + scene + ".json")
        if not os.path.exists(krp): continue
        kr = json.load(open(krp, encoding="utf-8"))["dataList"]
        id2idx = {}
        for i, e in enumerate(kr):
            if isinstance(e.get("id"), int): id2idx.setdefault(e["id"], i)
        scn = json.load(open(os.path.join(SC, scene + ".json"), encoding="utf-8"))["dataList"]
        m = {}
        for e in scn:
            v = e.get("voice"); i = e.get("id")
            if isinstance(v, str) and isinstance(i, int) and i in id2idx:
                m[str(id2idx[i])] = v
        if m: smap[scene] = m
    json.dump(smap, open(os.path.join(ROOT, "scenario_map.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # extract audio for scenes not yet done
    manifest_path = os.path.join(ROOT, "audio_manifest.json")
    manifest = json.load(open(manifest_path, encoding="utf-8")) if os.path.exists(manifest_path) else {}
    done = 0
    for scene, m in smap.items():
        if scene in manifest: continue
        wdir = ensure_wavs(scene)
        if not wdir: continue
        mm = {}
        for idx, clip in m.items():
            w = find_wav(scene, clip)
            if not w: continue
            mp3 = os.path.join(MEDIA, "LC2_%s_%s.mp3" % (scene, clip))
            if not os.path.exists(mp3):
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", w, "-b:a", "96k", mp3], capture_output=True)
            if os.path.exists(mp3): mm[idx] = os.path.basename(mp3)
        manifest[scene] = mm
        done += 1
        print("audio extracted:", scene, len(mm))
    json.dump(manifest, open(manifest_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("scenes in scenario_map:", len(smap), "| audio scenes:", len(manifest))

main()
