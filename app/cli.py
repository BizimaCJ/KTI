"""Command line tools.

  python -m app.cli init-db
  python -m app.cli seed
  python -m app.cli simulate --scenario peak_hour
  python -m app.cli simulate --scenario auto --loop --interval 60
"""
import argparse
import logging
import sys
import time

import app.models  # noqa: F401  (registers all tables)
from sqlalchemy.exc import OperationalError
from app.config import get_settings
from app.database import Base, get_engine, session_scope
from app.modules.network.service import seed_network
from app.modules.simulation.generator import SimulatedDataGenerator, SimulationError
from app.modules.simulation.scenarios import Scenario


def cmd_init_db(args) -> int:
    Base.metadata.create_all(get_engine())
    print("Tables created (existing tables were left untouched).")
    return 0


def cmd_seed(args) -> int:
    with session_scope() as db:
        result = seed_network(db)
    print(f"Seeded {result.intersections_created} intersections and {result.roads_created} roads.")
    return 0


def cmd_simulate(args) -> int:
    settings = get_settings()
    generator = SimulatedDataGenerator(args.scenario, refresh_interval_seconds=args.interval)
    cycles = 0
    while True:
        try:
            with session_scope() as db:
                r = generator.run_cycle(db)
        except SimulationError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        cycles += 1
        print(f"[{r.recorded_at:%H:%M:%S}] {r.scenario.value}: {r.conditions_created} conditions, "
              f"{r.incidents_created} incidents created, {r.incidents_resolved} resolved")
        if not args.loop or (args.cycles and cycles >= args.cycles):
            return 0
        time.sleep(generator.refresh_interval_seconds)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="Kigali Traffic Insight tools")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db", help="create the database tables").set_defaults(func=cmd_init_db)
    sub.add_parser("seed", help="add the Nyabugogo roads and intersections").set_defaults(func=cmd_seed)
    sim = sub.add_parser("simulate", help="generate simulated traffic data")
    choices = ["auto"] + [s.value.lower() for s in Scenario]
    sim.add_argument("--scenario", default=get_settings().simulation_scenario, choices=choices)
    sim.add_argument("--loop", action="store_true", help="keep running until stopped (Ctrl+C)")
    sim.add_argument("--interval", type=int, default=get_settings().simulation_interval_seconds,
                     help="seconds between cycles when looping")
    sim.add_argument("--cycles", type=int, default=0, help="stop after N cycles when looping (0 = forever)")
    sim.set_defaults(func=cmd_simulate)
    return parser


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0
    except OperationalError as exc:
        reason = str(exc.orig).strip().splitlines()[0] if exc.orig else "unknown error"
        print(f"Cannot reach the database: {reason}\n"
              f"Check that PostgreSQL is running and that KTI_DATABASE_URL in .env is correct.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
