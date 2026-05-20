# python/ch02/env_check.py
import platform
import sys


def main() -> None:
    major, minor = sys.version_info[:2]
    print(f"executable: {sys.executable}")
    print(f"version: {platform.python_version()}")
    if (major, minor) < (3, 10):
        print("WARN: Python 3.10+ recommended", file=sys.stderr)
    else:
        print("status: OK")


if __name__ == "__main__":
    main()
