#!/usr/bin/env python3
"""
Command-line interface for subtitle extraction tool.

This CLI provides a simple interface to extract subtitles from video URLs
using the subtitle_extractor module.
"""

import argparse
import sys
import logging
from typing import NoReturn

from subtitle_extractor import extract_subtitles


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level."""
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        stream=sys.stderr
    )


def validate_url(url: str) -> bool:
    """
    Basic URL validation to provide early feedback.

    Args:
        url (str): URL to validate

    Returns:
        bool: True if URL appears valid
    """
    from urllib.parse import urlparse

    try:
        result = urlparse(url)
        return bool(result.scheme and result.netloc)
    except Exception:
        return False


def print_error(message: str) -> None:
    """Print error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)


def exit_with_error(message: str, exit_code: int = 1) -> NoReturn:
    """Print error message and exit with specified code."""
    print_error(message)
    sys.exit(exit_code)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Extract subtitles from video URLs",
        epilog="""
Examples:
  %(prog)s "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  %(prog)s "https://example.com/video" --language es
  %(prog)s "https://example.com/video" > subtitles.txt
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'url',
        help='Video URL to extract subtitles from'
    )

    parser.add_argument(
        '-l', '--language',
        default='en',
        help='Language code for subtitles (default: en)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    return parser


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Validate URL format
    if not validate_url(args.url):
        exit_with_error(f"Invalid URL format: {args.url}", 2)

    if args.verbose:
        logging.info(f"Extracting subtitles from: {args.url}")
        logging.info(f"Language: {args.language}")

    try:
        # Extract subtitles
        subtitles = extract_subtitles(args.url, args.language)

        if not subtitles:
            if args.verbose:
                logging.info("No subtitles found or extraction failed")
            exit_with_error(
                f"No subtitles found for language '{args.language}' at {args.url}",
                1
            )

        # Output subtitles to stdout
        print(subtitles)

        if args.verbose:
            logging.info(f"Successfully extracted {len(subtitles)} characters")

    except KeyboardInterrupt:
        exit_with_error("Operation cancelled by user", 1)

    except Exception as e:
        if args.verbose:
            logging.exception("Unexpected error occurred")
        exit_with_error(f"Failed to extract subtitles: {str(e)}", 1)


if __name__ == "__main__":
    main()
