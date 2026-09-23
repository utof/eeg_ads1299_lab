#!/usr/bin/env python3
"""Entry point: python run_lab.py --help. Defaults require NO hardware."""

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from lab.signals import SyntheticConfig

ROOT = Path(__file__).resolve().parent


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="ADS1299 learning lab: models, tests, and bench-only transport"
    )
    sub = p.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Generate and analyze only synthetic EEG-like recordings")
    demo.add_argument("--out", type=Path, default=ROOT / "results/demo")
    demo.add_argument("--config", type=Path)
    demo.add_argument("--seed", type=int)
    demo.add_argument("--channels", type=int, choices=[4, 6, 8])
    demo.add_argument("--line-hz", type=int, choices=[50, 60])
    demo.add_argument("--null-effect", action="store_true")
    demo.add_argument("--permutations", type=int, default=20)
    demo.add_argument("--no-plots", action="store_true")
    circuits = sub.add_parser(
        "circuits", help="Solve a passive model; export SPICE; compare when installed"
    )
    circuits.add_argument("--out", type=Path, default=ROOT / "results/circuits")
    circuits.add_argument("--require-ngspice", action="store_true")
    verify = sub.add_parser(
        "verify", help="Run automated tests and record exact verification scope"
    )
    verify.add_argument("--require-ngspice", action="store_true")
    receive = sub.add_parser("receive", help="Capture synthetic/bench UDP; localhost default")
    receive.add_argument("--out", type=Path, default=ROOT / "results/capture.bin")
    receive.add_argument("--host", default="127.0.0.1")
    receive.add_argument("--port", type=int, default=9000)
    receive.add_argument("--seconds", type=float, default=10)
    replay = sub.add_parser(
        "replay", help="Send synthetic UDP packets at the nominal acquisition rate"
    )
    replay.add_argument("--host", default="127.0.0.1")
    replay.add_argument("--port", type=int, default=9000)
    replay.add_argument("--seconds", type=float, default=3)
    replay.add_argument("--channels", type=int, choices=[4, 6, 8], default=4)
    replay.add_argument("--drop-every", type=int, default=0)
    decode = sub.add_parser(
        "decode", help="Decode transport file to CSV without interpolating gaps"
    )
    decode.add_argument("input", type=Path)
    decode.add_argument("--out", type=Path, default=ROOT / "results/capture.csv")
    decode.add_argument("--vref", type=float, default=4.5)
    inspect = sub.add_parser(
        "inspect", help="Gap-safe quality and PSD report from decoded bench CSV"
    )
    inspect.add_argument("input", type=Path)
    inspect.add_argument("--out", type=Path, default=ROOT / "results/capture_quality")
    serial = sub.add_parser(
        "serial", help="USB bench capture ONLY, all body electrodes disconnected"
    )
    serial.add_argument("--port", required=True)
    serial.add_argument("--out", type=Path, default=ROOT / "results/serial.bin")
    serial.add_argument("--seconds", type=float, default=10)
    serial.add_argument("--acknowledge-bench-only", action="store_true", required=True)
    return p


def _run_demo(args: argparse.Namespace) -> None:
    from lab.pipeline import run_demo

    config_path: Path | None = args.config
    if config_path is None:
        cfg = SyntheticConfig()
    else:
        raw_config: object = json.loads(config_path.read_text())
        cfg = SyntheticConfig.from_mapping(raw_config)
    changes = {
        k: getattr(args, k) for k in ["seed", "channels", "line_hz"] if getattr(args, k) is not None
    }
    if args.null_effect:
        changes["null_effect"] = True
    cfg = replace(cfg, **changes)
    if args.permutations < 0:
        raise ValueError("permutations must be >=0")
    report = run_demo(args.out, cfg, args.permutations, not args.no_plots)
    print(
        json.dumps(
            {
                "kind": report["kind"],
                "accepted_epochs": report["accepted_epochs"],
                "rejected_epochs": report["rejected_epochs"],
                "closed_open_alpha_ratio": report["closed_open_alpha_ratio"],
                "balanced_accuracy": report["balanced_accuracy"],
                "baseline_balanced_accuracy": report["baseline_balanced_accuracy"],
                "block_permutation_mean": report["block_permutation_mean"],
            },
            indent=2,
        )
    )
    print(f"Outputs: {args.out.resolve()}")


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "demo":
        _run_demo(args)
    elif args.command == "circuits":
        from lab.analog import circuit_report

        print(json.dumps(circuit_report(args.out, require_ngspice=args.require_ngspice), indent=2))
    elif args.command == "verify":
        from tools.validate import validate

        return validate(ROOT, args.require_ngspice)
    elif args.command == "receive":
        from lab.acquisition import capture_udp

        print(json.dumps(capture_udp(args.out, args.seconds, args.host, args.port), indent=2))
    elif args.command == "replay":
        from lab.acquisition import replay_packets

        print(
            json.dumps(
                replay_packets(
                    args.host,
                    args.port,
                    args.seconds,
                    args.channels,
                    drop_every=args.drop_every,
                ),
                indent=2,
            )
        )
    elif args.command == "decode":
        from lab.acquisition import decode_capture

        print(json.dumps(decode_capture(args.input, args.out, args.vref), indent=2))
    elif args.command == "inspect":
        from lab.inspect_capture import inspect_capture

        print(json.dumps(inspect_capture(args.input, args.out), indent=2))
    elif args.command == "serial":
        from lab.acquisition import capture_serial

        print(json.dumps(capture_serial(args.out, args.port, args.seconds), indent=2))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _dispatch(args)
    except (ValueError, RuntimeError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
