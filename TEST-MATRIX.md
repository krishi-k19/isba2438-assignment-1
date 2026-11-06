# TEST-MATRIX.md — QA acceptance matrix for `products.py`

Every row must pass before submission. "File" = the selected data file.
Defaults apply: commands run in a scratch directory; expected exit code in the
**Xit** column (0/1/2 per PRD §10).

Legend for File column: **–** untouched/not created · **✎** created/modified ·
**↯** must remain byte-identical after the command.

## A. `add`

| # | Case | Action | Expected | Xit |
|---|---|---|---|---|
| A1 | First add creates store | fresh dir → `add --name "Notebook" --price 4.50 --quantity 10` | JSON object id=1, price `"4.50"`; file created with `next_id` 2 | 0 |
| A2 | Price normalization | `add ... --price 4.5` | stored/printed `"4.50"` | 0 |
| A3 | Zero price & zero qty | `add ... --price 0 --quantity 0` | `"0.00"`, qty `0` | 0 |
| A4 | Name trimming | `--name "  Pen  "` | stored/printed `"Pen"` | 0 |
| A5 | Unicode name | `--name "Café Mug"` | round-trips exactly (UTF-8) | 0 |
| A6 | Duplicate name | add two products named `"Pen"` | both saved, distinct ids | 0 |
| A7 | Price rejects | `--price 4.501` / `-4` / `$4` / `4.` / `1e3` / `.5` / `""` | stderr, no file change, ID not consumed | 2 |
| A8 | Qty rejects | `--quantity -1` / `1.5` / `abc` / `""` | stderr, file unchanged | 2 |
| A9 | Name rejects | `--name "   "` | stderr, file unchanged | 2 |
| A10 | Missing flag | omit each of `--name`/`--price`/`--quantity` in turn | stderr, file unchanged | 2 |
| A11 | Failed add keeps next_id | A7 then successful `add` | new product gets the same id the failed attempt would have had | 0 |

## B. `list` / `get`

| # | Case | Action | Expected | Xit |
|---|---|---|---|---|
| B1 | Empty/missing store | `list` with no data file | `[]`; file NOT created | 0 |
| B2 | Sort order | hand-write a valid store whose products array lists id 2 before id 1, then `list` | JSON array sorted by numeric id ascending | 0 |
| B3 | Get existing | `get 2` | JSON object for id 2 | 0 |
| B4 | Get missing | `get 999` | stderr mentions 999; nothing on stdout | 1 |
| B5 | Bad ID syntax | `get 0` / `-3` / `abc` / `1.5` | stderr | 2 |
| B6 | Get on missing file | `get 1` with no file | missing-product error; file NOT created | 1 |

## C. `update` / `delete`

| # | Case | Action | Expected | Xit |
|---|---|---|---|---|
| C1 | Update one field | `update 1 --quantity 5` | only qty changes; id/name/price intact; `next_id` unchanged | 0 |
| C2 | Update two fields | `update 1 --name "Pen" --price 2` | both applied, price `"2.00"` | 0 |
| C3 | No field flags | `update 1` | stderr; file unchanged | 2 |
| C4 | Invalid value wins over write | `update 1 --quantity -5` | stderr; file byte-identical (↯) | 2 |
| C5 | Update missing ID | `update 999 --quantity 5` | stderr mentions 999 | 1 |
| C6 | Delete happy path | `delete 1 --yes` | `{"deleted_id": 1}`; record gone; `next_id` unchanged | 0 |
| C7 | Delete without --yes | `delete 1` | stderr; record still present | 2 |
| C8 | Delete missing ID | `delete 999 --yes` | stderr mentions 999 | 1 |
| C9 | ID never reused | C6 then `add` | new id = old `next_id` value (not 1) | 0 |

## D. Custom: `search`

