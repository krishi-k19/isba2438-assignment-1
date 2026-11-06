# PRD — Storefront Inventory CLI (`products.py`)

Course: ISBA2438 · Version: 1.0 · Status: Approved for implementation
Related docs: [README-OUTLINE.md](README-OUTLINE.md) · [DEMO-SCRIPT.md](DEMO-SCRIPT.md) · [TEST-MATRIX.md](TEST-MATRIX.md)

---

## 1. Overview

A Python 3 command-line tool that manages product inventory for a small store,
backed by a single local JSON file. It ships the five required CRUD commands
(`add`, `list`, `get`, `update`, `delete`) plus **two custom read-only commands**
that solve real inventory problems for a store owner:

| Command | Inventory problem it solves |
|---|---|
| `search --query TEXT` | "A customer is asking: do you have more of X?" — find items instantly without scrolling the full `list` output. |
| `summary` | "How much money do I have on my shelves?" — one glance at product count, total units, and total shelf value for reorder/budget decisions. |

Both custom commands are **read-only**: they never create, modify, or delete the
data file, and they add no new fields to product records. This was a deliberate
choice — see §11 (Out of Scope) for the rejected alternative (`lowstock`).

## 2. Users

**Primary persona — "Pat", owner/operator of a small store.** Not a programmer.
Uses the terminal a few times a day: after a delivery, after a sale, before a
reorder, and whenever a customer asks whether an item is in stock. Pat needs
commands that are fast, honest about errors, and never destroy data.

## 3. Goals

1. Faithfully implement the handout contract (commands, file format, validation,
   exit codes) with zero deviations.
2. Give Pat two high-value, zero-risk (read-only) workflows: finding products
   and valuing stock.
3. Make every failure explicit: correct exit code, concise stderr message, and
   a data file that is never left altered by a failed command.
4. Keep the tool dependency-free (Python 3 standard library only) and
   non-interactive (one operation per invocation).

### Non-goals

- Interactive menus or prompts of any kind.
- Multi-user access, locking, or network storage.
- Categories, tags, per-product reorder thresholds, or any schema extension.
- Human-friendly colors, progress bars, or paging.

## 4. Product record

Stored as UTF-8 JSON in a data file (default `products.json` in the current
working directory). A store file has exactly this shape:

```json
{
  "next_id": 2,
  "products": [
    {"id": 1, "name": "Notebook", "price": "4.50", "quantity": 10}
  ]
}
```

Field rules (enforced on **input** and on **read** — see §8):

| Field | Rule |
|---|---|
| `id` | Positive integer, assigned by the tool. Starts at 1, never changes during updates, never reused after delete. |
| `name` | At least one non-whitespace character. Leading/trailing whitespace is trimmed on input; the rest is preserved verbatim. Duplicates allowed. |
| `price` | Nonnegative decimal: digits, optionally a decimal point and 1–2 digits (`0`, `4.5`, `4.50` OK; `+4`, `$4`, `4.`, `4.501`, `1e3` rejected). Always stored **and printed** as a string with exactly two decimal places (`"4.50"`). Input `4.5` is normalized to `"4.50"`. |
| `quantity` | Nonnegative integer. `0` allowed; negative, fractional, or blank rejected. |

`next_id` is greater than every existing product `id`, increments only on
successful `add`, and is never affected by `update` or `delete`.

## 5. CLI reference

```
python3 products.py [--file PATH] COMMAND [OPTIONS]
```

`--file PATH` must appear **before** the command. It selects the data file;
default is `products.json` in the current working directory. Relative paths
resolve from that directory. Missing parent directories are **not** created.
On Windows, `py -3` may replace `python3`.

