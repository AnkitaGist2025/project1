#!/usr/bin/env python3
"""Command-line tool to scan a folder and generate a summary report."""

import argparse
import os
import sys
from collections import Counter
from datetime import datetime


def format_size(size_bytes):
    """Convert bytes to a human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def scan_folder(folder_path, filter_exts=None):
    """Scan all files in a folder and return stats.

    Args:
        folder_path: Directory to scan.
        filter_exts: Optional set of lowercase extensions (e.g. {'.py', '.txt'})
                     to include. If None, all files are included.
    """
    total_files = 0
    total_size = 0
    largest_file = None
    largest_size = 0
    ext_counter = Counter()
    ext_sizes = Counter()
    name_counter = Counter()

    all_files = []

    for root, _, files in os.walk(folder_path):
        for name in files:
            ext = os.path.splitext(name)[1].lower() or "(no extension)"

            if filter_exts and ext not in filter_exts:
                continue

            filepath = os.path.join(root, name)
            try:
                size = os.path.getsize(filepath)
                mtime = os.path.getmtime(filepath)
            except OSError:
                continue

            total_files += 1
            total_size += size

            if size > largest_size:
                largest_size = size
                largest_file = filepath

            ext_counter[ext] += 1
            ext_sizes[ext] += size
            name_counter[name] += 1

            all_files.append((filepath, mtime, size))

    all_files.sort(key=lambda f: f[1])
    oldest_files = all_files[:5]
    new_files = all_files[-5:][::-1]

    duplicates = {name: count for name, count in name_counter.items() if count > 1}

    return {
        "total_files": total_files,
        "total_size": total_size,
        "largest_file": largest_file,
        "largest_size": largest_size,
        "ext_counter": ext_counter,
        "ext_sizes": ext_sizes,
        "newest_files": newest_files,
        "oldest_files": oldest_files,
        "duplicates": duplicates,
    }


def build_report(folder_path, stats, filter_exts=None):
    """Build the report string."""
    lines = []
    lines.append("=" * 60)
    lines.append("FOLDER SCAN REPORT")
    lines.append("=" * 60)
    lines.append(f"Folder:    {os.path.abspath(folder_path)}")
    lines.append(f"Scanned:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if filter_exts:
        lines.append(f"Filter:    {', '.join(sorted(filter_exts))}")
    lines.append("")
    lines.append(f"Total files:   {stats['total_files']}")
    lines.append(f"Total size:    {format_size(stats['total_size'])}")
    lines.append("")

    if stats["largest_file"]:
        lines.append(f"Largest file:  {stats['largest_file']}")
        lines.append(f"               {format_size(stats['largest_size'])}")
    else:
        lines.append("Largest file:  (none)")

    lines.append("")
    lines.append("-" * 60)
    lines.append("5 NEWEST FILES (by date modified)")
    lines.append("-" * 60)
    if stats["newest_files"]:
        for filepath, mtime, size in stats["newest_files"]:
            modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"  {modified}  {format_size(size):>10}  {filepath}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("-" * 60)
    lines.append("5 OLDEST FILES (by date modified)")
    lines.append("-" * 60)
    if stats["oldest_files"]:
        for filepath, mtime, size in stats["oldest_files"]:
            modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"  {modified}  {format_size(size):>10}  {filepath}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("-" * 60)
    lines.append("DUPLICATE FILE NAMES")
    lines.append("-" * 60)
    duplicates = stats["duplicates"]
    if duplicates:
        lines.append(f"  {len(duplicates)} duplicate name(s) found:")
        lines.append("")
        for name, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {name:<40} {count} copies")
    else:
        lines.append("  No duplicate file names found.")

    lines.append("")
    lines.append("-" * 60)
    lines.append(f"{'Extension':<20} {'Count':>8} {'Total Size':>15}")
    lines.append("-" * 60)

    for ext, count in stats["ext_counter"].most_common():
        size_str = format_size(stats["ext_sizes"][ext])
        lines.append(f"{ext:<20} {count:>8} {size_str:>15}")

    lines.append("-" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Scan a folder and generate a summary report.")
    parser.add_argument("folder", help="Path to the folder to scan")
    parser.add_argument("-o", "--output", help="Output report file path (default: scan_report.txt)")
    parser.add_argument(
        "-e", "--ext",
        nargs="+",
        metavar="EXT",
        help="Filter by file extension(s), e.g. -e .py .txt .md",
    )
    args = parser.parse_args()

    folder = args.folder
    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    filter_exts = None
    if args.ext:
        filter_exts = {e if e.startswith(".") else f".{e}" for e in args.ext}
        filter_exts = {e.lower() for e in filter_exts}

    stats = scan_folder(folder, filter_exts=filter_exts)
    report = build_report(folder, stats, filter_exts=filter_exts)

    print(report)

    output_path = args.output or os.path.join(folder, "scan_report.txt")
    with open(output_path, "w") as f:
        f.write(report + "\n")
    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
