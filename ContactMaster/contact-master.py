#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ContactMaster - A simple, durable contact manager (CLI)
Features:
- Add, View (sorted), Search (partial), Edit, Delete
- JSON persistence with auto-create and safe save
- CSV export/import with de-duplication
- One-click JSON backup
Author: Hareesh Kumar
"""

import json
import os
import re
import sys
import csv
import shutil
from datetime import datetime
from uuid import uuid4

DATA_FILE = "contacts.json"
BACKUP_DIR = "backups"

# ----------------------------- Utilities ----------------------------- #

def safe_print(s: str = "", end: str = "\n"):
    try:
        print(s, end=end)
    except Exception:
        # In case of weird terminal encoding issues
        print(s.encode("utf-8", "ignore").decode("utf-8"), end=end)

def now_stamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def file_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def ensure_data_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def load_contacts():
    ensure_data_file()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # basic sanity: list of dicts
            return [c for c in data if isinstance(c, dict)]
    except json.JSONDecodeError:
        safe_print("   contacts.json corrupted. Creating a safe backup & resetting...")
        backup_path = f"{DATA_FILE}.corrupt.{file_timestamp()}.bak"
        shutil.copy2(DATA_FILE, backup_path)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return []
    except FileNotFoundError:
        ensure_data_file()
        return []

def atomic_save(contacts):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)

def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())

def validate_phone(phone: str) -> bool:
    # allow +country and digits, 7–15 digits total
    digits = re.sub(r"[^\d]", "", phone)
    return 7 <= len(digits) <= 15

def validate_email(email: str) -> bool:
    if not email.strip():
        return True  # optional
    # simple, pragmatic email regex
    return re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email.strip()) is not None

def make_id() -> str:
    return uuid4().hex[:8]

def sort_contacts(contacts):
    return sorted(contacts, key=lambda c: (c.get("name","").lower(), c.get("phone",""), c.get("email","").lower()))

def human_table(rows, headers):
    # Compute widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    # Build lines
    def line(char="-", junction="+"):
        return junction + junction.join(char * (w + 2) for w in widths) + junction
    def fmt_row(row):
        cells = [f" {str(cell).ljust(widths[i])} " for i, cell in enumerate(row)]
        return "|" + "|".join(cells) + "|"
    out = []
    out.append(line("-","+") )
    out.append(fmt_row(headers))
    out.append(line("=","+") )
    for r in rows:
        out.append(fmt_row(r))
        out.append(line("-","+"))
    return "\n".join(out)

def prompt(msg, required=False, default=None):
    while True:
        val = input(msg).strip()
        if val == "" and default is not None:
            return default
        if required and val == "":
            safe_print("     required field.")
            continue
        return val

# ----------------------------- Core Ops ----------------------------- #

def add_contact(contacts):
    safe_print("\n  Add Contact")
    name = normalize_whitespace(prompt("   Name* : ", required=True))
    phone = normalize_whitespace(prompt("   Phone*: ", required=True))
    email = normalize_whitespace(prompt("   Email : "))
    tags  = normalize_whitespace(prompt("   Tags (comma separated) : "))

    if not validate_phone(phone):
        safe_print("    Invalid phone. Use digits with optional +country, length 7–15.")
        return

    if not validate_email(email):
        safe_print("     Invalid email format.")
        return

    new = {
        "id": make_id(),
        "name": name,
        "phone": phone,
        "email": email,
        "tags": [t.strip() for t in tags.split(",")] if tags else [],
        "created_at": now_stamp(),
        "updated_at": now_stamp()
    }
    contacts.append(new)
    atomic_save(contacts)
    safe_print(f"     Saved. Contact ID: {new['id']}")

def list_contacts(contacts):
    safe_print("\n  All Contacts")
    if not contacts:
        safe_print("   (empty)")
        return
    rows = []
    for c in sort_contacts(contacts):
        rows.append([
            c.get("id",""),
            c.get("name",""),
            c.get("phone",""),
            c.get("email",""),
            ", ".join(c.get("tags",[]))
        ])
    safe_print(human_table(rows, headers=["ID","Name","Phone","Email","Tags"]))

def find_contacts(contacts, query):
    q = query.lower().strip()
    res = []
    for c in contacts:
        hay = " ".join([
            c.get("name",""),
            c.get("phone",""),
            c.get("email",""),
            " ".join(c.get("tags",[]))
        ]).lower()
        if q in hay:
            res.append(c)
    return res

def search_contacts(contacts):
    safe_print("\n  Search")
    q = prompt("   Search text: ", required=True)
    found = find_contacts(contacts, q)
    if not found:
        safe_print("   (no matches)")
        return
    rows = []
    for c in sort_contacts(found):
        rows.append([
            c.get("id",""),
            c.get("name",""),
            c.get("phone",""),
            c.get("email",""),
            ", ".join(c.get("tags",[]))
        ])
    safe_print(human_table(rows, headers=["ID","Name","Phone","Email","Tags"]))

def pick_by_id(contacts, purpose="select"):
    id_ = prompt(f"   Enter Contact ID to {purpose}: ", required=True)
    for c in contacts:
        if c.get("id") == id_:
            return c
    safe_print("    No contact found with that ID.")
    return None

def edit_contact(contacts):
    safe_print("\n  Edit Contact")
    c = pick_by_id(contacts, "edit")
    if not c: return
    safe_print("   (Leave blank to keep existing value)")
    name = prompt(f"   Name [{c.get('name','')}] : ", default=c.get("name",""))
    phone = prompt(f"   Phone [{c.get('phone','')}] : ", default=c.get("phone",""))
    email = prompt(f"   Email [{c.get('email','')}] : ", default=c.get("email",""))
    curr_tags = ", ".join(c.get("tags",[]))
    tags  = prompt(f"   Tags (comma) [{curr_tags}] : ", default=curr_tags)

    name = normalize_whitespace(name)
    phone = normalize_whitespace(phone)
    email = normalize_whitespace(email)
    tags_list = [t.strip() for t in tags.split(",")] if tags else []

    if not validate_phone(phone):
        safe_print("    Invalid phone.")
        return
    if not validate_email(email):
        safe_print("    Invalid email.")
        return

    c["name"] = name
    c["phone"] = phone
    c["email"] = email
    c["tags"] = tags_list
    c["updated_at"] = now_stamp()
    atomic_save(contacts)
    safe_print("     Updated.")

def delete_contact(contacts):
    safe_print("\n   Delete Contact")
    c = pick_by_id(contacts, "delete")
    if not c: return
    confirm = prompt(f"   Confirm delete {c.get('name')}? (y/N): ").lower()
    if confirm == "y":
        contacts.remove(c)
        atomic_save(contacts)
        safe_print("     Deleted.")
    else:
        safe_print("     Cancelled.")

# ----------------------------- CSV / Backup ----------------------------- #

def export_csv(contacts):
    if not contacts:
        safe_print("\n  Export CSV\n   (no contacts to export)")
        return
    fname_default = f"contacts_{file_timestamp()}.csv"
    fname = prompt(f"\n  Export CSV filename [{fname_default}]: ", default=fname_default)
    fields = ["id","name","phone","email","tags","created_at","updated_at"]
    with open(fname, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for c in contacts:
            row = dict(c)
            row["tags"] = ", ".join(c.get("tags",[]))
            writer.writerow(row)
    safe_print(f"     Exported to {fname}")

def import_csv(contacts):
    safe_print("\n  Import CSV")
    path = prompt("   CSV file path: ", required=True)
    if not os.path.exists(path):
        safe_print("    File not found.")
        return

    seen = {(c.get("name","").lower(), c.get("phone","")) for c in contacts}
    added = 0
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = normalize_whitespace(row.get("name",""))
            phone = normalize_whitespace(row.get("phone",""))
            email = normalize_whitespace(row.get("email",""))
            tags  = [t.strip() for t in (row.get("tags","") or "").split(",") if t.strip()]

            if not name or not phone:
                continue
            key = (name.lower(), phone)
            if key in seen:
                continue
            if not validate_phone(phone) or not validate_email(email):
                continue

            contacts.append({
                "id": make_id(),
                "name": name,
                "phone": phone,
                "email": email,
                "tags": tags,
                "created_at": now_stamp(),
                "updated_at": now_stamp()
            })
            seen.add(key)
            added += 1

    atomic_save(contacts)
    safe_print(f"   Imported {added} new contact(s).")

def make_backup():
    safe_print("\n Backup")
    ensure_data_file()
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dest = os.path.join(BACKUP_DIR, f"contacts_{file_timestamp()}.json")
    shutil.copy2(DATA_FILE, dest)
    safe_print(f"   Backup created: {dest}")

# ----------------------------- Main Menu ----------------------------- #

MENU = """
==================== ContactMaster ====================
1) Add Contact
2) View All Contacts
3) Search Contacts
4) Edit Contact
5) Delete Contact
6) Export to CSV
7) Import from CSV
8) Backup JSON
9) Quit
=======================================================
"""

def main():
    safe_print("ContactMaster CLI starting…")
    contacts = load_contacts()

    while True:
        safe_print(MENU)
        choice = prompt("Choose an option [1-9]: ", required=True)
        if choice == "1":
            add_contact(contacts)
        elif choice == "2":
            list_contacts(contacts)
        elif choice == "3":
            search_contacts(contacts)
        elif choice == "4":
            edit_contact(contacts)
        elif choice == "5":
            delete_contact(contacts)
        elif choice == "6":
            export_csv(contacts)
        elif choice == "7":
            import_csv(contacts)
        elif choice == "8":
            make_backup()
        elif choice == "9":
            safe_print(" Bye!")
            sys.exit(0)
        else:
            safe_print(" Invalid choice, try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        safe_print("\n  Interrupted. Goodbye!")
