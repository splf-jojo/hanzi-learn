from argparse import ArgumentParser
from pathlib import Path

from .parsers import DEFAULT_MARKDOWN_DIR
from .services.seeding import seed_database


def main() -> None:
    parser = ArgumentParser(description="Import markdown learning data into the normalized Chinese vocab schema.")
    parser.add_argument("--markdown-dir", type=Path, default=DEFAULT_MARKDOWN_DIR)
    parser.add_argument("--if-empty", action="store_true", help="Do nothing if the words table already has data.")
    args = parser.parse_args()

    data = seed_database(args.markdown_dir, only_if_empty=args.if_empty)
    if data is None:
        print("seed skipped: data present")
        return

    print(f"Imported {len(data.words)} words, {len(data.sentences)} sentences, {len(data.groups)} groups.")


if __name__ == "__main__":
    main()
