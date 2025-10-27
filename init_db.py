#!/usr/bin/env python3
"""
Database initialization script for Palette Share
Run this script to create or update the database schema.

Usage:
    python init_db.py
"""

import sqlite3
import os
import sys

DATABASE = 'palettes.db'

def hex_to_rgb(hex_code):
    """Convert hex color to RGB tuple"""
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hsl(r, g, b):
    """Convert RGB to HSL"""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2.0

    if max_c == min_c:
        h = s = 0.0
    else:
        d = max_c - min_c
        s = d / (2.0 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)

        if max_c == r:
            h = (g - b) / d + (6.0 if g < b else 0.0)
        elif max_c == g:
            h = (b - r) / d + 2.0
        else:
            h = (r - g) / d + 4.0
        h /= 6.0

    return (int(h * 360), int(s * 100), int(l * 100))

def init_db():
    """Initialize the database with tables"""
    print(f"Initializing database: {DATABASE}")

    if os.path.exists(DATABASE):
        print(f"Database file already exists: {DATABASE}")
        response = input("Do you want to update the schema? (y/n): ")
        if response.lower() != 'y':
            print("Database initialization cancelled.")
            return

    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row

    print("Creating tables...")
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS palettes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            is_public INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            palette_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (palette_id) REFERENCES palettes (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS colors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            hex_code TEXT NOT NULL,
            r INTEGER NOT NULL,
            g INTEGER NOT NULL,
            b INTEGER NOT NULL,
            h INTEGER NOT NULL,
            s INTEGER NOT NULL,
            l INTEGER NOT NULL,
            name TEXT,
            position INTEGER DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_palettes_user ON palettes(user_id);
        CREATE INDEX IF NOT EXISTS idx_categories_palette ON categories(palette_id);
        CREATE INDEX IF NOT EXISTS idx_colors_category ON colors(category_id);
    ''')
    db.commit()
    print("Tables created successfully.")

    # Migrate existing colors table if needed
    print("Checking for schema updates...")
    cursor = db.execute("PRAGMA table_info(colors)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'r' not in columns:
        print("Migrating colors table to support RGB and HSL...")
        try:
            db.execute('ALTER TABLE colors ADD COLUMN r INTEGER DEFAULT 0')
            db.execute('ALTER TABLE colors ADD COLUMN g INTEGER DEFAULT 0')
            db.execute('ALTER TABLE colors ADD COLUMN b INTEGER DEFAULT 0')
            db.execute('ALTER TABLE colors ADD COLUMN h INTEGER DEFAULT 0')
            db.execute('ALTER TABLE colors ADD COLUMN s INTEGER DEFAULT 0')
            db.execute('ALTER TABLE colors ADD COLUMN l INTEGER DEFAULT 0')

            # Update existing rows
            colors = db.execute('SELECT id, hex_code FROM colors').fetchall()
            print(f"Converting {len(colors)} existing colors...")

            for color in colors:
                try:
                    r, g, b = hex_to_rgb(color['hex_code'])
                    h, s, l = rgb_to_hsl(r, g, b)
                    db.execute('''
                        UPDATE colors SET r = ?, g = ?, b = ?, h = ?, s = ?, l = ?
                        WHERE id = ?
                    ''', (r, g, b, h, s, l, color['id']))
                except Exception as e:
                    print(f"Warning: Could not convert color {color['hex_code']}: {e}")

            db.commit()
            print("Migration completed successfully.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Columns already exist, no migration needed.")
            else:
                print(f"Migration error: {e}")
    else:
        print("Schema is up to date.")

    db.commit()
    db.close()
    print(f"\nDatabase initialization completed successfully!")
    print(f"Database location: {os.path.abspath(DATABASE)}")

if __name__ == '__main__':
    try:
        init_db()
    except Exception as e:
        print(f"Error initializing database: {e}", file=sys.stderr)
        sys.exit(1)
