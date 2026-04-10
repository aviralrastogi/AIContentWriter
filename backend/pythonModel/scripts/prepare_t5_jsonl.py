#!/usr/bin/env python3
"""
Download public seq2seq data from Hugging Face Datasets and write JSONL for T5 fine-tuning.

Each line: {"input": "summarize: ...", "target": "..."}

Heavy / large sources (load with --max-samples or omit for full train split):

  ccdv/cnn_dailymail     ~287k train, ~534 MB — article → highlights (great for “short content”)
  EdinburghNLP/xsum      ~204k train — document → one-line BBC summary (very abstractive)
  big_patent             1.2M+ train (subset configs a–y) — description → abstract (use --config g --stream)
  reddit_tifu (long)     long posts → TL;DR (see dataset card; medium size)

Install: pip install datasets

Examples:
  py -3 prepare_t5_jsonl.py --dataset ccdv/cnn_dailymail --split train --out cnn_train.jsonl
  py -3 prepare_t5_jsonl.py --dataset EdinburghNLP/xsum --split train --max-samples 50000 --out xsum_50k.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Callable, Iterator


def rows_cnn_dailymail(ex) -> tuple[str, str]:
    return ex["article"].strip(), ex["highlights"].strip()


def rows_xsum(ex) -> tuple[str, str]:
    return ex["document"].strip(), ex["summary"].strip()


def rows_big_patent(ex) -> tuple[str, str]:
    # config names like "d", "e", "f", "g", "h", "y" — description + abstract
    return ex["description"].strip(), ex["abstract"].strip()


# (dataset_config_for_load_dataset_name, row_mapper, default_t5_prefix)
REGISTRY: dict[str, tuple[str | None, Callable[[dict], tuple[str, str]], str]] = {
    "ccdv/cnn_dailymail": ("3.0.0", rows_cnn_dailymail, "summarize:"),
    "EdinburghNLP/xsum": (None, rows_xsum, "summarize:"),
    "big_patent": (None, rows_big_patent, "summarize:"),  # requires --config e.g. g, h, all
}


def iter_examples(
    dataset_id: str,
    split: str,
    max_samples: int | None,
    streaming: bool,
    subset_config: str | None,
) -> Iterator[tuple[str, str]]:
    from datasets import load_dataset

    if dataset_id not in REGISTRY:
        print("Known datasets:", ", ".join(REGISTRY), file=sys.stderr)
        raise SystemExit(1)

    config, mapper, _ = REGISTRY[dataset_id]
    if dataset_id == "big_patent" and not subset_config:
        print("big_patent requires --config (e.g. g, h, or all). See dataset card on Hugging Face.", file=sys.stderr)
        raise SystemExit(1)
    name = subset_config if dataset_id == "big_patent" else config
    kwargs = {
        "path": dataset_id,
        "split": split,
        "streaming": streaming,
        "trust_remote_code": False,
    }
    if name is not None:
        kwargs["name"] = name

    ds = load_dataset(**kwargs)
    n = 0
    for ex in ds:
        inp, tgt = mapper(ex)
        if not inp or not tgt:
            continue
        yield inp, tgt
        n += 1
        if max_samples is not None and n >= max_samples:
            break


def main() -> None:
    p = argparse.ArgumentParser(description="Export HF datasets to T5 JSONL")
    p.add_argument("--dataset", required=True, help="HF dataset id, e.g. ccdv/cnn_dailymail")
    p.add_argument("--split", default="train")
    p.add_argument("--out", required=True, help="Output .jsonl path")
    p.add_argument("--max-samples", type=int, default=None)
    p.add_argument(
        "--stream",
        action="store_true",
        help="Use streaming (needed for very large sets like big_patent)",
    )
    p.add_argument(
        "--config",
        default=None,
        help="Subset for multi-config datasets (required for big_patent: g, h, all, ...)",
    )
    p.add_argument(
        "--prefix",
        default=None,
        help="T5 task prefix (default: per-dataset, usually summarize:)",
    )
    args = p.parse_args()

    _, _, default_prefix = REGISTRY[args.dataset]
    prefix = (args.prefix or default_prefix).rstrip() + " "

    count = 0
    with open(args.out, "w", encoding="utf-8") as f:
        for inp, tgt in iter_examples(
            args.dataset,
            args.split,
            args.max_samples,
            streaming=args.stream,
            subset_config=args.config,
        ):
            line = json.dumps(
                {"input": f"{prefix}{inp}", "target": tgt},
                ensure_ascii=False,
            )
            f.write(line + "\n")
            count += 1
            if count % 5000 == 0:
                print(count, "rows...", file=sys.stderr)

    print(f"Wrote {count} lines to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
