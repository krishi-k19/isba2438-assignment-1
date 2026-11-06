# DEMO-SCRIPT.md — recording plan (~5–6 min)

Handout requirements for the recording: demonstrate a successful use and one
relevant edge case of the custom feature(s); explain inputs, logic, and output
in your own words; show the core commands still work. This script covers both
custom commands. Pause-and-type everything live; no pre-staged files.

Setup before recording: empty folder containing only `products.py`;
verify `py -3 products.py --help` shows `search` and `summary`.

---

## Beat 1 — Core commands still work (60–75s)  `[say] "The assignment core first"`
```
py -3 products.py add --name "Ballpoint Pen" --price 1.20 --quantity 40
py -3 products.py add --name "Pen Holder" --price 3.99 --quantity 12
py -3 products.py add --name "Notebook" --price 4.5 --quantity 25
py -3 products.py list
py -3 products.py get 3
py -3 products.py update 3 --quantity 22
py -3 products.py get 3
```
`[say]`: prices normalize to two decimals ("4.5" became "4.50"), IDs are
assigned automatically, update touches only the field you give it.

## Beat 2 — `search`, successful use (60s)  `[say] "Feature 1: search"`
```
py -3 products.py search --query pen
```
`[say]` (explain in your own words, e.g.): "A customer asks whether I have
ballpoint pens. Instead of scrolling the whole list, I type one word. Search
takes `--query`, lowercases both the query and every product name, and keeps
the products whose name contains the query as a substring — that's why
'Ballpoint Pen' and 'Pen Holder' both match. Output is a table sorted by ID,
and the PRICE column keeps two decimals."

## Beat 3 — `search`, edge case (45s)
```
py -3 products.py search --query stapler
py -3 products.py search --query
py -3 products.py search --query "   "
```
`[say]`: "First edge case: nothing matches, so I print a friendly message and
exit 0 — same spirit as `list` printing `[]`. Second edge case: a blank query
is invalid input, so I print an error to stderr and exit 2." (Optionally show
`echo %ERRORLEVEL%` / `echo $?` to prove the codes.)

## Beat 4 — `summary`, successful use (60s)  `[say] "Feature 2: summary"`
```
py -3 products.py summary
```
`[say]` (own words, e.g.): "Before I place a purchase order I want to know how
much money is sitting on my shelves. Summary adds up all three numbers: 3
distinct products, 74 total units, and the total shelf value. The value is
computed with Python's Decimal type — each product's price times its quantity,
summed exactly — so a price like 3.99 times 12 never suffers float rounding.
That's why the total shows clean two decimals."

## Beat 5 — `summary`, edge cases (45s)
```
py -3 products.py --file empty-store.json summary
py -3 products.py summary --extra
```
`[say]`: "With a file that doesn't exist, summary treats the store as empty —
zeros, exit 0, and note the file is still not created, because summary is
read-only. And I reject stray arguments with exit 2."

## Beat 6 — Read-only proof + core regression (30s)
```
py -3 products.py --file demo.json list
dir
```
`[say]`: "demo.json was never created by that read-only command. And one last
check that CRUD still works end-to-end:" then run one `add` (gets id 1), `get
1`, `delete 1 --yes`, `list` on `demo.json`.

## Beat 7 — Wrap (15s)
`[say]`: recap: two custom read-only features — `search` for finding products
fast, `summary` for knowing what your stock is worth — with the CRUD core
untouched, all stdlib, data in one JSON file.

---

## Failure-language checklist (do not trace back on camera)
- If asked what happens on a corrupted file: `py -3 products.py --file corrupt.json summary`
  → exit 1, concise stderr message, file left untouched (can pre-stage a bad
  file off-camera if time allows).
- Never say "it crashes" — say "it reports the error and exits nonzero while
  leaving the data file exactly as it was."
