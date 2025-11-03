#!/usr/bin/env python3
"""duplicate_finder.py

Recursively scans a directory and identifies duplicate files.

Features:
- Groups by file size, then by SHA256 of file contents (fast) to find duplicates.
- Optional WAV-aware mode to hash only the audio 'data' chunk (ignoring metadata like bext/XML) for more accurate audio duplicates.
- CLI with dry-run, CSV export, and options to move or delete duplicates.

Usage examples:
  python3 duplicate_finder.py --root "/path/to/library" --extensions .wav .aif --wav-audio-hash --dry-run
  python3 duplicate_finder.py --root ./SFX --move-to ./duplicates --min-size 1024
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import struct
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Iterable, List, Optional, Tuple


def iter_files(root: str, exts: Optional[List[str]] = None) -> Iterable[str]:
    """Yield file paths under root. If exts is given, filter by extensions (case-insensitive)."""
    exts_lc = [e.lower() for e in exts] if exts else None
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if exts_lc:
                if not any(fn.lower().endswith(ext) for ext in exts_lc):
                    continue
            yield os.path.join(dirpath, fn)


def sha256_file(path: str, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def sha256_wav_audio_chunk(path: str) -> Optional[str]:
    """Compute SHA256 of the WAV 'data' chunk only. Returns None if file is not a RIFF/WAV or parsing fails."""
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except Exception:
        return None

    # Look for 'data' chunk in RIFF file. This is a simple scanner, not a full parser.
    idx = 0
    if len(data) < 12:
        return None
    # basic RIFF header check
    if data[0:4] != b'RIFF' or data[8:12] != b'WAVE':
        return None

    # iterate chunks
    idx = 12
    h = hashlib.sha256()
    found = False
    while idx + 8 <= len(data):
        chunk_id = data[idx:idx+4]
        chunk_size = struct.unpack('<I', data[idx+4:idx+8])[0]
        data_start = idx + 8
        data_end = data_start + chunk_size
        if data_end > len(data):
            break
        if chunk_id == b'data':
            h.update(data[data_start:data_end])
            found = True
            break
        # move to next chunk (account for pad byte if size odd)
        pad = 1 if (chunk_size % 2) == 1 else 0
        idx = data_end + pad

    if not found:
        return None
    return h.hexdigest()


def group_by_size(paths: Iterable[str]) -> Dict[int, List[str]]:
    d = defaultdict(list)
    for p in paths:
        try:
            sz = os.path.getsize(p)
        except Exception:
            continue
        d[sz].append(p)
    return d


def find_duplicates(root: str, exts: Optional[List[str]] = None, min_size: int = 1,
                    wav_audio_hash: bool = False, workers: int = 4) -> Dict[str, List[str]]:
    """Return mapping from hash -> list of file paths that share that hash (only groups with >1 are included)."""
    paths = list(iter_files(root, exts))
    # filter by min size
    paths = [p for p in paths if os.path.getsize(p) >= min_size]

    size_groups = group_by_size(paths)

    # candidate paths: only sizes with more than one file
    candidates = [p for sz, ps in size_groups.items() if len(ps) > 1 for p in ps]

    hash_map: Dict[str, List[str]] = defaultdict(list)

    def work(path: str) -> Tuple[str, Optional[str]]:
        # returns (path, hash)
        if wav_audio_hash and path.lower().endswith('.wav'):
            h = sha256_wav_audio_chunk(path)
            if h:
                return (path, 'wav_audio:' + h)
            # fallback to full file hash
        try:
            h = sha256_file(path)
            return (path, 'full:' + h)
        except Exception:
            return (path, None)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for path, h in ex.map(work, candidates):
            if h:
                hash_map[h].append(path)

    # keep only duplicates
    return {h: ps for h, ps in hash_map.items() if len(ps) > 1}


def write_csv_report(dupes: Dict[str, List[str]], out_csv: str) -> None:
    rows = []
    for h, paths in dupes.items():
        size = os.path.getsize(paths[0]) if paths else 0
        for p in paths:
            rows.append({'hash': h, 'size': size, 'path': p})
    fieldnames = ['hash', 'size', 'path']
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description='Find duplicate files recursively (optimized by size then hash).')
    p.add_argument('--root', '-r', required=True, help='Root directory to scan')
    p.add_argument('--extensions', '-e', nargs='*', help='Limit to these extensions, e.g. .wav .aif')
    p.add_argument('--min-size', type=int, default=1, help='Minimum file size in bytes to consider')
    p.add_argument('--wav-audio-hash', action='store_true', help="Hash only WAV 'data' chunk when possible")
    p.add_argument('--workers', type=int, default=4, help='Worker threads for hashing')
    p.add_argument('--dry-run', action='store_true', help='Do not move or delete, only report')
    p.add_argument('--move-to', help='Move duplicates (keeps the first occurrence) into this folder')
    p.add_argument('--delete', action='store_true', help='Delete duplicate files (keep first occurrence)')
    p.add_argument('--csv', help='Write CSV report to this file')
    p.add_argument('--report-limit', type=int, default=20, help='Show up to N files per duplicate group in console')
    args = p.parse_args(argv)

    root = args.root
    if not os.path.isdir(root):
        print('Error: root directory does not exist:', root)
        return 2

    dupes = find_duplicates(root, args.extensions, args.min_size, args.wav_audio_hash, args.workers)

    if not dupes:
        print('No duplicates found.')
        return 0

    # print summary
    print(f'Found {len(dupes)} duplicate groups')
    for h, paths in dupes.items():
        print('-' * 60)
        print('Group hash:', h)
        print('Count:', len(paths), 'Size:', os.path.getsize(paths[0]) if paths else 0)
        for p in paths[:args.report_limit]:
            print(' ', p)
        if len(paths) > args.report_limit:
            print('  ... and', len(paths) - args.report_limit, 'more')

    if args.csv:
        try:
            write_csv_report(dupes, args.csv)
            print('Wrote CSV report to', args.csv)
        except Exception as e:
            print('Error writing CSV:', e)

    # If move or delete, perform operations. Keep the first path as canonical, move/delete the rest.
    if args.move_to or args.delete:
        if args.move_to and args.delete:
            print('Error: cannot use --move-to and --delete together')
            return 2
        if args.move_to and not os.path.isdir(args.move_to):
            try:
                os.makedirs(args.move_to, exist_ok=True)
            except Exception as e:
                print('Error creating move-to directory:', e)
                return 2

        for h, paths in dupes.items():
            keeper = paths[0]
            for duplicate in paths[1:]:
                if args.dry_run:
                    print('[DRY] Would', 'delete' if args.delete else 'move', duplicate)
                    continue
                try:
                    if args.delete:
                        os.remove(duplicate)
                    else:
                        # move
                        dest = os.path.join(args.move_to, os.path.basename(duplicate))
                        # ensure unique name
                        base, ext = os.path.splitext(dest)
                        i = 1
                        while os.path.exists(dest):
                            dest = f"{base}.{i}{ext}"
                            i += 1
                        os.replace(duplicate, dest)
                except Exception as e:
                    print('Error handling duplicate', duplicate, e)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
