"""
create_db.py
============
Creates a local SQLite database for the One Piece TCG card data.

Usage:
    python create_db.py

Creates:
    optcg.db -- SQLite database with all tables ready to populate
"""

import sqlite3
from pathlib import Path

DB_PATH = "optcg.db"


def create_database():
    db_exists = Path(DB_PATH).exists()
    if db_exists:
        print(f"Database already exists at {DB_PATH}. Skipping creation.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # --- Blocks ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE blocks (
            id      INTEGER PRIMARY KEY,
            name    TEXT NOT NULL,
            active  INTEGER NOT NULL DEFAULT 1
        )
    """)

    # --- Sets -----------------------------------------------------------------
    cur.execute("""
        CREATE TABLE sets (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            released_at TEXT
        )
    """)

    # --- Cards ----------------------------------------------------------------
    cur.execute("""
        CREATE TABLE cards (
            id          TEXT PRIMARY KEY,
            set_id      TEXT NOT NULL REFERENCES sets(id),
            name        TEXT NOT NULL,
            class       TEXT NOT NULL,
            rarity      TEXT,
            block       INTEGER REFERENCES blocks(id),
            cost        INTEGER,
            power       INTEGER,
            counter     INTEGER,
            raw_effect  TEXT,
            artist      TEXT
        )
    """)

    # --- Reference tables -----------------------------------------------------
    # Canonical lists of valid types, colors, and attributes.
    # Updated as new cards introduce new values via INSERT OR IGNORE in the
    # import script -- no manual intervention needed when new sets are added.
    cur.execute("""
        CREATE TABLE types (
            name    TEXT PRIMARY KEY
        )
    """)

    cur.execute("""
        CREATE TABLE colors (
            name    TEXT PRIMARY KEY
        )
    """)

    cur.execute("""
        CREATE TABLE attributes (
            name    TEXT PRIMARY KEY
        )
    """)

    # --- Card colors ----------------------------------------------------------
    cur.execute("""
        CREATE TABLE card_colors (
            card_id     TEXT NOT NULL REFERENCES cards(id),
            color       TEXT NOT NULL REFERENCES colors(name),
            PRIMARY KEY (card_id, color)
        )
    """)

    # --- Card types -----------------------------------------------------------
    cur.execute("""
        CREATE TABLE card_types (
            card_id     TEXT NOT NULL REFERENCES cards(id),
            type        TEXT NOT NULL REFERENCES types(name),
            PRIMARY KEY (card_id, type)
        )
    """)

    # --- Card attributes ------------------------------------------------------
    cur.execute("""
        CREATE TABLE card_attributes (
            card_id     TEXT NOT NULL REFERENCES cards(id),
            attribute   TEXT NOT NULL REFERENCES attributes(name),
            PRIMARY KEY (card_id, attribute)
        )
    """)

    # --- Alternate prints -----------------------------------------------------
    # The alt id is sufficient to derive the image path on the frontend.
    cur.execute("""
        CREATE TABLE card_alts (
            id          TEXT PRIMARY KEY,
            card_id     TEXT NOT NULL REFERENCES cards(id),
            set_name    TEXT,
            artist      TEXT
        )
    """)

    # --- Card restrictions ----------------------------------------------------
    # One row per restriction per card. Each column references its own
    # lookup table so only valid values can be inserted. Most cards have
    # no rows here -- only cards like the Nami leader that impose
    # deckbuilding rules.
    cur.execute("""
        CREATE TABLE card_restrictions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id         TEXT NOT NULL REFERENCES cards(id),
            type_value      TEXT REFERENCES types(name),
            color_value     TEXT REFERENCES colors(name),
            attribute_value TEXT REFERENCES attributes(name),
            CHECK (
                (type_value IS NOT NULL) +
                (color_value IS NOT NULL) +
                (attribute_value IS NOT NULL) = 1
            )
        )
    """)

    # --- Banned cards ---------------------------------------------------------
    cur.execute("""
        CREATE TABLE banned_cards (
            card_id     TEXT PRIMARY KEY REFERENCES cards(id),
            reason      TEXT,
            banned_at   TEXT
        )
    """)

    # --- Pair bans ------------------------------------------------------------
    cur.execute("""
        CREATE TABLE pair_bans (
            card_id_a   TEXT NOT NULL REFERENCES cards(id),
            card_id_b   TEXT NOT NULL REFERENCES cards(id),
            reason      TEXT,
            PRIMARY KEY (card_id_a, card_id_b),
            CHECK (card_id_a < card_id_b)
        )
    """)

    # --- Standard exceptions --------------------------------------------------
    cur.execute("""
        CREATE TABLE standard_exceptions (
            card_id     TEXT PRIMARY KEY REFERENCES cards(id),
            reason      TEXT
        )
    """)

    # --- Card aliases ---------------------------------------------------------
    # Cards that also respond to another name in ability effect resolution.
    # Does not affect deck building -- only used when matching [Name] targets
    # in ability effects. One row per alias per card.
    cur.execute("""
        CREATE TABLE card_aliases (
            card_id     TEXT NOT NULL REFERENCES cards(id),
            alias       TEXT NOT NULL,
            PRIMARY KEY (card_id, alias)
        )
    """)

    # --- Indexes --------------------------------------------------------------
    cur.execute("CREATE INDEX idx_cards_set          ON cards(set_id)")
    cur.execute("CREATE INDEX idx_cards_class        ON cards(class)")
    cur.execute("CREATE INDEX idx_cards_cost         ON cards(cost)")
    cur.execute("CREATE INDEX idx_cards_block        ON cards(block)")
    cur.execute("CREATE INDEX idx_pair_bans_a        ON pair_bans(card_id_a)")
    cur.execute("CREATE INDEX idx_pair_bans_b        ON pair_bans(card_id_b)")
    cur.execute("CREATE INDEX idx_restrictions_card  ON card_restrictions(card_id)")
    cur.execute("CREATE INDEX idx_aliases_card       ON card_aliases(card_id)")
    cur.execute("CREATE INDEX idx_aliases_alias      ON card_aliases(alias)")

    conn.commit()
    conn.close()

    print(f"Database created at {DB_PATH}")
    print("\nTables created:")
    print("  blocks               -- rotation groups, active flag controls standard eligibility")
    print("  sets                 -- organisational groupings for display only")
    print("  cards                -- one row per card")
    print("  card_colors          -- one row per color per card")
    print("  card_types           -- one row per type per card")
    print("  card_attributes      -- one row per attribute per card")
    print("  card_alts            -- one row per alternate print per card")
    print("  types                -- canonical list of valid card types")
    print("  colors               -- canonical list of valid card colors")
    print("  attributes           -- canonical list of valid card attributes")
    print("  card_restrictions    -- deck restrictions per card (type, color, or attribute)")
    print("  banned_cards         -- cards illegal in all formats")
    print("  pair_bans            -- card pairs that cannot coexist in the same deck")
    print("  standard_exceptions  -- cards exempt from block rotation in standard")
    print("  card_aliases         -- name aliases for ability effect resolution")


if __name__ == "__main__":
    create_database()