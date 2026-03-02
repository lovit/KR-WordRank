"""Command-line interface for keyword and key-sentence extraction."""

import argparse
import json
import sys

from krwordrank.sentence import summarize_with_sentences
from krwordrank.word import summarize_with_keywords


def _read_texts(stream, fmt: str = "text", field: str | None = None) -> list[str]:
    """Read documents from a file-like object.

    - text: One document per line. If a line contains a tab, only the first column is used.
    - jsonl: Each line is a JSON object; the value at *field* is used as the document text.
    """
    if fmt == "text":
        texts = []
        for line in stream:
            line = line.strip()
            if not line:
                continue
            if "\t" in line:
                line = line.split("\t", 1)[0].strip()
            texts.append(line)
        return texts

    if fmt == "jsonl":
        if not field:
            raise ValueError("--field is required when --format is jsonl")
        texts = []
        for line in stream:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if field not in obj:
                raise KeyError(f"field {field!r} not found in JSON line: {line[:80]}...")
            val = obj[field]
            if not isinstance(val, str):
                raise TypeError(f"field {field!r} must be string, got {type(val).__name__}")
            texts.append(val)
        return texts

    raise ValueError(f"unsupported format: {fmt}")


def _parse_stopwords(s: str | None) -> set[str]:
    if not s or not s.strip():
        return set()
    return {w.strip() for w in s.split(",") if w.strip()}


def _open_input(path: str | None):
    if path is None:
        return sys.stdin
    return open(path, encoding="utf-8")


def cmd_keywords(args: argparse.Namespace) -> int:
    if args.format == "jsonl" and not getattr(args, "field", None):
        print("error: --field is required when --format is jsonl", file=sys.stderr)
        return 1

    with _open_input(args.input) as f:
        try:
            texts = _read_texts(f, fmt=args.format, field=getattr(args, "field", None))
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

    if not texts:
        print("error: no input documents (use a file or stdin)", file=sys.stderr)
        return 1

    stopwords = _parse_stopwords(args.stopwords)
    keywords = summarize_with_keywords(
        texts,
        num_keywords=args.num_keywords,
        stopwords=stopwords,
        min_count=args.min_count,
        max_length=args.max_length,
        beta=args.beta,
        max_iter=args.max_iter,
        verbose=args.verbose,
    )

    if args.json:
        out = [{"word": w, "rank": r} for w, r in keywords.items()]
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for word, rank in keywords.items():
            print(f"{word}\t{rank:.6f}")
    return 0


def cmd_keysents(args: argparse.Namespace) -> int:
    if args.format == "jsonl" and not getattr(args, "field", None):
        print("error: --field is required when --format is jsonl", file=sys.stderr)
        return 1

    with _open_input(args.input) as f:
        try:
            texts = _read_texts(f, fmt=args.format, field=getattr(args, "field", None))
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

    if not texts:
        print("error: no input documents (use a file or stdin)", file=sys.stderr)
        return 1

    stopwords = _parse_stopwords(args.stopwords)
    penalty = None
    if args.min_len is not None and args.max_len is not None:
        min_len, max_len = args.min_len, args.max_len

        def penalty(x: str) -> float:
            return 0 if min_len <= len(x) <= max_len else 1

    return_indices = args.show_indices
    result = summarize_with_sentences(
        texts,
        num_keywords=args.num_keywords,
        num_keysents=args.num_keysents,
        diversity=args.diversity,
        stopwords=stopwords,
        penalty=penalty,
        min_count=args.min_count,
        max_length=args.max_length,
        beta=args.beta,
        max_iter=args.max_iter,
        verbose=args.verbose,
        return_indices=return_indices,
    )

    if return_indices:
        keywords, sents, indices = result
    else:
        keywords, sents = result
        indices = None

    if args.json:
        out = {
            "keywords": [{"word": w, "rank": r} for w, r in keywords.items()],
            "sentences": sents,
        }
        if indices is not None:
            out["indices"] = indices
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        if not args.keywords_only:
            for word, rank in keywords.items():
                print(f"keyword\t{word}\t{rank:.6f}")
            print("---")
        for i, sent in enumerate(sents, start=1):
            prefix = f"{indices[i - 1]}\t" if indices is not None else (f"{i}. " if args.number else "")
            print(f"{prefix}{sent}")
    return 0


