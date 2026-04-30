"""Deterministic hexagram generator from (date, time, address)."""
import hashlib
from .hexagrams import HEXAGRAMS, hexagram_tone


def generate_hexagram(date_str: str, time_str: str, address: str):
    """Same input always produces the same hexagram."""
    seed = f"{date_str}|{time_str}|{address.lower().strip()}"
    h = hashlib.sha256(seed.encode()).hexdigest()

    # 6 lines from first 6 hex chars (0=yin, 1=yang)
    lines = [int(h[i], 16) % 2 for i in range(6)]
    # Changing lines from next 6 chars
    changing = [i + 1 for i in range(6) if int(h[i + 6], 16) % 7 == 0]

    # Hexagram number 1–64
    bin_str = "".join(str(b) for b in reversed(lines))
    hex_num = (int(bin_str, 2) % 64) + 1

    name, title, theme = HEXAGRAMS[hex_num]
    tone = hexagram_tone(hex_num)

    return {
        "number": hex_num,
        "name": name,
        "title": title,
        "theme": theme,
        "lines": lines,
        "changing": changing,
        "tone": tone,
        "ascii": render_ascii(lines, changing),
    }


"""Deterministic hexagram generator from (date, time, address)."""
import hashlib
from .hexagrams import HEXAGRAMS, hexagram_tone


def generate_hexagram(date_str: str, time_str: str, address: str):
    """Same input always produces the same hexagram."""
    seed = f"{date_str}|{time_str}|{address.lower().strip()}"
    h = hashlib.sha256(seed.encode()).hexdigest()

    # 6 lines from first 6 hex chars (0=yin, 1=yang)
    # Lines are stored bottom-up: lines[0] is the bottom line
    lines = [int(h[i], 16) % 2 for i in range(6)]

    # Changing lines from next 6 chars
    changing = [i + 1 for i in range(6) if int(h[i + 6], 16) % 7 == 0]

    # Hexagram number 1–64 (King Wen sequence requires lookup,
    # but we use binary representation for deterministic mapping)
    bin_str = "".join(str(b) for b in reversed(lines))
    hex_num = (int(bin_str, 2) % 64) + 1

    name, title, theme = HEXAGRAMS[hex_num]
    tone = hexagram_tone(hex_num)

    return {
        "number": hex_num,
        "name": name,
        "title": title,
        "theme": theme,
        "lines": lines,
        "changing": changing,
        "tone": tone,
        "ascii": render_hexagram(lines, changing),
        "unicode": render_unicode(lines, changing),
    }


def render_hexagram(lines, changing):
    """
    Render hexagram with HTML-safe characters.
    Lines are bottom-up: lines[0] = bottom.
    Display is top-down (line 6 at top).
    """
    rows = []
    for i in range(5, -1, -1):
        line_num = i + 1
        marker = "  ⊗" if line_num in changing else ""
        if lines[i] == 1:
            rows.append(f"━━━━━━━━━━━━━━━━━━━━━━{marker}")  # yang (solid)
        else:
            rows.append(f"━━━━━━━━    ━━━━━━━━{marker}")  # yin (broken with gap)
    return "\n".join(rows)


def render_unicode(lines, changing):
    """
    Render using proper trigram unicode characters for visual clarity.
    Returns a dict with both lines representation and unicode hexagram char.
    """
    # Build line-by-line with unicode block chars
    rows = []
    for i in range(5, -1, -1):
        line_num = i + 1
        marker = " ●" if line_num in changing else ""
        if lines[i] == 1:
            rows.append(f"▬▬▬▬▬▬▬▬▬{marker}")
        else:
            rows.append(f"▬▬▬▬   ▬▬▬▬{marker}")
    return "\n".join(rows)


def resonance(empirical_score: int, tone: str) -> str:
    """Does the symbolic layer 'agree' with empirical risk?"""
    if empirical_score >= 65 and tone == "danger":
        return "HIGH"
    if empirical_score < 35 and tone == "harmony":
        return "HIGH"
    if 35 <= empirical_score < 65 and tone == "neutral":
        return "HIGH"
    return "LOW"


def resonance(empirical_score: int, tone: str) -> str:
    """Does the symbolic layer 'agree' with empirical risk?"""
    if empirical_score >= 65 and tone == "danger":
        return "HIGH"
    if empirical_score < 35 and tone == "harmony":
        return "HIGH"
    if 35 <= empirical_score < 65 and tone == "neutral":
        return "HIGH"
    return "LOW"
