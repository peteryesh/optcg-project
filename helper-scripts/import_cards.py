"""
import_cards.py
==============
Reads the raw optcg_info.json file and populates the optcg.db SQLite database.

Usage:
    python import_cards.py --json optcg_info.json --db optcg.db

The database must already exist (run create_db.py first).

Notes:
    - Blocks must be inserted manually before running this script since
      block names and active status are not in the source data.
    - artist is intentionally left NULL -- to be populated later.
    - deck_restriction is intentionally left out -- to be populated manually.
    - card_restrictions, banned_cards, pair_bans, standard_exceptions
      are not populated here -- those are managed manually.
"""

import argparse
import json
import re
import sqlite3
from pathlib import Path


# --- Helpers ------------------------------------------------------------------

def extract_set_id(set_name: str) -> str:
    """Derive a set ID from the set name.
    Prefers the bracketed code e.g. [OP01], falls back to a slugified name."""
    m = re.search(r'\[([^\]]+)\]', set_name)
    if m:
        return m.group(1)
    return re.sub(r'[^A-Za-z0-9]+', '-', set_name).strip('-')


def parse_int(value) -> int | None:
    """Convert a value to int, returning None for missing or dash values."""
    if value in (None, '', '-'):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_block(value) -> int | None:
    """Convert block value to int, returning None for missing or dash values."""
    return parse_int(value)


# --- Import -------------------------------------------------------------------

