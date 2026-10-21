"""Build a source distribution ZIP with per-file checksums; no dependencies."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from uasek.common import KIT_ROOT, KitError, files, is_sensitive, now
from uasek.operations import scan
from uasek import __version__
from uasek.checkpoints import list_checkpoints


def package(destination, dry_run=False):
    destination = Path(destination).resolve()
    if destination.exists():
        raise KitError('Destino existente; no se reemplaza.')
    report = scan(KIT_ROOT)
    if any(item['severity'] == 'high' for item in report['findings']):
        raise KitError('Revisar hallazgos de seguridad antes de empaquetar.')
    list_checkpoints(KIT_ROOT)  # Fail closed if versioned recovery records are damaged.
    selected = [p for p in files(KIT_ROOT) if not is_sensitive(p)
                and p.suffix.lower() not in {'.whl', '.pyc'} and p != destination
                and (p.suffix.lower() != '.zip' or p.relative_to(KIT_ROOT).as_posix().startswith('project-memory/checkpoints/'))]
    manifest = {'created_at':now(),'version':__version__,'algorithm':'sha256','files':{}}
    data = []
    for path in selected:
        relative = path.relative_to(KIT_ROOT).as_posix()
        content = path.read_bytes()
        manifest['files'][relative] = hashlib.sha256(content).hexdigest()
        data.append((relative, content))
    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destination, 'x', zipfile.ZIP_DEFLATED) as archive:
            for relative, content in data:
                archive.writestr('UNIVERSAL-AI-SOFTWARE-KIT/' + relative, content)
            archive.writestr('UNIVERSAL-AI-SOFTWARE-KIT/PACKAGE_MANIFEST.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    return {'destination':str(destination),'files':len(data),'dry_run':dry_run}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(package(args.destination, args.dry_run), ensure_ascii=False, indent=2))
    except (KitError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
