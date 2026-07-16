"""Minimal robots.txt evaluator for source due-diligence (pure, unit-tested).

Not a full RFC 9309 implementation — a pragmatic subset sufficient to answer "may we fetch this
path?": it reads the rules for the matching User-agent (falling back to `*`), and treats a path
as disallowed if it matches a Disallow prefix with no longer Allow prefix. `Disallow: /` blocks
everything; an empty Disallow allows everything. `*` and `$` wildcards in patterns are handled
by simple prefix logic (the common case for the gazette/regulator sites we track).
"""
from __future__ import annotations


def _rules_for(robots_text: str, user_agent: str) -> tuple[list[str], list[str]]:
    """(disallow_prefixes, allow_prefixes) for the given UA, falling back to the '*' group.
    Consecutive User-agent lines share the following rule block (standard robots grouping)."""
    groups: dict[str, dict[str, list[str]]] = {}
    current_uas: list[str] = []
    last_was_ua = False
    for raw in robots_text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, value = (p.strip() for p in line.split(":", 1))
        field = field.lower()
        if field == "user-agent":
            if not last_was_ua:
                current_uas = []
            ua = value.lower()
            current_uas.append(ua)
            groups.setdefault(ua, {"disallow": [], "allow": []})
            last_was_ua = True
        elif field in ("disallow", "allow") and current_uas:
            for ua in current_uas:
                groups[ua][field].append(value)
            last_was_ua = False
    ua = user_agent.lower()
    chosen = groups.get(ua) or groups.get("*") or {"disallow": [], "allow": []}
    return chosen["disallow"], chosen["allow"]


def path_allowed(robots_text: str, path: str, user_agent: str = "*") -> bool:
    disallow, allow = _rules_for(robots_text, user_agent)
    # An empty Disallow value ("Disallow:") means allow-all for that group.
    disallow = [d for d in disallow if d != ""]
    if not disallow:
        return True

    def _match_len(prefixes: list[str]) -> int:
        best = -1
        for pref in prefixes:
            stem = pref.rstrip("*$")
            if stem == "" and pref not in ("", None):  # "Disallow: /" or bare wildcard
                stem = "/"
            if path.startswith(stem):
                best = max(best, len(stem))
        return best

    dis = _match_len(disallow)
    if dis < 0:
        return True
    alw = _match_len(allow)
    return alw >= dis  # a same-or-longer Allow prefix wins
