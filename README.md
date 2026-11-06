# products.py — a tiny inventory manager for small stores

Run it from the terminal, keep all your products in one JSON file. No setup, no
accounts, no packages to install — just Python.

Built by Krishi Konindala for ISBA 2438 (Assignment 1).

## Requirements

- Python 3 (any recent version — 3.8 or newer).
- Nothing else. The tool uses only the Python standard library, so there are
  no packages to install.

**Windows note:** you may need to type `py -3` instead of `python3` in every
example below.

## Quick start

Open a terminal in the folder containing `products.py` and try:

```
python3 products.py add --name "Notebook" --price 4.50 --quantity 10
python3 products.py list
python3 products.py get 1
python3 products.py update 1 --quantity 8
python3 products.py delete 1 --yes
```

That's the whole lifecycle: add a product, list what you have, look one up,
change it, remove it.

## Command reference

| Command | Syntax | What it does |
|---|---|---|
| `add` | `add --name NAME --price PRICE --quantity QTY` | Adds a product. All three flags are required. Prints the new product as JSON. |
| `list` | `list` | Prints every product as a JSON array, sorted by ID. |
| `get` | `get ID` | Prints one product as a JSON object. |
| `update` | `update ID [--name NAME] [--price PRICE] [--quantity QTY]` | Changes only the fields you pass. At least one field flag is required. |
| `delete` | `delete ID --yes` | Deletes a product. `--yes` confirms — there is no interactive prompt. |
| `search` | `search --query TEXT` | Finds products whose name contains TEXT (case-insensitive). |
| `summary` | `summary` | Prints how many products, how many units, and the total shelf value. |

**The data file:** by default everything is stored in `products.json` in the
current directory. Every command accepts `--file PATH` **before the command**
to use a different file, e.g. `python3 products.py --file backup.json list`.
Missing parent folders are never created for you — if you ask for
`--file nodir/store.json`, saving will fail with a clear error.

## Custom feature 1 — `search`

**Who it helps & why:** you, mid-customer-conversation. "Do you have more of
the ballpoint pens?" Scrolling through the whole `list` output while someone
waits is no fun. `search` takes the one word you remember and instantly shows
every product whose name contains it, case-insensitively — IDs included, ready
for a follow-up `update` or `delete`. It shines when your catalog is long and
you only remember part of a product's name.

**Syntax:**
```
python3 products.py [--file PATH] search --query TEXT
```

**Inputs:** `--query` is required. Matching is a case-insensitive substring of
the product name. Blank queries are rejected.

**Runnable example** (in a fresh directory, so IDs start at 1):
```
python3 products.py add --name "Ballpoint Pen" --price 1.20 --quantity 40
python3 products.py add --name "Pen Holder" --price 3.99 --quantity 12
python3 products.py search --query pen
```
Output:
```
ID  NAME           PRICE  QUANTITY
 1  Ballpoint Pen   1.20        40
 2  Pen Holder      3.99        12
```

Nothing matches? You get a friendly message and a normal exit:
`No products found for "stapler".`

## Custom feature 2 — `summary`

**Who it helps & why:** you, before placing a purchase order or doing the
books. Looking at single products is easy — the *total* is invisible. How much
of your money is sitting on the shelves right now? How many units do you
carry? One command answers both, so you can decide what to reorder and
roughly what an inventory write-off would cost.

**Syntax:**
```
python3 products.py [--file PATH] summary
```

**Inputs:** none (besides the global `--file`).

**Expected output:** one row — PRODUCTS (how many records), UNITS (total
quantity), TOTAL VALUE (the sum of every price × quantity, computed with exact
decimal math, always shown with 2 decimal places).
```
python3 products.py add --name "Ballpoint Pen" --price 1.20 --quantity 40
python3 products.py add --name "Pen Holder" --price 3.99 --quantity 12
python3 products.py summary
```
Output:
```
PRODUCTS  UNITS  TOTAL VALUE
       2     52        95.88
```

An empty (or missing) data file prints zeros and exits normally: `0`, `0`,
`0.00`.

## The data file

A store file is plain UTF-8 JSON. Example with one product:

```json
{
  "next_id": 2,
  "products": [
    {"id": 1, "name": "Notebook", "price": "4.50", "quantity": 10}
  ]
}
```

Notes on how IDs and values behave:

- `id` is assigned by the tool: it starts at 1, never changes, and is never
  reused after a delete — even if you delete the newest product.
- `name` is trimmed of surrounding whitespace; inside, it's kept exactly as
  you typed it. Duplicate names are allowed (two different brands of "Pen"
  are fine).
- `price` is stored as text with exactly two decimal places. `4.5` becomes
  `"4.50"`. Values like `4.501`, `$4`, or `1e3` are rejected.
- `quantity` is a whole number, zero or more.
- A missing data file is treated as an empty store. Read-only commands
  (`list`, `get`, `search`, `summary`, all `--help`) never create or modify
  it — only a successful `add`, `update`, or `delete` writes to disk.

## Errors & exit codes

Every failure prints a short explanation on stderr — never a Python
traceback — and **a failed command never changes your data file**.

| Exit code | Meaning | Example |
|---|---|---|
| 0 | Success, including empty results and `--help` | `search` with no matches |
| 1 | ID not found, invalid stored data, or file read/write failure | `get 999`; corrupt JSON; read-only file |
| 2 | Invalid syntax, missing arguments, or invalid values | `add` without `--name`; price `4.501`; blank query |

## Known limitations / future ideas

- Reorder alerts ("low stock") need a per-product threshold, because 40 pens
  is normal but 2 espresso machines is not. That would require a schema
  change, so it's parked for now.
- One JSON file means one store, one user at a time. There's no locking or
  networking — that's deliberate: it keeps the tool simple and your data
  portable.
