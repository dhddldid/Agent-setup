#!/usr/bin/env python3
"""한국어 말뭉치의 실제 OMH Route Hint를 공통 점검기로 측정한다."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from check_parallel_gaps import routing


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=HERE / "ko.json")
    parser.add_argument("--corpus", type=Path, default=HERE / "ko-corpus.json")
    parser.add_argument("--omh", default="omh")
    args = parser.parse_args(argv)
    result = routing(args.corpus, omh=args.omh, pack=args.pack)
    print(f"multi hit rate: {result['multi_hits']}/{result['multi_total']} = {result['multi_hit_rate']:.2%}")
    print(f"small FP rate: {result['small_misses']}/{result['small_total']} = {result['small_fp_rate']:.2%}")
    print(f"shipped-rule-claimed count: {result['shipped_rule_claimed']}")
    print("misses: " + json.dumps(result["misses"], ensure_ascii=False))
    return int(result["threshold_exceeded"])


if __name__ == "__main__":
    raise SystemExit(main())