def import_cards(json_path: str, db_path: str) -> None:
    if not Path(json_path).exists():
        print(f"Error: JSON file not found: {json_path}")
        raise SystemExit(1)

    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        print("Run create_db.py first.")
        raise SystemExit(1)

    with open(json_path, encoding='utf-8') as f:
        source = json.load(f)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Track counts for summary
    counts = {
        'sets': 0,
        'cards': 0,
        'colors': 0,
        'types': 0,
        'attributes': 0,
        'alts': 0,
        'skipped': 0,
    }
    errors = []

    # --- Pass 0: seed blocks from source data --------------------------------
    # Block values in the source are 1-4 (or "-" for unknown).
    # We insert them here so the cards.block foreign key resolves.
    # Set active=1 for all by default -- update manually as blocks rotate.
    print("Pass 0: inserting blocks...")
    block_values = set()
    for card in source.values():
        b = parse_block(card.get("block"))
        if b is not None:
            block_values.add(b)

    for b in sorted(block_values):
        cur.execute(
            "INSERT OR IGNORE INTO blocks (id, name, active) VALUES (?, ?, 1)",
            (b, f"Block {b}")
        )
    conn.commit()
    print(f"  {len(block_values)} blocks seeded: {sorted(block_values)}")

    # --- Pass 1: collect and insert all unique sets ---------------------------
    print("Pass 1: inserting sets...")
    seen_sets = {}
    for card in source.values():
        set_name = card.get('set', '').strip()
        if not set_name:
            continue
        set_id = extract_set_id(set_name)
        if set_id not in seen_sets:
            seen_sets[set_id] = set_name

    for set_id, set_name in seen_sets.items():
        cur.execute(
            "INSERT OR IGNORE INTO sets (id, name) VALUES (?, ?)",
            (set_id, set_name)
        )
        if cur.rowcount:
            counts['sets'] += 1

    conn.commit()
    print(f"  {counts['sets']} sets inserted ({len(seen_sets)} total unique sets)")

    # --- Pass 2: insert reference values (colors, types, attributes) ----------
    print("Pass 2: inserting reference values...")
    for card in source.values():
        for color in card.get('color', []):
            color = color.strip()
            if color:
                cur.execute("INSERT OR IGNORE INTO colors (name) VALUES (?)", (color,))
                if cur.rowcount:
                    counts['colors'] += 1

        for t in card.get('card_type', []):
            t = t.strip()
            if t:
                cur.execute("INSERT OR IGNORE INTO types (name) VALUES (?)", (t,))
                if cur.rowcount:
                    counts['types'] += 1

        for attr in card.get('attribute', []):
            attr = attr.strip()
            if attr:
                cur.execute("INSERT OR IGNORE INTO attributes (name) VALUES (?)", (attr,))
                if cur.rowcount:
                    counts['attributes'] += 1

    conn.commit()
    print(f"  {counts['colors']} colors, {counts['types']} types, {counts['attributes']} attributes inserted")

    # --- Pass 3: insert cards and relationships --------------------------------
    print("Pass 3: inserting cards...")
    for card_id, card in source.items():
        try:
            set_name = card.get('set', '').strip()
            set_id = extract_set_id(set_name) if set_name else None

            if not set_id:
                errors.append(f"[{card_id}] {card.get('name')} -- missing set, skipped")
                counts['skipped'] += 1
                continue

            # --- Insert card --------------------------------------------------
            cur.execute(
                """
                INSERT OR IGNORE INTO cards
                    (id, set_id, name, class, rarity, block, cost, power, counter, raw_effect)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card_id,
                    set_id,
                    card.get('name', '').strip(),
                    card.get('class', '').strip(),
                    card.get('rarity', '').strip() or None,
                    parse_block(card.get('block')),
                    parse_int(card.get('cost')),
                    parse_int(card.get('power')),
                    parse_int(card.get('counter')),
                    card.get('effect', '').strip() or None,
                )
            )
            if cur.rowcount:
                counts['cards'] += 1

            # --- Insert colors ------------------------------------------------
            for color in card.get('color', []):
                color = color.strip()
                if color:
                    cur.execute(
                        "INSERT OR IGNORE INTO card_colors (card_id, color) VALUES (?, ?)",
                        (card_id, color)
                    )

            # --- Insert types -------------------------------------------------
            for t in card.get('card_type', []):
                t = t.strip()
                if t:
                    cur.execute(
                        "INSERT OR IGNORE INTO card_types (card_id, type) VALUES (?, ?)",
                        (card_id, t)
                    )

            # --- Insert attributes --------------------------------------------
            for attr in card.get('attribute', []):
                attr = attr.strip()
                if attr:  # skip empty string attributes [""]
                    cur.execute(
                        "INSERT OR IGNORE INTO card_attributes (card_id, attribute) VALUES (?, ?)",
                        (card_id, attr)
                    )

            # --- Insert alternate prints --------------------------------------
            for alt in card.get('alts', []):
                alt_id = alt.get('alt_code', '').strip()
                if not alt_id:
                    continue
                cur.execute(
                    "INSERT OR IGNORE INTO card_alts (id, card_id, set_name) VALUES (?, ?, ?)",
                    (
                        alt_id,
                        card_id,
                        alt.get('set', '').strip() or None,
                    )
                )
                if cur.rowcount:
                    counts['alts'] += 1

        except Exception as e:
            errors.append(f"[{card_id}] {card.get('name')} -- {e}")
            counts['skipped'] += 1

    conn.commit()

    # --- Pass 4: insert known aliases -----------------------------------------
    # Aliases are hardcoded here since they come from effect text, not a
    # structured field. Add new entries manually as new cards are released.
    print("Pass 4: inserting aliases...")
    aliases = [
        ("EB02-016", "Tony Tony.Chopper"),
        ("EB02-024", "Usopp"),
        ("EB04-038", "Trafalgar Law"),
        ("EB04-038", "Donquixote Rosinante"),
        ("OP01-121", "Kouzuki Oden"),
        ("OP02-042", "Kouzuki Oden"),
        ("OP03-122", "Usopp"),
        ("OP04-099", "Charlotte Linlin"),
        ("P-027",    "Franky"),
    ]
    alias_count = 0
    for card_id, alias in aliases:
        cur.execute(
            "INSERT OR IGNORE INTO card_aliases (card_id, alias) VALUES (?, ?)",
            (card_id, alias)
        )
        if cur.rowcount:
            alias_count += 1
    conn.commit()
    print(f"  {alias_count} aliases inserted")

    # --- Pass 5: insert card restrictions -------------------------------------
    # Hardcoded deck restrictions derived from Leader effect text.
    # Add new entries manually as new cards are released.
    # Each tuple: (card_id, type_value, color_value, attribute_value)
    # Only one of the three value columns should be non-None per row.
    print("Pass 5: inserting card restrictions...")
    restrictions = [
        ("P-117", "East Blue", None, None),  # Nami -- {East Blue} type only
    ]
    restriction_count = 0
    for card_id, type_value, color_value, attribute_value in restrictions:
        # Ensure the value exists in its reference table before inserting
        if type_value:
            cur.execute("INSERT OR IGNORE INTO types (name) VALUES (?)", (type_value,))
        if color_value:
            cur.execute("INSERT OR IGNORE INTO colors (name) VALUES (?)", (color_value,))
        if attribute_value:
            cur.execute("INSERT OR IGNORE INTO attributes (name) VALUES (?)", (attribute_value,))
        cur.execute(
            """INSERT OR IGNORE INTO card_restrictions
               (card_id, type_value, color_value, attribute_value)
               VALUES (?, ?, ?, ?)""",
            (card_id, type_value, color_value, attribute_value)
        )
        if cur.rowcount:
            restriction_count += 1
    conn.commit()
    print(f"  {restriction_count} restrictions inserted")

    # --- Pass 6: insert banned cards ------------------------------------------
    # (card_id, reason, banned_at)
    print("Pass 6: inserting banned cards...")
    banned_cards = [
        # ("OP01-XXX", "power level", "2024-01-01"),
        ("OP06-047", None, "2026-04-01"), # Charlotte Pudding
        ("OP03-040", None, "2025-08-30"), # Nami Leader
        ("OP06-086", None, "2025-04-01"), # Gecko Moria
        ("ST10-001", None, "2024-09-06"), # Trafalgar Law Leader
        ("OP06-116", None, "2024-06-21"), # Reject Event
    ]
    banned_count = 0
    for card_id, reason, banned_at in banned_cards:
        cur.execute(
            "INSERT OR IGNORE INTO banned_cards (card_id, reason, banned_at) VALUES (?, ?, ?)",
            (card_id, reason, banned_at)
        )
        if cur.rowcount:
            banned_count += 1
    conn.commit()
    print(f"  {banned_count} banned cards inserted")

    # --- Pass 7: insert pair bans ---------------------------------------------
    # (card_id_a, card_id_b, reason) -- card_id_a must be alphabetically less
    # than card_id_b. Use sorted() to enforce this before adding entries.
    print("Pass 7: inserting pair bans...")
    pair_bans = [
        # ("OP01-XXX", "OP02-XXX", "combo too strong"),
        ("OP11-040", "OP11-067", None), # UP Luffy and Charlotte Katakuri
        ("OP08-069", "OP11-040", None), # Charlotte Linlin and UP Luffy
        ("OP07-115", "EB04-058", None), # Re-Quasar and Borsalino
    ]
    pair_ban_count = 0
    for card_id_a, card_id_b, reason in pair_bans:
        card_id_a, card_id_b = sorted([card_id_a, card_id_b])
        cur.execute(
            "INSERT OR IGNORE INTO pair_bans (card_id_a, card_id_b, reason) VALUES (?, ?, ?)",
            (card_id_a, card_id_b, reason)
        )
        if cur.rowcount:
            pair_ban_count += 1
    conn.commit()
    print(f"  {pair_ban_count} pair bans inserted")

    # --- Pass 8: insert standard exceptions -----------------------------------
    # (card_id, reason)
    print("Pass 8: inserting standard exceptions...")
    standard_exceptions = [
        ("EB01-006", None),
        ("EB02-061", None),
        ("OP01-016", None),
        ("OP01-039", None),
        ("OP01-055", None),
        ("OP01-120", None),
        ("OP02-005", None),
        ("OP02-013", None),
        ("OP02-068", None),
        ("OP03-008", None),
        ("OP03-044", None),
        ("OP03-048", None),
        ("OP03-072", None),
        ("OP03-097", None),
        ("OP03-122", None),
        ("OP04-016", None),
        ("OP04-077", None),
        ("OP04-083", None),
        ("OP04-096", None),
        ("OP05-069", None),
        ("OP05-074", None),
        ("OP05-119", None),
        ("OP06-118", None),
        ("OP06-119", None),
        ("OP07-051", None),
        ("OP08-118", None),
        ("OP09-004", None),
        ("OP09-051", None),
        ("OP09-093", None),
        ("OP09-118", None),
        ("OP09-119", None),
        ("OP10-119", None),
        ("OP11-118", None),
        ("OP12-118", None),
        ("OP13-118", None),
        ("OP13-119", None),
        ("OP13-120", None),
        ("OP14-119", None),
        ("OP15-118", None),
        ("ST01-011", None),
        ("ST02-007", None),
        ("ST06-008", None),
    ]
    exception_count = 0
    for card_id, reason in standard_exceptions:
        cur.execute(
            "INSERT OR IGNORE INTO standard_exceptions (card_id, reason) VALUES (?, ?)",
            (card_id, reason)
        )
        if cur.rowcount:
            exception_count += 1
    conn.commit()
    print(f"  {exception_count} standard exceptions inserted")

    conn.close()

    # --- Summary --------------------------------------------------------------
    print("\n--- Import complete ---")
    print(f"  Sets:       {counts['sets']}")
    print(f"  Cards:      {counts['cards']}")
    print(f"  Colors:     {counts['colors']} unique")
    print(f"  Types:      {counts['types']} unique")
    print(f"  Attributes: {counts['attributes']} unique")
    print(f"  Alts:       {counts['alts']}")
    print(f"  Skipped:    {counts['skipped']}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
    else:
        print("\nNo errors.")

    print("\nNote: blocks, card_restrictions, banned_cards, pair_bans,")
    print("and standard_exceptions must be populated manually.")


# --- Entry point --------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import OPTCG card data into SQLite")
    parser.add_argument("--json", required=True, help="Path to optcg_info.json")
    parser.add_argument("--db",   required=True, help="Path to optcg.db")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    import_cards(args.json, args.db)