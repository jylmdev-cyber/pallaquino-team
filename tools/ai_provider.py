"""Compatibilidad CLI; implementación compartida en uasek, sin duplicación."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from uasek.cli import main

if __name__ == '__main__':
    # Move global flags before the central subcommand, accepting either position here.
    args = sys.argv[1:]
    global_args, rest = [], []
    index = 0
    while index < len(args):
        token = args[index]
        if token in ('--root', '--output') and index + 1 < len(args):
            global_args.extend(args[index:index+2])
            index += 2
        elif token.startswith(('--root=', '--output=')) or token == '--verbose':
            global_args.append(token)
            index += 1
        else:
            rest.append(token)
            index += 1
    raise SystemExit(main(global_args + ['provider'] + rest))
