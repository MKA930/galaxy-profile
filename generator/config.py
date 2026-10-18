"""Config validation and defaults for the Galaxy Profile generator."""

from generator.i18n import DEFAULT_LOCALE, LOCALES, normalize_locale
from generator.utils import resolve_theme, HEX_COLOR_RE


class ConfigError(ValueError):
    """Raised when config.yml has invalid or missing data."""


def _validate_i18n(config: dict) -> dict:
    """Validate the optional `i18n` block and fill in per-locale text.

    Shape:
        locale: en                 # global default
        i18n:
          en:
            name: "..."            # override any string from the en table
          zh:
            name: "..."
            tagline: "..."
            philosophy: "..."

    Overrides land in config["i18n"][locale] and are merged on top of the
    built-in string table by the templates. Recognised keys:

        name, tagline, philosophy   profile text
        galaxy_arms: [...]          localized arm names, matched by index
        projects: [...]             localized project descriptions, by index

    Arm labels resolve as: arms_overrides[locale][i] > arm.name.
    Project text resolves as: project_overrides[locale][i] > project.description.
    """
    locale = config.get("locale") or DEFAULT_LOCALE
    if not isinstance(locale, str):
        raise ConfigError("'locale' must be a string, e.g. 'en' or 'zh'.")
    if locale.strip().lower().split("-")[0] not in LOCALES:
        raise ConfigError(
            f"'locale' must be one of {', '.join(LOCALES)}, got '{locale}'."
        )
    config["locale"] = normalize_locale(locale)

    i18n = config.get("i18n", {})
    if not isinstance(i18n, dict):
        raise ConfigError("'i18n' must be a mapping of locale -> string overrides.")

    overrides = {}
    for lang, table in i18n.items():
        if not isinstance(table, dict):
            raise ConfigError(f"i18n.{lang} must be a mapping of string overrides.")
        code = normalize_locale(lang)
        cleaned = {}
        for key, value in table.items():
            if value is None:
                continue
            if key in ("galaxy_arms", "projects"):
                if not isinstance(value, list) or not all(
                    isinstance(v, str) for v in value
                ):
                    raise ConfigError(f"i18n.{lang}.{key} must be a list of strings.")
            elif not isinstance(value, (str, int, float)):
                raise ConfigError(f"i18n.{lang}.{key} must be a scalar value.")
            cleaned[key] = value
        overrides[code] = {**overrides.get(code, {}), **cleaned}
    config["i18n"] = overrides

    # profile[locale] — per-locale profile text overrides
    profile = config["profile"]
    profile_locales = profile.pop("locales", {})
    if profile_locales and not isinstance(profile_locales, dict):
        raise ConfigError("'profile.locales' must be a mapping of locale -> fields.")
    profile["locales"] = {
        normalize_locale(lang): dict(fields)
        for lang, fields in (profile_locales or {}).items()
        if isinstance(fields, dict)
    }

    return config


def validate_config(config: dict) -> dict:
    """Validate and apply defaults to a parsed config dict.

    Args:
        config: raw dict from yaml.safe_load()

    Returns:
        config dict with defaults applied for optional fields

    Raises:
        ConfigError: if required fields are missing or values are invalid
    """
    if not isinstance(config, dict):
        raise ConfigError("Config must be a YAML mapping (dict).")

    # username — required
    username = config.get("username")
    if not username or not isinstance(username, str) or not username.strip():
        raise ConfigError("'username' is required and must be a non-empty string.")

    # profile.name — required
    profile = config.get("profile", {})
    if not isinstance(profile, dict):
        raise ConfigError("'profile' must be a mapping.")
    if not profile.get("name"):
        raise ConfigError("'profile.name' is required.")

    # galaxy_arms — required, must be a list
    galaxy_arms = config.get("galaxy_arms", [])
    if not isinstance(galaxy_arms, list) or not galaxy_arms:
        raise ConfigError("'galaxy_arms' must be a non-empty list.")
    for i, arm in enumerate(galaxy_arms):
        if not isinstance(arm, dict):
            raise ConfigError(f"galaxy_arms[{i}] must be a mapping.")
        if not arm.get("name"):
            raise ConfigError(f"galaxy_arms[{i}].name is required.")
        if not arm.get("color"):
            raise ConfigError(f"galaxy_arms[{i}].color is required.")
        if not isinstance(arm.get("items", []), list):
            raise ConfigError(f"galaxy_arms[{i}].items must be a list.")

    # projects — optional, validate entries if present
    projects = config.get("projects", [])
    if not isinstance(projects, list):
        raise ConfigError("'projects' must be a list.")
    for i, proj in enumerate(projects):
        if not isinstance(proj, dict):
            raise ConfigError(f"projects[{i}] must be a mapping.")
        if not proj.get("repo"):
            raise ConfigError(f"projects[{i}].repo is required.")
        arm_idx = proj.get("arm", 0)
        if not isinstance(arm_idx, int) or arm_idx < 0 or arm_idx >= len(galaxy_arms):
            raise ConfigError(
                f"projects[{i}].arm must be an integer from 0 to {len(galaxy_arms) - 1}."
            )

    # theme — optional, validate hex codes
    user_theme = config.get("theme", {})
    if not isinstance(user_theme, dict):
        raise ConfigError("'theme' must be a mapping.")
    for key, value in user_theme.items():
        if not isinstance(value, str) or not HEX_COLOR_RE.match(value):
            raise ConfigError(
                f"theme.{key} must be a valid hex color (e.g. #00d4ff), got '{value}'."
            )

    # Apply theme defaults
    config["theme"] = resolve_theme(user_theme)

    # Apply other defaults
    config["profile"].setdefault("tagline", "")
    config["profile"].setdefault("philosophy", "")
    for i, arm in enumerate(galaxy_arms):
        arm.setdefault("items", [])
    config.setdefault("social", {})
    config.setdefault("projects", [])
    config.setdefault("stats", {}).setdefault(
        "metrics", ["commits", "stars", "prs", "issues", "repos"]
    )
    lang_cfg = config.setdefault("languages", {})
    lang_cfg.setdefault("exclude", [])
    lang_cfg.setdefault("max_display", 8)

    # i18n / locale
    _validate_i18n(config)

    return config
