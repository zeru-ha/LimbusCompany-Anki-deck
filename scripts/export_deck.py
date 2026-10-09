import zipfile, sqlite3, tempfile, os, csv, json

ROOT = r"D:\scoop\opencode-data\limbus_anki"
APKG = os.path.join(ROOT, "Limbus_Company_Anki.apkg")
OUT = os.path.join(ROOT, "repo", "deck-source")
MODEL = json.load(open(os.path.join(ROOT, "lapis_model.json"), encoding="utf-8"))

os.makedirs(OUT, exist_ok=True)
z = zipfile.ZipFile(APKG)
tmp = os.path.join(tempfile.gettempdir(), "col_export.anki2")
open(tmp, "wb").write(z.read("collection.anki2"))
cur = sqlite3.connect(tmp).cursor()

fields = [f["name"] if isinstance(f, dict) else f for f in MODEL["fields"]]
with open(os.path.join(OUT, "notes.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(fields + ["Tags"])
    for flds, tags in cur.execute("select flds, tags from notes"):
        parts = flds.split("\x1f")
        parts += [""] * (len(fields) - len(parts))
        w.writerow(parts + [tags.strip()])
print("notes.csv rows:", cur.execute("select count(*) from notes").fetchone()[0])

# templates
tpl_dir = os.path.join(OUT, "templates")
os.makedirs(tpl_dir, exist_ok=True)
for i, t in enumerate(MODEL["templates"], 1):
    base = "card%d_%s" % (i, t["name"].replace("/", "_").replace(" ", "_"))
    open(os.path.join(tpl_dir, base + ".front.html"), "w", encoding="utf-8").write(t["qfmt"])
    open(os.path.join(tpl_dir, base + ".back.html"), "w", encoding="utf-8").write(t["afmt"])
open(os.path.join(tpl_dir, "style.css"), "w", encoding="utf-8").write(MODEL["css"])
print("done ->", OUT)
