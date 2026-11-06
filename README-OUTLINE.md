# README-OUTLINE.md — plan for the final `README.md`

The handout requires the README to explain who each custom feature helps and
why, document its syntax/inputs/expected output, and include a runnable
example. This outline guarantees every required element lands. Write the real
README in warm, plain language for store owners (not graders).

## 1. Title & one-liner
- `products.py` — a tiny inventory manager for small stores, run from the
  terminal, data in a single JSON file.

## 2. Requirements & install
- Python 3 (any recent version; no packages to install).
- Windows note: `py -3` may replace `python3` in every example.

## 3. Quick start (runnable)
```
py -3 products.py add --name "Notebook" --price 4.50 --quantity 10
py -3 products.py list
py -3 products.py get 1
py -3 products.py update 1 --quantity 8
py -3 products.py delete 1 --yes
```

## 4. Command reference table
One row per command with syntax (reuse PRD §5 table), plus the `--file PATH`
rule (must come **before** the command; default `products.json`).

## 5. Custom feature 1 — `search`
- **Who it helps & why:** Pat, the store owner, mid-customer-conversation:
  "Do you have more of the ballpoint pens?" Instead of scrolling the whole
  `list`, one word finds every product whose name contains it,
  case-insensitively. Helps most when the catalog is long and you only
  remember part of the name.
- **Syntax:** `py -3 products.py [--file PATH] search --query TEXT`
- **Inputs:** `--query` (required). Case-insensitive substring of the product
  name. Blank queries are rejected.
- **Expected output:** aligned table of matches sorted by ID; friendly message
  when nothing matches.
- **Runnable example** (in a fresh directory, so IDs start at 1):
  ```
  py -3 products.py add --name "Ballpoint Pen" --price 1.20 --quantity 40
  py -3 products.py add --name "Pen Holder" --price 3.99 --quantity 12
  py -3 products.py search --query pen
  ```
  Expected:
  ```
  ID  NAME           PRICE  QUANTITY
   1  Ballpoint Pen   1.20        40
   2  Pen Holder      3.99        12
  ```
  And the empty case: `py -3 products.py search --query stapler` →
  `No products found for "stapler".`

## 6. Custom feature 2 — `summary`
- **Who it helps & why:** Pat, before reordering or doing the books. The total
  value of stock-on-hand and the unit count are invisible when looking at
  single products; `summary` answers "how much money is on my shelves?" in one
  line. Useful before placing purchase orders and at inventory/tax time.
- **Syntax:** `py -3 products.py [--file PATH] summary`
- **Inputs:** none (besides the global `--file`).
- **Expected output:** one table row with PRODUCTS (record count), UNITS
  (sum of quantity), TOTAL VALUE (Σ price × quantity, exact decimal math,
  always 2 decimal places).
- **Runnable example:**
  ```
  py -3 products.py add --name "Ballpoint Pen" --price 1.20 --quantity 40
  py -3 products.py add --name "Pen Holder" --price 3.99 --quantity 12
  py -3 products.py summary
  ```
  Expected:
  ```
  PRODUCTS  UNITS  TOTAL VALUE
         2     52        95.88
  ```
- Mention: empty store prints `0  0  0.00` and exits 0.

## 7. Data file
- Default `products.json`; `--file PATH` to use another; missing file = empty
  store; first `add` creates it; read-only commands never create it.
- Show the one-product example JSON from the handout.

## 8. Errors & exit codes
- The 0/1/2 table (reuse PRD §10). One sentence: "A failed command never
  changes your data file."

## 9. Known limitations / future ideas
- Parked per-product low-stock thresholds (needs a schema change).
- Single JSON file = single-store, single-user tool.
