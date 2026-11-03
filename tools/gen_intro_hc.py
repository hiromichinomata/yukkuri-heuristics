#!/usr/bin/env python3
"""Intro HC（AtCoder Introduction to Heuristics Contest）形式の入力を生成する.

公式と同じ分布: D = 365、c_i は 0〜100、s_{d,i} は 0〜20000 の一様乱数。

  python tools/gen_intro_hc.py --seed 1 > data/common/intro_hc_d365.txt
  python tools/gen_intro_hc.py --seed 2 --days 50   # 小さめの入力
"""
import argparse
import random


def main() -> None:
    parser = argparse.ArgumentParser(description="Intro HC 形式の入力を生成")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--days", type=int, default=365)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    print(args.days)
    print(" ".join(str(rng.randint(0, 100)) for _ in range(26)))
    for _ in range(args.days):
        print(" ".join(str(rng.randint(0, 20000)) for _ in range(26)))


if __name__ == "__main__":
    main()
