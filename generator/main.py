"""Entry point for the Galaxy Profile README generator."""

import argparse
import logging
import os
import sys

import requests
import yaml

from generator.config import ConfigError, validate_config
from generator.github_api import GitHubAPI
from generator.i18n import DEFAULT_LOCALE, LOCALES, normalize_locale
from generator.svg_builder import SVGBuilder

logger = logging.getLogger(__name__)

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS_DIR = os.path.join(REPO_ROOT, "assets", "generated")

DEMO_STATS = {"commits": 1847, "stars": 342, "prs": 156, "issues": 89, "repos": 42}
DEMO_LANGUAGES = {
    "Python": 450000,
    "TypeScript": 380000,
    "JavaScript": 120000,
    "Go": 95000,
    "Rust": 45000,
    "Shell": 30000,
    "Dockerfile": 15000,
    "CSS": 10000,
}


def parse_locales(value) -> list:
    """Parse a --locales value like "en,zh" into a validated locale list."""
    if not value:
        return list(LOCALES)
    if isinstance(value, (list, tuple)):
        raw = value
    else:
        raw = str(value).replace(" ", ",").split(",")
    out = []
    for item in raw:
        if not item:
            continue
        code = normalize_locale(item)
        if code not in out:
            out.append(code)
    return out or list(LOCALES)


def generate(args):
    """Generate SVGs from config (existing behavior extracted into a function)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    demo = getattr(args, "demo", False)
    skip_fetch = getattr(args, "skip_fetch", False)
    locales = parse_locales(getattr(args, "locales", None))

    # Load config
    if demo:
        config_path = os.path.join(REPO_ROOT, "config.example.yml")
    elif getattr(args, "config", None):
        config_path = args.config
    else:
        config_path = os.path.join(REPO_ROOT, "config.yml")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        if demo:
            logger.error("config.example.yml not found.")
        else:
            logger.error("config.yml not found. Copy config.example.yml to config.yml and edit it.")
        sys.exit(1)

    try:
        config = validate_config(config)
    except ConfigError as e:
        logger.error("Invalid config: %s", e)
        sys.exit(1)

    username = config["username"]

    logger.info("Generating profile SVGs for @%s...", username)
    logger.info("Locales: %s", ", ".join(locales))

    if demo:
        logger.info("Demo mode: using hardcoded stats and languages.")
        stats = DEMO_STATS
        languages = DEMO_LANGUAGES
    elif skip_fetch:
        logger.info("Skip-fetch mode: using the previous run's GitHub data.")
        stats, languages = load_cached_stats()
    else:
        # Fetch GitHub data
        api = GitHubAPI(username)

        logger.info("Fetching stats...")
        try:
            stats = api.fetch_stats()
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            logger.warning("Could not fetch stats (%s). Using defaults.", e)
            stats = {"commits": 0, "stars": 0, "prs": 0, "issues": 0, "repos": 0}

        logger.info("Fetching languages...")
        try:
            languages = api.fetch_languages()
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            logger.warning("Could not fetch languages (%s). Using defaults.", e)
            languages = {}

    logger.info("Stats: %s", stats)
    logger.info("Languages: %d found", len(languages))

    written = 0
    for locale in locales:
        builder = SVGBuilder(config, stats, languages, locale=locale)
        output_dir = os.path.join(ASSETS_DIR, locale)
        os.makedirs(output_dir, exist_ok=True)

        for filename, content in builder.render_all().items():
            path = os.path.join(output_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Wrote %s", path)
            written += 1

    # Backwards compatibility: the default locale is also written one level up,
    # so existing <img src="assets/generated/galaxy-header.svg"> links keep working.
    # Skip with --no-legacy-copy (used when the root files are replaced by redirect stubs).
    legacy_copy = locales[0] if locales else DEFAULT_LOCALE
    if not getattr(args, "no_legacy_copy", False):
        builder = SVGBuilder(config, stats, languages, locale=legacy_copy)
        for filename, content in builder.render_all().items():
            path = os.path.join(ASSETS_DIR, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Wrote %s", path)

    logger.info("Done! %d SVGs generated across %d locale(s).", written, len(locales))


def load_cached_stats():
    """Read stats/languages left by a previous run, falling back to demo values."""
    stats_path = os.path.join(REPO_ROOT, ".cache", "stats.json")
    try:
        import json

        with open(stats_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("stats", DEMO_STATS), data.get("languages", DEMO_LANGUAGES)
    except (FileNotFoundError, ValueError):
        logger.warning("No cached stats found; using demo data.")
        return DEMO_STATS, DEMO_LANGUAGES


def main():
    parser = argparse.ArgumentParser(description="Generate Galaxy Profile SVGs")
    subparsers = parser.add_subparsers(dest="command")

    # Subcommand: init
    subparsers.add_parser("init", help="Interactive setup wizard to create config.yml")

    def add_generate_flags(p):
        p.add_argument(
            "--demo",
            action="store_true",
            help="Generate SVGs with demo data (no API calls, uses config.example.yml)",
        )
        p.add_argument(
            "--locales",
            default=None,
            help="Comma-separated locales to render, e.g. en,zh (default: all supported)",
        )
        p.add_argument(
            "--config",
            default=None,
            help="Path to an alternative config file",
        )
        p.add_argument(
            "--skip-fetch",
            action="store_true",
            help="Reuse the stats from .cache/stats.json instead of calling the GitHub API",
        )
        p.add_argument(
            "--no-legacy-copy",
            action="store_true",
            help="Do not also write the first locale into assets/generated/",
        )

    # Subcommand: generate
    gen_parser = subparsers.add_parser("generate", help="Generate SVGs from config")
    add_generate_flags(gen_parser)

    # Top-level --demo for backward compatibility (python -m generator.main --demo)
    add_generate_flags(parser)

    args = parser.parse_args()

    if args.command == "init":
        from generator.cli_init import run_init
        run_init()
    else:
        # Default behavior: generate (supports both `generate --demo` and `--demo`)
        generate(args)


if __name__ == "__main__":
    main()
