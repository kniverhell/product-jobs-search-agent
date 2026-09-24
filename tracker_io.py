"""The only sanctioned way to read or write 02-tracker.csv (SKILL.md rule 10).

Works with any header: nothing here assumes a particular column set.

Every write:
  1. quotes every field (QUOTE_ALL), so commas, quotes and newlines in notes can't split a row
  2. writes to a temp file next to the tracker, never to the tracker directly
  3. re-reads the temp file and validates header, row count and column width
  4. refuses to drop rows unless the caller passes allow_row_loss=True (see write_tracker)
  5. copies the current tracker to archive/ with a timestamp
  6. renames the temp file over the tracker (atomic on the same filesystem)

Usage:
    from tracker_io import read_tracker, write_tracker
    rows, fields = read_tracker()
    ... edit rows (list of dicts) ...
    write_tracker(rows, fields)

    python3 tracker_io.py                 # validate the current tracker, change nothing
    python3 tracker_io.py repair          # dry run: report which malformed rows can be realigned
    python3 tracker_io.py repair --write  # realign what can be realigned; leave the rest untouched

Repair realigns a row only when its displaced cells are empty: a row wider than the header whose extra
trailing cells are all blank (typically a spreadsheet export's trailing commas). Those cells are dropped.
Every other malformed row (too short, or overflow holding data, which means something shifted mid-row)
is reported and written back unchanged, for a person to fix. `integrity` mode may run repair.
"""
import csv
import os
import shutil
import sys
import tempfile
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
TRACKER = os.path.join(HERE, "02-tracker.csv")


class TrackerError(Exception):
    pass


def _validate(path, fields):
    """Return the data row count if every row is exactly as wide as the header; raise otherwise."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header != fields:
            raise TrackerError(f"header mismatch in {path}: {header} != {fields}")
        n = 0
        for i, row in enumerate(reader, start=2):
            if len(row) != len(fields):
                raise TrackerError(f"{path} record {i}: {len(row)} fields, expected {len(fields)} "
                                   f"(first field={row[0] if row else '?'!r})")
            n += 1
    return n


def _read_records(path):
    """Return (header, records) as raw lists, without checking width."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        return header, list(reader)


def _atomic_write(path, header, records):
    """Write header + records (lists) to a temp file, back up the original, rename over it."""
    fd, tmp = tempfile.mkstemp(prefix=".02-tracker.", suffix=".tmp", dir=os.path.dirname(path) or ".")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, quoting=csv.QUOTE_ALL)
            w.writerow(header)
            w.writerows(records)
        _, written = _read_records(tmp)
        if written != records:
            raise TrackerError("temp file does not round-trip; nothing written")
        backup = None
        if os.path.exists(path):
            archive = os.path.join(os.path.dirname(os.path.abspath(path)), "archive")
            os.makedirs(archive, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = os.path.join(archive, f"{os.path.basename(path)}.bak-{stamp}")
            shutil.copy2(path, backup)
        os.replace(tmp, path)
        return backup
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def read_tracker(path=TRACKER):
    """Return (rows, fieldnames). Raises TrackerError if any row is malformed."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
    key = fields[0] if fields else "?"
    bad = [r.get(key, "?") for r in rows if None in r or any(v is None for v in r.values())]
    if bad:
        raise TrackerError(f"malformed rows (wrong column count): {bad}. "
                           f"Run `python3 tracker_io.py repair` to see which can be realigned.")
    return rows, fields


def write_tracker(rows, fields, path=TRACKER, allow_row_loss=False):
    """Validate, back up, and atomically replace the tracker. Returns the backup path.

    Shrink guard: refuses to write fewer rows than the file currently holds. The current count is taken
    from raw CSV records, so it works even when the existing file has malformed rows.

    allow_row_loss=True turns the shrink guard off, and nothing else. Use it only for a deliberate removal
    (a dedup merge, or a row the user asked to delete), and report how many rows were removed and which.
    """
    fields = list(fields)
    for r in rows:
        extra = set(r) - set(fields)
        if extra:
            raise TrackerError(f"row {r.get(fields[0], '?')} has fields not in header: {sorted(map(str, extra))}")

    if os.path.exists(path) and not allow_row_loss:
        _, old_records = _read_records(path)
        if len(rows) < len(old_records):
            raise TrackerError(f"refusing to shrink tracker from {len(old_records)} to {len(rows)} rows "
                               f"(pass allow_row_loss=True if intended, and report which rows)")

    records = [[r.get(k, "") for k in fields] for r in rows]
    backup = _atomic_write(path, fields, records)
    n = _validate(path, fields)
    if n != len(rows):
        raise TrackerError(f"wrote {n} rows, expected {len(rows)}")
    return backup


def repair_tracker(path=TRACKER, write=False):
    """Realign rows whose displaced cells are empty; report every other malformed row untouched.

    Returns (realigned, untouched): lists of (record_number, first_field, reason).
    With write=False nothing is changed. With write=True the file is rewritten only if at least one row
    was realigned; untouched rows are written back with the same values.
    """
    header, records = _read_records(path)
    width = len(header)
    realigned, untouched, out = [], [], []
    for i, row in enumerate(records, start=2):
        first = row[0] if row else ""
        if len(row) == width:
            out.append(row)
        elif len(row) > width and all(c.strip() == "" for c in row[width:]):
            realigned.append((i, first, f"dropped {len(row) - width} empty trailing cell(s)"))
            out.append(row[:width])
        else:
            why = (f"{len(row)} fields, header has {width}: "
                   + ("too short, can't tell which cells are missing" if len(row) < width
                      else "extra cells hold data, so something shifted mid-row"))
            untouched.append((i, first, why))
            out.append(row)
    if write and realigned:
        if len(out) != len(records):
            raise TrackerError("repair would change the row count; nothing written")
        _atomic_write(path, header, out)
    return realigned, untouched


def _main(argv):
    if argv[:1] == ["repair"]:
        write = "--write" in argv[1:]
        realigned, untouched = repair_tracker(write=write)
        verb = "realigned" if write else "would realign"
        for i, first, why in realigned:
            print(f"{verb:14} record {i} ({first!r}): {why}")
        for i, first, why in untouched:
            print(f"{'left as-is':14} record {i} ({first!r}): {why}")
        if not realigned and not untouched:
            print("ok    no malformed rows")
        return 1 if untouched else 0
    try:
        rows, fields = read_tracker()
        n = _validate(TRACKER, fields)
    except TrackerError as e:
        print(f"FAIL  {e}")
        return 1
    print(f"ok    {n} rows x {len(fields)} columns")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
