import hashlib
import io
import urllib.request
import zipfile
from pathlib import Path

RELEASE = "https://github.com/CAMeL-Lab/camel-tools-data/releases/download/2022.03.21/"

# per-file sha256 values copied from CAMeL's own catalogue.json, which is how
# camel_data verifies an install — the archive itself has no published checksum
PACKAGES = [
    (
        "morphology_db_calima-msa-r13-0.4.0.zip",
        "morphology_db/calima-msa-r13",
        {"morphology.db": "195bc25a333237a2126470da888d7936b59ed3729f9210e0a4194ba43497dd70"},
    ),
    (
        "disambig_mle_calima-msa-r13-0.2.5.zip",
        "disambig_mle/calima-msa-r13",
        {"model.json": "e7d79e7744101b6933f9a4b41063d4b9934488fc8c8b6130a24467e0f0dfe9af"},
    ),
]

TARGET = Path(__file__).resolve().parent / "camel_data" / "data"


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _verified(folder, checksums):
    return all(
        (folder / name).is_file() and _sha256(folder / name) == expected
        for name, expected in checksums.items()
    )


def fetch():
    for archive, destination, checksums in PACKAGES:
        folder = TARGET / destination
        if _verified(folder, checksums):
            print(f"present  {destination}")
            continue

        blob = urllib.request.urlopen(RELEASE + archive).read()
        folder.mkdir(parents=True, exist_ok=True)
        zipfile.ZipFile(io.BytesIO(blob)).extractall(folder)

        if not _verified(folder, checksums):
            raise SystemExit(f"checksum mismatch in {archive}")
        print(f"fetched  {destination}")


if __name__ == "__main__":
    fetch()