| Command | Syntax | Behavior | Exit |
|---|---|---|---|
| `add` | `add --name NAME --price PRICE --quantity QTY` | All three flags required. Validate, assign `next_id`, increment `next_id`, save, print the new product as a JSON object. | 0 / 1 / 2 |
| `list` | `list` | Print a JSON array of all products sorted by `id` ascending. `[]` when empty. | 0 / 1 |
| `get` | `get ID` | Print the matching product as a JSON object. | 0 / 1 / 2 |
| `update` | `update ID [--name NAME] [--price PRICE] [--quantity QTY]` | At least one field flag required. Validate supplied values **before** saving; change only those fields; ID and other fields untouched; print updated product as JSON. | 0 / 1 / 2 |
| `delete` | `delete ID --yes` | `--yes` required (no prompt). Print `{"deleted_id": ID}`. | 0 / 1 / 2 |
| `search` *(custom)* | `search --query TEXT` | See §6. | 0 / 1 / 2 |
| `summary` *(custom)* | `summary` | See §7. | 0 / 1 / 2 |
| `--help` | top-level and per-command (e.g. `update --help`) | Print usage; exit 0; **never reads or writes the data file**. | 0 |

### Argument rules (all commands)

- IDs must be positive integers (`1`, `10`; reject `0`, `-1`, `1.5`, `abc`, `""`) → exit 2.
- Unknown command, unknown flag, unexpected positional argument, missing
  required flag, or invalid field value → exit 2.
- `argparse` is configured so expected input/file errors never print a Python
  traceback (tracebacks are a defect, not an error style).
- Every command supports `--help`, which exits 0 without touching the data file.

## 6. Custom command 1 — `search`

**Syntax:** `python3 products.py [--file PATH] search --query TEXT`

**Who it helps and why:** Pat, mid-customer-interaction. "Do you have more of
the ballpoint pens?" Today Pat would dump the whole `list` and eyeball it. With
`search`, Pat types the one word they remember and gets exactly the matching
rows, IDs included, ready for a follow-up `update` or `delete`.

**Behavior**

1. `--query` is required. After trimming leading/trailing whitespace it must
   contain at least one non-whitespace character; otherwise exit 2 with
   `error: --query must not be blank` on stderr.
2. Matching is **case-insensitive substring** against each product's `name`
   (`--query pen` matches "Ballpoint Pen" and "Pen Holder"). Trimmed query is
   used for matching, since stored names never have leading/trailing spaces.
3. Matching products print as a table sorted by numeric `id` ascending:

```
ID  NAME           PRICE  QUANTITY
 1  Ballpoint Pen   1.20        40
 2  Pen Holder      3.99        12
```

   Column alignment: `ID`, `PRICE`, `QUANTITY` right-aligned; `NAME`
   left-aligned; the `NAME` column width equals the longest matching name.
   `PRICE` always shows two decimal places. The example above is an exact
   render.
4. No matches (or a missing data file, which is an empty store): print
   `No products found for "pen".` to stdout, exit 0. The data file is **not**
   created or modified.
5. Malformed or schema-inconsistent data file: exit 1 with a concise stderr
   message; file untouched.

**Edge cases demonstrated in recording** (see DEMO-SCRIPT.md): no matches →
friendly message, exit 0; blank `--query` → exit 2.

## 7. Custom command 2 — `summary`

**Syntax:** `python3 products.py [--file PATH] summary`

**Who it helps and why:** Pat, before reordering or at tax time. "How much of
my money is sitting on the shelves?" and "How many units total?" Individual
products are easy to see; the total requires adding up every row by hand. One
command answers it.

**Behavior**

1. No flags beyond the global `--file`. Any extra argument → exit 2.
2. Computes three figures over the whole store:
   - `PRODUCTS` — number of product records.
   - `UNITS` — sum of `quantity` across all products.
   - `TOTAL VALUE` — Σ `price × quantity`, computed with `decimal.Decimal`
     (never binary floats) so `"4.10" × 3` is exactly `12.30`. Printed with
     exactly two decimal places.
3. Output: one aligned table, numeric columns right-aligned (for a store with
   3 products — 40×1.20, 12×3.99, 22×4.50):

```
PRODUCTS  UNITS  TOTAL VALUE
       3     74       194.88
```

4. Empty store or missing data file: same table with `0`, `0`, `0.00`,
   exit 0. The data file is **not** created or modified.
5. Malformed or schema-inconsistent data file (e.g. a price that isn't a valid
   two-decimal string, a negative quantity, `next_id` ≤ some product `id`):
   exit 1 with a concise stderr message; file untouched.

## 8. Validation & data integrity

Validation runs in this order, all before any write:

1. **Syntax layer** (argparse): command known, flags known, required flags
   present, correct arity → else exit 2.
