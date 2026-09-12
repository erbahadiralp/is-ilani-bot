"""Package only reviewed source/config/docs; excludes secrets and local state."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
ROOT = Path(__file__).resolve().parents[1]
files = list(ROOT.glob("*.py"))
for folder in ("scrapers", "tools", "tests"):
    files.extend((ROOT / folder).glob("*.py"))
for name in ("companies.json", "programs.json", "source_audit.json", "job_link_audit.json", "program_audit.json", "requirements.txt", ".env.example", "turkiye_yeni_mezun_sirket_takip_listesi.md", "SOURCE_COVERAGE.md", "BANK_COVERAGE.md", "TRACKING.md", "SERVER_UPDATE.md", "README.md", "PROJE_DOKUMANTASYONU.md"):
    files.append(ROOT / name)
files.extend((ROOT / "certificates").glob("*.pem"))
files = sorted(set(files))
out = ROOT / "dist"
out.mkdir(exist_ok=True)
target = out / "job-bot-update.zip"
manifest = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with ZipFile(target,"w",ZIP_DEFLATED) as archive:
    for p in files:
        archive.write(p,p.relative_to(ROOT).as_posix())
    archive.writestr("RELEASE_MANIFEST.json",json.dumps(manifest,indent=2))
with ZipFile(target) as archive:
    assert archive.testzip() is None
    assert ".env" not in archive.namelist()
    assert not any(n.endswith((".db", ".sqlite", ".log")) for n in archive.namelist())
print(json.dumps({"path":str(target),"files":len(files),"sha256":hashlib.sha256(target.read_bytes()).hexdigest()}))
