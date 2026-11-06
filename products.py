from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from decimal import Decimal, localcontext
from typing import TypedDict, cast

DEFAULT_FILE = "products.json"
ID_RE = re.compile(r"^[1-9][0-9]*$")
PRICE_INPUT_RE = re.compile(r"^[0-9]+(\.[0-9]{1,2})?$")
PRICE_STORED_RE = re.compile(r"^[0-9]+\.[0-9]{2}$")
QUANTITY_RE = re.compile(r"^[0-9]+$")
STORE_KEYS = {"next_id", "products"}
PRODUCT_KEYS = {"id", "name", "price", "quantity"}


class CliError(Exception):
    pass


class StoreError(Exception):
    pass


class Product(TypedDict):
    id: int
    name: str
    price: str
    quantity: int


class Store(TypedDict):
    next_id: int
    products: list[Product]


def validate_id(raw: str) -> int:
    if ID_RE.fullmatch(raw) is None:
        raise CliError(f"ID must be a positive integer, got {raw!r}")
    return int(raw)


def validate_name(raw: str) -> str:
    name = raw.strip()
    if not name:
        raise CliError("--name must not be blank")
    return name


def normalize_price(raw: str) -> str:
    if "." not in raw:
        return f"{int(raw)}.00"
    whole, fraction = raw.split(".", 1)
    return f"{int(whole)}.{fraction.ljust(2, '0')}"


def validate_price(raw: str) -> str:
    if PRICE_INPUT_RE.fullmatch(raw) is None:
        raise CliError(f"price must be a nonnegative number with at most two decimal places, got {raw!r}")
    return normalize_price(raw)


def validate_quantity(raw: str) -> int:
    if QUANTITY_RE.fullmatch(raw) is None:
        raise CliError(f"quantity must be a nonnegative whole number, got {raw!r}")
    return int(raw)


def check_store_schema(data: object, path: str) -> None:
    def fail(detail: str) -> None:
        raise StoreError(f"invalid store data in {path}: {detail}")

    if not isinstance(data, dict):
        fail("top level must be a JSON object")
        return
    store = cast("dict[str, object]", data)
    keys = set(store.keys())
    missing = STORE_KEYS - keys
    unexpected = keys - STORE_KEYS
    if missing:
        fail(f"missing key(s): {', '.join(sorted(missing))}")
    if unexpected:
        fail(f"unexpected key(s): {', '.join(sorted(unexpected))}")
    next_id = store["next_id"]
    products = store["products"]
    if isinstance(next_id, bool) or not isinstance(next_id, int) or next_id < 1:
        fail(f"next_id must be a positive integer, got {next_id!r}")
    if not isinstance(products, list):
        fail("products must be a JSON array")
        return
    seen_ids: set[int] = set()
    for record in products:
        if not isinstance(record, dict):
            fail("each product must be a JSON object")
            return
        product = cast("dict[str, object]", record)
        record_keys = set(product.keys())
        record_missing = PRODUCT_KEYS - record_keys
        record_unexpected = record_keys - PRODUCT_KEYS
        if record_missing:
            fail(f"product missing key(s): {', '.join(sorted(record_missing))}")
        if record_unexpected:
            fail(f"product has unexpected key(s): {', '.join(sorted(record_unexpected))}")
        product_id = product["id"]
        name = product["name"]
        price = product["price"]
        quantity = product["quantity"]
        if isinstance(product_id, bool) or not isinstance(product_id, int) or product_id < 1:
            fail(f"product id must be a positive integer, got {product_id!r}")
        if product_id in seen_ids:
            fail(f"duplicate product id {product_id}")
        seen_ids.add(product_id)
        if product_id >= next_id:
            fail(f"next_id {next_id} must be greater than product id {product_id}")
        if not isinstance(name, str) or not name.strip():
            fail(f"product {product_id}: name must contain at least one non-whitespace character")
        if not isinstance(price, str) or PRICE_STORED_RE.fullmatch(price) is None:
            fail(f"product {product_id}: price must be a string with exactly two decimal places, got {price!r}")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
            fail(f"product {product_id}: quantity must be a nonnegative integer, got {quantity!r}")


