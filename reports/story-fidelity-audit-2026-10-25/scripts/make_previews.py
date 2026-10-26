"""Create report-only thumbnails of the exact saved API image inputs."""
import base64
import io
import json
from pathlib import Path
from PIL import Image, ImageOps

out = Path(__file__).resolve().parents[1]
root = out.parents[1]
manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
previews = {}
for package in manifest["packages"]:
    for ref in package["reference_files"]:
        rel = Path(ref["path"])
        source = root / "tmp/fidelity-audit-2026-10-25/snapshots" / Path(*rel.parts[1:])
        with Image.open(source) as original:
            image = ImageOps.exif_transpose(original).convert("RGB")
            image.thumbnail((720,720))
            stream = io.BytesIO()
            image.save(stream,format="WEBP",quality=82)
        previews[ref["sha256"]] = {"preview_data_url":"data:image/webp;base64,"+base64.b64encode(stream.getvalue()).decode("ascii"),"preview_width":image.width,"preview_height":image.height}
(out / "image-previews.json").write_text(json.dumps(previews),encoding="utf-8")
print(json.dumps({"previews":len(previews),"bytes":(out/'image-previews.json').stat().st_size}))
