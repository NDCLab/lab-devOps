import argparse

from . import create_scaffolds, match_syllables


def get_args():
    parser = argparse.ArgumentParser(
        description="Process commands to create scaffolds or match syllables."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser(
        "create", help="Create scaffolds from a directory"
    )
    create_parser.add_argument(
        "directory", type=str, help="Directory to process for scaffold creation"
    )

    match_parser = subparsers.add_parser("match", help="Match syllables")
    match_parser.add_argument(
        "directory", type=str, help="Directory to process for matching syllables"
    )
    match_parser.add_argument("syllable_id", type=str, help="Syllable ID to match")

    return parser.parse_args()


def main():
    args = get_args()

    if args.command == "create":
        create_scaffolds.main(args.directory)
    elif args.command == "match":
        match_syllables.main(args.directory, args.syllable_id)


if __name__ == "__main__":
    main()
