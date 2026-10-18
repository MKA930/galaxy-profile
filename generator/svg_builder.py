"""SVG Builder — orchestrator connecting config, stats, and templates."""

from generator.i18n import (
    DEFAULT_LOCALE,
    get_fonts,
    get_strings,
    get_title_tracking,
    normalize_locale,
)
from generator.templates import galaxy_header, stats_card, tech_stack, projects_constellation

# Profile text fields that can be overridden per locale.
PROFILE_TEXT_FIELDS = ("name", "tagline", "philosophy")


class SVGBuilder:
    """Builds all SVG assets from config and GitHub data.

    Expects a config dict that has already been through validate_config(),
    which resolves theme defaults and applies missing optional fields.
    """

    def __init__(self, config: dict, stats: dict, languages: dict, locale: str | None = None):
        self.config = config
        self.stats = stats
        self.languages = languages
        self.theme = config["theme"]
        self.galaxy_arms = config.get("galaxy_arms", [])
        self.projects = config.get("projects", [])
        self.locale = normalize_locale(locale or config.get("locale", DEFAULT_LOCALE))

    # ── Localization helpers ──

    def strings(self) -> dict:
        """Built-in string table for this locale, with config.i18n overrides."""
        table = dict(get_strings(self.locale))
        overrides = self.config.get("i18n", {}).get(self.locale, {})
        for key, value in overrides.items():
            if isinstance(value, (str, int, float)):
                table[key] = value
        table["_fonts"] = get_fonts(self.locale)
        table["_tracking"] = get_title_tracking(self.locale)
        return table

    def localized_arms(self) -> list:
        """Galaxy arms with names/items localized for this locale."""
        overrides = self.config.get("i18n", {}).get(self.locale, {})
        names = overrides.get("galaxy_arms") or []
        arms = []
        for i, arm in enumerate(self.galaxy_arms):
            arm = dict(arm)
            if i < len(names) and names[i]:
                arm["name"] = names[i]
            arms.append(arm)
        return arms

    def localized_projects(self) -> list:
        """Projects with descriptions localized for this locale."""
        overrides = self.config.get("i18n", {}).get(self.locale, {})
        texts = overrides.get("projects") or []
        projects = []
        for i, proj in enumerate(self.projects):
            proj = dict(proj)
            if i < len(texts) and texts[i]:
                proj["description"] = texts[i]
            projects.append(proj)
        return projects

    def localized_config(self) -> dict:
        """Config with profile text, arms and projects resolved for this locale.

        Precedence per field: profile.locales[locale][field] > profile[field].
        The name falls back to i18n[locale][name] before the default profile name.
        """
        config = dict(self.config)
        profile = dict(self.config.get("profile", {}))

        overrides = self.config.get("i18n", {}).get(self.locale, {})
        for field in PROFILE_TEXT_FIELDS:
            if overrides.get(field):
                profile[field] = overrides[field]

        profile.update(self.config.get("profile", {}).get("locales", {}).get(self.locale, {}))

        config["profile"] = profile
        config["username"] = profile.get("name", config.get("username", "user"))
        return config

    # ── Renderers ──

    def render_galaxy_header(self) -> str:
        return galaxy_header.render(
            config=self.localized_config(),
            theme=self.theme,
            galaxy_arms=self.localized_arms(),
            projects=self.localized_projects(),
            strings=self.strings(),
        )

    def render_stats_card(self) -> str:
        metrics = self.config["stats"]["metrics"]
        return stats_card.render(
            stats=self.stats,
            metrics=metrics,
            theme=self.theme,
            strings=self.strings(),
        )

    def render_tech_stack(self) -> str:
        lang_config = self.config.get("languages", {})
        return tech_stack.render(
            languages=self.languages,
            galaxy_arms=self.localized_arms(),
            theme=self.theme,
            exclude=lang_config.get("exclude", []),
            max_display=lang_config.get("max_display", 8),
            strings=self.strings(),
        )

    def render_projects_constellation(self) -> str:
        return projects_constellation.render(
            projects=self.localized_projects(),
            galaxy_arms=self.localized_arms(),
            theme=self.theme,
            strings=self.strings(),
        )

    def render_all(self) -> dict:
        """Render every SVG asset, keyed by filename."""
        return {
            "galaxy-header.svg": self.render_galaxy_header(),
            "stats-card.svg": self.render_stats_card(),
            "tech-stack.svg": self.render_tech_stack(),
            "projects-constellation.svg": self.render_projects_constellation(),
        }
