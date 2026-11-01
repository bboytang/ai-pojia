#!/usr/bin/env python3
"""Package only the files needed to install the AstrBot plugin."""

import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "main.py", "astrbot_policy.py", "metadata.yaml", "_conf_schema.json",
    "README.md", "docs/astrbot.md", "LICENSE", "THIRD_PARTY_NOTICES.md",
    "third_party/gpt-instruct/LICENSE", "prompts/ai-pojia.md",
    "skills/ai-pojia/SKILL.md", "skills/ai-pojia/references/demo-contract.md",
)


def build(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / "astrbot_plugin_ai_pojia-v0.3.0.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name in FILES:
            item = zipfile.ZipInfo("astrbot_plugin_ai_pojia/" + name, (1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            bundle.writestr(item, (ROOT / name).read_bytes())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    print(build(parser.parse_args().output_dir))
