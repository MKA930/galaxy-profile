"""Locale strings for the generated SVGs.

Every user-visible label that is not taken from config.yml lives here.
Add a new language by adding a dict to LOCALES — keys must stay in sync
with the English entry, otherwise the fallback kicks in.
"""

DEFAULT_LOCALE = "en"
LOCALES = ("en", "zh")

# Font stacks per locale. CJK text needs a CJK-capable family, otherwise
# browsers fall back to whatever the platform has and metrics drift.
FONT_STACKS = {
    "en": {
        "sans": "sans-serif",
        "mono": "monospace",
    },
    "zh": {
        "sans": "'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', "
                "'Noto Sans SC', 'Source Han Sans SC', sans-serif",
        "mono": "'JetBrains Mono', 'SFMono-Regular', 'Cascadia Mono', "
                "'Microsoft YaHei Mono', 'Noto Sans Mono CJK SC', monospace",
    },
}

# Width per character, in em units, used to estimate rendered text width.
# CJK glyphs are full-width (~1.0em), ASCII averages ~0.55em in sans/mono.
CHAR_WIDTH_EM = {
    "ascii": 0.55,
    "wide": 1.0,
}

STRINGS = {
    "en": {
        # stats card
        "stats_title": "MISSION TELEMETRY",
        "metric_commits": "Commits",
        "metric_stars": "Stars",
        "metric_prs": "PRs",
        "metric_issues": "Issues",
        "metric_repos": "Repos",
        # tech stack card
        "lang_title": "LANGUAGE TELEMETRY",
        "sectors_title": "FOCUS SECTORS",
        "items_count": "({n})",
        # projects card
        "projects_title": "FEATURED SYSTEMS",
        "systems_online": "SYS {n}/{n} ONLINE",
        "no_projects": "No featured projects configured",
    },
    "zh": {
        # stats card
        "stats_title": "使命遥测",
        "metric_commits": "提交",
        "metric_stars": "星标",
        "metric_prs": "合并请求",
        "metric_issues": "议题",
        "metric_repos": "仓库",
        # tech stack card
        "lang_title": "语言遥测",
        "sectors_title": "专注领域",
        "items_count": "({n} 项)",
        # projects card
        "projects_title": "核心系统",
        "systems_online": "系统 {n}/{n} 在线",
        "no_projects": "尚未配置精选项目",
    },
}

# `letter-spacing` values that look right for tracked-out section headers.
# CJK glyphs already read as spaced, so they get less extra tracking.
TITLE_TRACKING = {
    "en": 3,
    "zh": 2,
}


def normalize_locale(value) -> str:
    """Coerce an arbitrary string to a supported locale code."""
    if not isinstance(value, str):
        return DEFAULT_LOCALE
    code = value.strip().lower().replace("_", "-").split("-")[0]
    return code if code in LOCALES else DEFAULT_LOCALE


def get_strings(locale: str) -> dict:
    """Return the string table for a locale, falling back to English."""
    return STRINGS.get(normalize_locale(locale), STRINGS[DEFAULT_LOCALE])


def get_fonts(locale: str) -> dict:
    """Return the font stacks for a locale."""
    return FONT_STACKS.get(normalize_locale(locale), FONT_STACKS[DEFAULT_LOCALE])


def get_title_tracking(locale: str) -> int:
    """Return the letter-spacing for section titles in a locale."""
    return TITLE_TRACKING.get(normalize_locale(locale), TITLE_TRACKING[DEFAULT_LOCALE])