def load_store(path: str) -> Store:
    if not os.path.exists(path):
        return {"next_id": 1, "products": []}
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError:
        raise StoreError(f"cannot read data file: {path}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise StoreError(f"data file is not valid UTF-8: {path}")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise StoreError(f"data file is not valid JSON: {path}")
    check_store_schema(data, path)
    return cast(Store, data)


def save_store(path: str, store: Store) -> None:
    payload = json.dumps(store, indent=2, ensure_ascii=False) + "\n"
    directory = os.path.dirname(path) or "."
    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=directory,
            prefix=".products-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = handle.name
            handle.write(payload)
        os.replace(temp_path, path)
        temp_path = None
    except OSError:
        raise StoreError(f"cannot write data file: {path}")
    finally:
        if temp_path is not None:
            try:
                os.remove(temp_path)
            except OSError:
                pass


def find_product(store: Store, product_id: int) -> Product:
    for product in store["products"]:
        if product["id"] == product_id:
            return product
    raise StoreError(f"product {product_id} not found")


def print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def render_search_table(products: list[Product]) -> str:
    id_width = max([len("ID")] + [len(str(product["id"])) for product in products])
    name_width = max([len("NAME")] + [len(product["name"]) for product in products])
    price_width = max([len("PRICE")] + [len(product["price"]) for product in products])
    quantity_width = max([len("QUANTITY")] + [len(str(product["quantity"])) for product in products])

    def row(cells: list[str]) -> str:
        return "  ".join(
            [
                cells[0].rjust(id_width),
                cells[1].ljust(name_width),
                cells[2].rjust(price_width),
                cells[3].rjust(quantity_width),
            ]
        )

    lines = [row(["ID", "NAME", "PRICE", "QUANTITY"])]
    lines.extend(
        row(
            [
                str(product["id"]),
                product["name"],
                product["price"],
                str(product["quantity"]),
            ]
        )
        for product in products
    )
    return "\n".join(lines)


def render_summary(product_count: int, unit_count: int, total_value: str) -> str:
    product_width = max(len("PRODUCTS"), len(str(product_count)))
    unit_width = max(len("UNITS"), len(str(unit_count)))
    value_width = max(len("TOTAL VALUE"), len(total_value))
    header = "  ".join(
        [
            "PRODUCTS".rjust(product_width),
            "UNITS".rjust(unit_width),
            "TOTAL VALUE".rjust(value_width),
        ]
    )
    row = "  ".join(
        [
            str(product_count).rjust(product_width),
            str(unit_count).rjust(unit_width),
            total_value.rjust(value_width),
        ]
    )
    return "\n".join([header, row])


def compute_total_value(products: list[Product]) -> str:
    with localcontext() as context:
        context.prec = max(
            [28]
            + [
                len(product["price"]) + len(str(product["quantity"])) + 4
                for product in products
            ]
        )
        total = sum(
            (Decimal(product["price"]) * product["quantity"] for product in products),
            Decimal(0),
        )
        return f"{total:.2f}"


def cmd_add(args: argparse.Namespace) -> None:
    name = validate_name(args.name)
    price = validate_price(args.price)
    quantity = validate_quantity(args.quantity)
    store = load_store(args.file)
    product: Product = {
        "id": store["next_id"],
        "name": name,
        "price": price,
        "quantity": quantity,
    }
    store["products"].append(product)
    store["next_id"] = product["id"] + 1
    save_store(args.file, store)
    print_json(product)


def cmd_list(args: argparse.Namespace) -> None:
    store = load_store(args.file)
    products = sorted(store["products"], key=lambda product: product["id"])
    print_json(products)


def cmd_get(args: argparse.Namespace) -> None:
    product_id = validate_id(args.id)
    store = load_store(args.file)
    print_json(find_product(store, product_id))


def cmd_update(args: argparse.Namespace) -> None:
    product_id = validate_id(args.id)
    if args.name is None and args.price is None and args.quantity is None:
        raise CliError("update requires at least one of --name, --price, --quantity")
    name = validate_name(args.name) if args.name is not None else None
    price = validate_price(args.price) if args.price is not None else None
    quantity = validate_quantity(args.quantity) if args.quantity is not None else None
    store = load_store(args.file)
    product = find_product(store, product_id)
    if name is not None:
        product["name"] = name
    if price is not None:
        product["price"] = price
    if quantity is not None:
        product["quantity"] = quantity
    save_store(args.file, store)
    print_json(product)


def cmd_delete(args: argparse.Namespace) -> None:
    product_id = validate_id(args.id)
    store = load_store(args.file)
    product = find_product(store, product_id)
    store["products"].remove(product)
    save_store(args.file, store)
    print(json.dumps({"deleted_id": product_id}))


def cmd_search(args: argparse.Namespace) -> None:
    query = args.query.strip()
    if not query:
        raise CliError("--query must not be blank")
    store = load_store(args.file)
    needle = query.lower()
    matches = [
        product
        for product in sorted(store["products"], key=lambda product: product["id"])
        if needle in product["name"].lower()
    ]
    if not matches:
        print(f'No products found for "{query}".')
        return
    print(render_search_table(matches))


def cmd_summary(args: argparse.Namespace) -> None:
    store = load_store(args.file)
    products = store["products"]
    print(
        render_summary(
            len(products),
            sum(product["quantity"] for product in products),
            compute_total_value(products),
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="products.py",
        description="Storefront inventory CLI: manage products in a JSON data file.",
        epilog=(
            "command synopsis:\n"
            "  products.py [--file PATH] add --name NAME --price PRICE --quantity QTY\n"
            "  products.py [--file PATH] list\n"
            "  products.py [--file PATH] get ID\n"
            "  products.py [--file PATH] update ID [--name NAME] [--price PRICE] [--quantity QTY]\n"
            "  products.py [--file PATH] delete ID --yes\n"
            "  products.py [--file PATH] search --query TEXT\n"
            "  products.py [--file PATH] summary\n"
            "\n"
            'Run "products.py COMMAND --help" for the detailed usage of one command.'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
    )
    parser.add_argument(
        "--file",
        metavar="PATH",
        default=DEFAULT_FILE,
        help='path to the JSON data file (default: "%(default)s"); must come before the command',
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)

    add_parser = subparsers.add_parser(
        "add", help="add a new product", allow_abbrev=False
    )
    add_parser.add_argument("--name", required=True, metavar="NAME")
    add_parser.add_argument("--price", required=True, metavar="PRICE")
    add_parser.add_argument("--quantity", required=True, metavar="QTY")
    add_parser.set_defaults(func=cmd_add)

    list_parser = subparsers.add_parser(
        "list",
        help="print all products as a JSON array sorted by id",
        allow_abbrev=False,
    )
    list_parser.set_defaults(func=cmd_list)

    get_parser = subparsers.add_parser(
        "get", help="print one product as a JSON object", allow_abbrev=False
    )
    get_parser.add_argument("id", metavar="ID")
    get_parser.set_defaults(func=cmd_get)

    update_parser = subparsers.add_parser(
        "update", help="update fields of an existing product", allow_abbrev=False
    )
    update_parser.add_argument("id", metavar="ID")
    update_parser.add_argument("--name", metavar="NAME")
    update_parser.add_argument("--price", metavar="PRICE")
    update_parser.add_argument("--quantity", metavar="QTY")
    update_parser.set_defaults(func=cmd_update)

    delete_parser = subparsers.add_parser(
        "delete", help="delete an existing product", allow_abbrev=False
    )
    delete_parser.add_argument("id", metavar="ID")
    delete_parser.add_argument(
        "--yes",
        action="store_true",
        required=True,
        help="confirm deletion (required; no prompt)",
    )
    delete_parser.set_defaults(func=cmd_delete)

    search_parser = subparsers.add_parser(
        "search",
        help="find products whose name contains the query (read-only)",
        allow_abbrev=False,
    )
    search_parser.add_argument("--query", required=True, metavar="TEXT")
    search_parser.set_defaults(func=cmd_search)

    summary_parser = subparsers.add_parser(
        "summary",
        help="print product count, total units, and total shelf value (read-only)",
        allow_abbrev=False,
    )
    summary_parser.set_defaults(func=cmd_summary)

    return parser


def force_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", newline="\n")
        except (AttributeError, OSError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    force_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except StoreError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: file operation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
