import os, json, sys, time
sys.path.insert(0, r"D:\scoop\opencode-data\limbus_anki")
import asr_pipeline as P

ROOT = r"D:\scoop\opencode-data\limbus_anki"
BANKDIR = r"E:\Steam\steamapps\common\Limbus Company\LimbusCompany_Data\StreamingAssets\Assets\Sound\FMODBuilds\Desktop"
info = json.load(open(os.path.join(ROOT, "scene_info.json"), encoding="utf-8"))
scenes = sorted(sc for sc in info if os.path.exists(os.path.join(BANKDIR, sc + ".assets.bank")))
log = open(os.path.join(ROOT, "logs", "asr_all2.log"), "w", encoding="utf-8")
def w(s): log.write(s + "\n"); log.flush()
w("scenes with bank: %d" % len(scenes))
for k, sc in enumerate(scenes):
    t = time.time()
    try:
        r = P.run(sc)
        w("[%d/%d] %s mapped=%d (%.0fs)" % (k+1, len(scenes), sc, len(r.get("mapping", {})), time.time()-t))
    except Exception as e:
        w("[%d/%d] %s ERR %s" % (k+1, len(scenes), sc, e))
w("DONE")
log.close()
