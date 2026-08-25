#!/usr/bin/env python3
"""
convert-spelling-bee.py

Reads a Spelling Bee CSV with columns:
  Level,List,Study,Media,Answer,Prompt

Writes questions_spelling.json with the shape used by the app:
{
  "spelling-bee-1": {
    "name": "Spelling Bee List 1",
    "levels": {
      "J1": {
        "Practice 1": "one, two, three",
        "Practice 2": "black, orange",
        "Championship": "one, two, three, black, orange"
      },
      ...
    }
  },
  ...
}

Usage:
  python convert-spelling-bee.py "spelling-bee - 1.csv" --out questions_spelling.json
"""
import csv
import json
import argparse
from pathlib import Path

def menu_key_from_list(list_name):
    # Expects "List 1", "List 2", etc. -> "spelling-bee-1"
    if not list_name:
        return "spelling-bee-1"
    parts = list_name.strip().split()
    # find last numeric token
    for p in reversed(parts):
        if p.isdigit():
            return f"spelling-bee-{p}"
    # fallback: sanitize name
    sanitized = list_name.strip().lower().replace(' ', '-').replace('.', '')
    return f"spelling-bee-{sanitized}"

def unique_preserve_order(items):
    seen = set()
    out = []
    for it in items:
        if not it:
            continue
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out

def read_csv_build_structure(csv_path):
    data = {}
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # normalize keys and values
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k,v in row.items()}
            level = row.get('Level') or 'Unknown'
            list_name = row.get('List') or 'List 1'
            study = row.get('Study') or 'Practice 1'
            answer = (row.get('Answer') or '').strip()
            media = (row.get('Media') or '').strip()
            prompt = (row.get('Prompt') or '').strip()

            menu_key = menu_key_from_list(list_name)

            if menu_key not in data:
                # default name uses the list number if possible
                data[menu_key] = {'name': f'Spelling Bee {list_name}', 'levels': {}}
            if level not in data[menu_key]['levels']:
                data[menu_key]['levels'][level] = {}
            if study not in data[menu_key]['levels'][level]:
                data[menu_key]['levels'][level][study] = []

            # Append a dict (keeps media/prompt for later use), but primary app uses 'answer'
            data[menu_key]['levels'][level][study].append({
                'answer': answer,
                'media': media,
                'prompt': prompt
            })
    return data

def generate_championships_and_strings(data):
    # For each menu -> level -> create Championship (Practice 1 + Practice 2) and produce comma-joined strings
    out = {}
    for menu_key, menu in data.items():
        out[menu_key] = {'name': menu.get('name', menu_key), 'levels': {}}
        for level, studies in menu['levels'].items():
            out[menu_key]['levels'][level] = {}
            p1 = [item['answer'] for item in studies.get('Practice 1', [])]
            p2 = [item['answer'] for item in studies.get('Practice 2', [])]
            # Merge practice lists preserving order and removing duplicates
            championship = unique_preserve_order(p1 + p2)

            for study_name, entries in studies.items():
                answers = [e['answer'] for e in entries if e.get('answer')]
                uniq = unique_preserve_order(answers)
                out[menu_key]['levels'][level][study_name] = ', '.join(uniq)

            # Ensure Championship exists and is a deduped string
            if 'Championship' not in out[menu_key]['levels'][level] or not out[menu_key]['levels'][level]['Championship'].strip():
                out[menu_key]['levels'][level]['Championship'] = ', '.join(championship)
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv', type=Path, help='Input CSV file')
    parser.add_argument('--out', '-o', default='questions_spelling.json', help='Output JSON file')
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"Input CSV {args.csv} not found.")
        return

    raw = read_csv_build_structure(args.csv)
    produced = generate_championships_and_strings(raw)

    out_path = Path(args.out)
    out_path.write_text(json.dumps(produced, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Wrote {out_path} with {len(produced)} spelling menus.")

if __name__ == '__main__':
    main()
