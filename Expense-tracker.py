#!/usr/bin/env python3
"""
Expense Tracker
===============
Record expenses by category, save them to expenses.csv so they survive
restarts, and see totals per category.

Features
--------
1. Add an expense (date, category, amount, description)
2. View all expenses
3. Filter by category and/or date range
4. Category summary (count, total, average, largest, share of spending)

The CSV file lives next to this script and looks like this:

    date,category,amount,description
    2026-10-03,Food,120.00,Canteen lunch

Rules
-----
* Dates must be real dates in YYYY-MM-DD format and not in the future.
* Amounts must be positive numbers with at most 2 decimals (no commas or
  currency symbols). They are stored as text in the file but converted to
  Decimal numbers for all calculations.
* Every value is validated at the moment it is read (typed in OR loaded
  from the CSV), so one bad row can never crash the program.

Run with:  python expense_tracker.py
"""

import csv
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

# ----------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------
CSV_PATH = Path(__file__).with_name("expenses.csv")
FIELDNAMES = ["date", "category", "amount", "description"]
DATE_FORMAT = "%Y-%m-%d"
MAX_AMOUNT = Decimal("10000000")
MIN_YEAR = 2000
MAX_CATEGORY_LEN = 30
MAX_DESCRIPTION_LEN = 100
AMOUNT_PATTERN = re.compile(r"\d+(\.\d{1,2})?")


# ----------------------------------------------------------------------
# Validation: each function returns a clean value or raises ValueError
# ----------------------------------------------------------------------
def parse_date(text, allow_future=False):
    """Turn 'YYYY-MM-DD' text into a date object."""
    try:
        parsed = datetime.strptime(text.strip(), DATE_FORMAT).date()
    except ValueError:
        raise ValueError("use a real date in YYYY-MM-DD format, e.g. 2026-10-31")
    if parsed.year < MIN_YEAR:
        raise ValueError(f"year must be {MIN_YEAR} or later")
    if parsed > date.today() and not allow_future:
        raise ValueError("date cannot be in the future")
    return parsed


def parse_amount(text):
    """Turn text like '99.50' into a positive Decimal with 2 decimals."""
    cleaned = text.strip()
    if not AMOUNT_PATTERN.fullmatch(cleaned):
        raise ValueError(
            "enter a positive number with at most 2 decimals, e.g. 250 or 99.50 "
            "(no commas or currency symbols)"
        )
    amount = Decimal(cleaned)
    if amount <= 0:
        raise ValueError("amount must be greater than 0")
    if amount > MAX_AMOUNT:
        raise ValueError(f"amount cannot be more than {MAX_AMOUNT}")
    return amount.quantize(Decimal("0.01"))


def parse_category(text):
    """Tidy a category name: trim, collapse spaces, Title Case."""
    category = " ".join(text.split()).title()
    if not category:
        raise ValueError("category cannot be empty")
    if len(category) > MAX_CATEGORY_LEN:
        raise ValueError(f"category must be {MAX_CATEGORY_LEN} characters or fewer")
    return category


def parse_description(text):
    description = " ".join(text.split())
    if len(description) > MAX_DESCRIPTION_LEN:
        raise ValueError(f"description must be {MAX_DESCRIPTION_LEN} characters or fewer")
    return description


def ask(prompt, parser, allow_blank=False, blank_value=None):
    """Keep asking until the parser accepts the answer."""
    while True:
        raw = input(prompt).strip()
        if not raw and allow_blank:
            return blank_value
        try:
            return parser(raw)
        except ValueError as err:
            print(f"  Invalid: {err}")