2. **Value layer**: ID positive integer; price matches
   `^[0-9]+(\.[0-9]{1,2})?$`; quantity matches `^[0-9]+$` → else exit 2.
3. **Read layer**: if the file exists it must be valid UTF-8 JSON matching the
   store schema — `next_id` a positive integer greater than every product `id`;
   each record a valid product (field rules in §4); `id`s unique → else exit 1.
   A missing file is an empty store (valid).
4. **Existence layer** (`get`/`update`/`delete`): ID must exist → else exit 1.
5. **Write layer**: only after 1–4 pass, save the file, then report success.

Integrity guarantees:

- A failed command **never** alters the data file and never consumes an ID.
- Writes use a temp file + atomic replace so a mid-write crash cannot leave a
  half-written store.
- Read-only commands (`list`, `get`, `search`, `summary`, all `--help`) never
  create or rewrite the data file.

## 9. Implementation conventions (type hints)

Type hints are **annotations, not runtime enforcement** — CPython ignores them
at runtime, and no checker is required to run the tool. We use them for
documentation and static bug-catching:

1. Annotate every function signature. Example boundary:
   `def validate_price(raw: str) -> str:` (returns the normalized `"4.50"` form).
2. Model the product record with a `TypedDict` (or frozen dataclass); alias
   `Price = str` where clarity helps. Hints capture intent; they do **not**
   replace the §8 validation layer — argparse delivers raw strings and regex
   validation remains the only gatekeeper.
3. Put `from __future__ import annotations` at the top of `products.py` so
   modern hint syntax (`dict[str, object]`, `str | None`) works on any
   Python 3 version, not just 3.10+.
4. CLI parsing uses `argparse` (stdlib). Handler boundaries are `str`-in;
   richer types live inside the store layer.
5. Standard library only — `typing` and `argparse` are stdlib, so these
   conventions never introduce a dependency (§3, Goal 4).
6. Runtime behavior is identical with or without hints: exit codes, output,
   and file format are unaffected. A `mypy --strict` / `pyright` pass is
   recommended before submission but is not a handout requirement.

## 10. Output & exit codes

- Successful data commands print only their result to stdout (JSON for required
  commands; the specified table for `search`/`summary`). No extra chatter.
- Failures print a concise explanation to **stderr**, including the relevant ID
  when a product is missing, and print **nothing** to stdout. No tracebacks.

| Exit code | Meaning | Examples |
|---|---|---|
| 0 | Success, including empty results and help | `list` on empty store; `search` with no matches; `--help` |
| 1 | ID not found, invalid stored data, or file read/write failure | `get 999`; corrupted JSON; unwritable directory |
| 2 | Invalid syntax, missing arguments, or invalid input values | `add` without `--name`; `update 3` with no field flags; `delete 3` without `--yes`; blank `--query` |

## 11. Out of scope (parked, with rationale)

- **`lowstock` reorder report** — rejected during brainstorming: useful reorder
  thresholds differ per product (40 pens is normal, 2 espresso machines is not),
  so a meaningful version needs a per-product threshold field. That violates
  the handout's "use the existing JSON product records" constraint, so the
  feature is parked rather than shipped as a watered-down global threshold.
- If a future revision allows schema extension: per-product `reorder_point`
  plus a `lowstock` command and a low-stock line inside `summary`.

## 12. Acceptance criteria

1. All five required commands behave exactly as §5; all handout exit codes (§10)
   are honored; every TEST-MATRIX.md case passes.
2. `search` and `summary` appear in top-level `--help`, each support `--help`
   and `--file`, and match §6/§7 exactly.
3. No invocation ever produces a Python traceback for an expected error.
4. `list`, `get`, `search`, `summary`, and `--help` never create or modify the
   data file (verified by absence/mtime checks in the test matrix).
5. Only the Python 3 standard library is imported.
6. Failed commands leave the file byte-identical and never consume an ID.

## 13. Deliverables

| Artifact | Purpose |
|---|---|
| `products.py` | The tool (single file, stdlib only). |
| `README.md` | User-facing doc, per README-OUTLINE.md. |
| `PRD.md`, `TEST-MATRIX.md` | Design and QA documentation. |
| Recording | Walkthrough per DEMO-SCRIPT.md. |