| # | Case | Action | Expected | Xit |
|---|---|---|---|---|
| D1 | Substring, case-insensitive | fresh scratch store via `--file` seeded with "Ballpoint Pen" 1.20×40, "Pen Holder" 3.99×12, "Notebook" 4.50×25 → `search --query pen` | table with the two Pen rows sorted by id; Notebook absent; header `ID  NAME  PRICE  QUANTITY` | 0 |
| D2 | No matches | in the D1 store → `search --query stapler` | `No products found for "stapler".` on stdout; file untouched | 0 |
| D3 | Blank query | `search --query "   "` | stderr `--query must not be blank`; file untouched | 2 |
| D4 | Missing query | `search` | stderr; usage hint | 2 |
| D5 | Trimming | in the D1 store → `search --query "  pen "` (trailing space) | same result set as D1 (query trimmed before matching) | 0 |
| D6 | Read-only on missing file | `search --query pen` with no data file | no-match message; file NOT created | 0 |
| D7 | With `--file` | `--file demo.json search --query pen` (flag before command) | reads demo.json only | 0 |
| D8 | Price formatting | in the D1 store → match the product with price `"1.20"` | table shows `1.20`, not `1.2` | 0 |
| D9 | `--help` | `search --help` | usage text; data file untouched | 0 |

## E. Custom: `summary`

| # | Case | Action | Expected | Xit |
|---|---|---|---|---|
| E1 | Populated store | fresh scratch store via `--file` seeded with 3 products: 40×1.20, 12×3.99, 22×4.50 → `summary` | `3`, `74`, `194.88` in one aligned row | 0 |
| E2 | Decimal exactness | fresh scratch store seeded with 3× `--price 0.10 --quantity 1` → `summary` | TOTAL VALUE `0.30` (float math would give `0.30000000000000004`-style noise) | 0 |
| E3 | Empty/missing store | `summary` with no data file | `0  0  0.00`; file NOT created | 0 |
| E4 | Stray argument | `summary extra` | stderr | 2 |
| E5 | Corrupt file | hand-written file with invalid JSON → `summary` | concise stderr; file byte-identical (↯) | 1 |
| E6 | Bad stored record | file where one product's price is `"abc"` (or qty `-3`, or string qty) | exit 1; file untouched (↯) | 1 |
| E7 | Schema violation | file with `next_id` not greater than max product id | exit 1; file untouched (↯) | 1 |
| E8 | `--help` | `summary --help` | usage text; file untouched | 0 |

## F. File behavior & global rules

| # | Case | Action | Expected | Xit |
|---|---|---|---|---|
| F1 | `--file` placement | `add --name X --file demo.json ...` (flag AFTER command) | rejected | 2 |
| F2 | Missing parent dir | `--file nodir/demo.json add ...` | write-failure message; `nodir` NOT created | 1 |
| F3 | Read-only commands never write | run `list`, `get`, `search`, `summary`, `--help`; snapshot file before/after | byte-identical every time (↯) | 0 |
| F4 | Save before success | `add` then re-`list` in a new invocation | new product visible (persistence across processes) | 0 |
| F5 | Empty existing file | 0-byte file → `add ...` | exit 1, file left 0 bytes (↯) | 1 |
| F6 | Malformed JSON | file with `{oops` → `list` / `add` | stderr; file unchanged (↯) | 1 |
| F7 | Help exits clean | `--help`, `add --help`, `search --help` with NO data file present | usage; exit 0; no file created | 0 |
| F8 | Unknown command | `products.py foo` | stderr; exit 2 | 2 |
| F9 | Unknown flag | `list --sort name` | stderr | 2 |
| F10 | Unexpected positional | `list 5` | stderr | 2 |
| F11 | No tracebacks | run every A–E failure row | none prints a Python traceback | 1/2 |
| F12 | Stdout purity | every failure row | stdout has no JSON result | 1/2 |
| F13 | Write failure safety | make file read-only → `update 1 --quantity 5` | exit 1; original content intact (↯) | 1 |
| F14 | Stdlib only | `grep` all imports in `products.py` | only Python 3 standard library | — |

## Verification workflow

1. Run sections A–F in order in a scratch directory (`A` builds the store used
   by later rows; B–E reuse it or fresh scratch dirs as noted).
2. Any failed row → fix → re-run the **entire** section (not just the row).
3. Before recording, re-run D1–D9 and E1–E8 — the demo depends on them.