def _add_common_input_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default=None,
        metavar="FILE",
        help="Input file. Default: stdin.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose progress.")
    parser.add_argument(
        "--format",
        choices=("text", "jsonl"),
        default="text",
        help="Input format: text (one document per line, tab uses first column) or jsonl (JSON Lines). Default: text.",
    )
    parser.add_argument(
        "--field",
        type=str,
        default=None,
        metavar="KEY",
        help="For --format jsonl: JSON key whose value is the document text (required when format is jsonl).",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="krwordrank",
        description="KR-WordRank: Unsupervised Korean word/keyword and key-sentence extraction.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommand.")

    # --- keywords ---
    kw = subparsers.add_parser("keywords", help="Extract keywords only.")
    _add_common_input_args(kw)
    kw.add_argument(
        "-n",
        "--num-keywords",
        type=int,
        default=100,
        metavar="N",
        help="Number of keywords to extract (default: 100).",
    )
    kw.add_argument(
        "--min-count",
        type=int,
        default=5,
        metavar="N",
        help="Minimum subword frequency (default: 5).",
    )
    kw.add_argument(
        "--max-length",
        type=int,
        default=10,
        metavar="N",
        help="Maximum subword length (default: 10).",
    )
    kw.add_argument("--beta", type=float, default=0.85, help="PageRank damping factor (default: 0.85).")
    kw.add_argument("--max-iter", type=int, default=10, help="Max HITS iterations (default: 10).")
    kw.add_argument(
        "-s",
        "--stopwords",
        type=str,
        default=None,
        metavar="W1,W2,...",
        help="Comma-separated stopwords to exclude.",
    )
    kw.add_argument("--json", action="store_true", help="Output as JSON.")
    kw.set_defaults(run=cmd_keywords)

    # --- keysents ---
    ks = subparsers.add_parser("keysents", help="Extract keywords and key sentences.")
    _add_common_input_args(ks)
    ks.add_argument(
        "-n",
        "--num-keywords",
        type=int,
        default=100,
        metavar="N",
        help="Number of keywords (default: 100).",
    )
    ks.add_argument(
        "-k",
        "--num-keysents",
        type=int,
        default=10,
        metavar="N",
        help="Number of key sentences (default: 10).",
    )
    ks.add_argument(
        "--diversity",
        type=float,
        default=0.3,
        metavar="D",
        help="Min cosine distance between sentences, 0–1 (default: 0.3).",
    )
    ks.add_argument(
        "--min-len",
        type=int,
        default=None,
        metavar="L",
        help="Prefer sentences with length >= L (use with --max-len).",
    )
    ks.add_argument(
        "--max-len",
        type=int,
        default=None,
        metavar="L",
        help="Prefer sentences with length <= L (use with --min-len).",
    )
    ks.add_argument(
        "--min-count",
        type=int,
        default=5,
        metavar="N",
        help="Minimum subword frequency (default: 5).",
    )
    ks.add_argument(
        "--max-length",
        type=int,
        default=10,
        metavar="N",
        help="Maximum subword length (default: 10).",
    )
    ks.add_argument("--beta", type=float, default=0.85, help="PageRank damping factor (default: 0.85).")
    ks.add_argument("--max-iter", type=int, default=10, help="Max HITS iterations (default: 10).")
    ks.add_argument(
        "-s",
        "--stopwords",
        type=str,
        default=None,
        metavar="W1,W2,...",
        help="Comma-separated stopwords to exclude.",
    )
    ks.add_argument("--json", action="store_true", help="Output as JSON.")
    ks.add_argument(
        "--keywords-only",
        action="store_true",
        help="In text output, print only key sentences (no keyword list).",
    )
    ks.add_argument(
        "--number",
        action="store_true",
        help="In text output, prefix each sentence with 1., 2., ...",
    )
    ks.add_argument(
        "--show-indices",
        action="store_true",
        help="Print original text index (0-based) before each sentence.",
    )
    ks.set_defaults(run=cmd_keysents)

    args = parser.parse_args()
    return args.run(args)
