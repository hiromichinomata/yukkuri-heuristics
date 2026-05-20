# python/templates/io_template.py
import sys


def read_ints():
    return list(map(int, sys.stdin.readline().split()))


def main():
    n, = read_ints()
    a = read_ints()
    print(sum(a))


if __name__ == "__main__":
    main()