# ----------------------------------------------------------------------
# CSV reading and writing (always newline='' with the csv module)
# ----------------------------------------------------------------------
def load_expenses():
    """
    Read expenses.csv and validate every row as it is read.
    Returns (expenses, problems). Bad rows are skipped and listed in
    'problems'. Raises ValueError if the header itself is unusable.
    """
    expenses, problems = [], []
    if not CSV_PATH.exists():
        return expenses, problems

    try:
        # utf-8-sig also copes with files re-saved by Excel
        with open(CSV_PATH, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:  # completely empty file
                return expenses, problems

            missing = [name for name in FIELDNAMES[:3] if name not in reader.fieldnames]
            if missing:
                raise ValueError(
                    f"expenses.csv is missing column(s): {', '.join(missing)}. "
                    f"Expected header: {','.join(FIELDNAMES)}"
                )

            for row_number, row in enumerate(reader, start=2):  # row 1 = header
                try:
                    expenses.append({
                        "date": parse_date(row.get("date") or ""),
                        "category": parse_category(row.get("category") or ""),
                        "amount": parse_amount(row.get("amount") or ""),
                        "description": parse_description(row.get("description") or ""),
                    })
                except ValueError as err:
                    problems.append(f"Row {row_number} skipped: {err}")
    except (OSError, UnicodeDecodeError, csv.Error) as err:
        problems.append(f"Could not finish reading expenses.csv ({err})")

    return expenses, problems


def file_ends_with_newline():
    with open(CSV_PATH, "rb") as f:
        f.seek(-1, 2)
        return f.read(1) in (b"\n", b"\r")


def append_expense(expense):
    """Add one row to the end of the CSV (writes the header if needed)."""
    needs_header = not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0
    needs_newline = not needs_header and not file_ends_with_newline()

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        if needs_newline:
            f.write("\r\n")
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if needs_header:
            writer.writeheader()
        writer.writerow({
            "date": expense["date"].isoformat(),
            "category": expense["category"],
            "amount": f"{expense['amount']:.2f}",  # text in the file
            "description": expense["description"],
        })


# ----------------------------------------------------------------------
# Features
# ----------------------------------------------------------------------
def add_expense(expenses):
    print("\n--- Add an expense ---")
    when = ask("Date [YYYY-MM-DD, blank = today]: ", parse_date,
               allow_blank=True, blank_value=date.today())

    known = sorted({e["category"] for e in expenses})
    if known:
        print(f"  Existing categories: {', '.join(known)}")
    category = ask("Category: ", parse_category)
    amount = ask("Amount: ", parse_amount)
    description = ask("Description (optional): ", parse_description,
                      allow_blank=True, blank_value="")

    expense = {"date": when, "category": category,
               "amount": amount, "description": description}
    try:
        append_expense(expense)
    except OSError as err:
        print(f"  Could not save to {CSV_PATH.name}: {err}")
        return
    expenses.append(expense)
    print(f"  Saved: {when.isoformat()} | {category} | {amount:,.2f}")


def print_table(rows):
    if not rows:
        print("  No expenses to show.")
        return

    rows = sorted(rows, key=lambda e: (e["date"], e["category"]))
    cat_w = max(len("Category"), max(len(e["category"]) for e in rows))

    print(f"\n  {'Date':<10}  {'Category':<{cat_w}}  {'Amount':>12}  Description")
    print("  " + "-" * (10 + cat_w + 12 + 20))
    for e in rows:
        print(f"  {e['date'].isoformat():<10}  {e['category']:<{cat_w}}  "
              f"{e['amount']:>12,.2f}  {e['description']}")

    total = sum((e["amount"] for e in rows), Decimal("0"))
    print("  " + "-" * (10 + cat_w + 12 + 20))
    print(f"  {len(rows)} expense(s), total: {total:,.2f}")


def view_all(expenses):
    print("\n--- All expenses ---")
    print_table(expenses)


def filter_expenses(expenses):
    print("\n--- Filter expenses (leave a question blank to skip it) ---")
    known = sorted({e["category"] for e in expenses})
    if known:
        print(f"  Categories: {', '.join(known)}")

    category = ask("Category: ", parse_category, allow_blank=True)
    allow_future = lambda text: parse_date(text, allow_future=True)
    start = ask("From date [YYYY-MM-DD]: ", allow_future, allow_blank=True)
    end = ask("To date   [YYYY-MM-DD]: ", allow_future, allow_blank=True)

    if start and end and start > end:
        print("  'From' date is after the 'To' date, so nothing can match.")
        return

    matches = [
        e for e in expenses
        if (category is None or e["category"].lower() == category.lower())
        and (start is None or e["date"] >= start)
        and (end is None or e["date"] <= end)
    ]
    print_table(matches)


def category_summary(expenses):
    print("\n--- Category summary ---")
    if not expenses:
        print("  No expenses yet.")
        return

    # Group with a dictionary: {category: {count, total, largest}}
    stats = {}
    for e in expenses:
        s = stats.setdefault(e["category"],
                             {"count": 0, "total": Decimal("0"), "largest": Decimal("0")})
        s["count"] += 1
        s["total"] += e["amount"]
        s["largest"] = max(s["largest"], e["amount"])

    grand_total = sum((s["total"] for s in stats.values()), Decimal("0"))
    ranked = sorted(stats.items(), key=lambda item: (-item[1]["total"], item[0]))
    cat_w = max(len("Category"), max(len(name) for name in stats))

    print(f"\n  {'Category':<{cat_w}}  {'Count':>5}  {'Total':>12}  "
          f"{'Average':>10}  {'Largest':>10}  {'Share':>6}")
    print("  " + "-" * (cat_w + 5 + 12 + 10 + 10 + 6 + 10))
    for name, s in ranked:
        average = s["total"] / s["count"]
        share = s["total"] / grand_total * 100
        print(f"  {name:<{cat_w}}  {s['count']:>5}  {s['total']:>12,.2f}  "
              f"{average:>10,.2f}  {s['largest']:>10,.2f}  {share:>5.1f}%")
    print("  " + "-" * (cat_w + 5 + 12 + 10 + 10 + 6 + 10))
    print(f"  {'ALL':<{cat_w}}  {len(expenses):>5}  {grand_total:>12,.2f}")
    print(f"\n  Biggest spending category: {ranked[0][0]}")


# ----------------------------------------------------------------------
# Menu
# ----------------------------------------------------------------------
def main():
    print("=" * 40)
    print("          EXPENSE TRACKER")
    print("=" * 40)

    try:
        expenses, problems = load_expenses()
    except ValueError as err:
        print(f"\nCannot start: {err}")
        return

    print(f"Loaded {len(expenses)} expense(s) from {CSV_PATH.name}.")
    if problems:
        print(f"Warning: {len(problems)} problem(s) found while reading:")
        for line in problems[:5]:
            print(f"  - {line}")
        if len(problems) > 5:
            print(f"  ... and {len(problems) - 5} more")

    actions = {
        "1": add_expense,
        "2": view_all,
        "3": filter_expenses,
        "4": category_summary,
    }

    while True:
        print("\n1) Add expense")
        print("2) View all expenses")
        print("3) Filter expenses")
        print("4) Category summary")
        print("5) Quit")
        choice = input("Choose 1-5: ").strip()

        if choice in actions:
            actions[choice](expenses)
        elif choice == "5":
            print("Goodbye! Your expenses are saved in", CSV_PATH.name)
            break
        else:
            print("  Please type a number from 1 to 5.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")