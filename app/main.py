"""
Fashion Agent — App-level entry point.

Usage:
    python main.py <path-to-image>
    python main.py /path/to/garment.jpg
"""

import sys
from fashion_agent.main import run


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path-to-image>")
        sys.exit(1)

    run(sys.argv[1])


if __name__ == "__main__":
    main()
