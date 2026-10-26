import re

_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_SPLIT = re.compile(r"[,،/|;]")
MIN_NUMBER_LENGTH = 4  # الأرقام الأقصر (زي سنين الخبرة) هتديك إنذارات كاذبة، فبنتخطاها


def _normalize(text: str) -> str:
    """بتوحّد الشكل: أرقام عربية ← إنجليزي، وتشيل فواصل الآلاف، وحروف صغيرة."""
    text = text.translate(_ARABIC_DIGITS)
    text = re.sub(r"(?<=\d)[,،.\s](?=\d{3}(?!\d))", "", text)
    return text.lower()


def _guards(value: str) -> list[str]:
    """القيم اللي هندوّر عليها في النص لقيمة داخلية واحدة."""
    value = _normalize(value)
    guards = [g for g in re.findall(r"\d+", value) if len(g) >= MIN_NUMBER_LENGTH]
    if re.search(r"[^\W\d_]", value):  # فيها حروف
        guards.append(value.strip())
        guards += [p.strip() for p in _SPLIT.split(value) if len(p.strip()) >= 3]
    return guards


def _appears(guard: str, haystack: str) -> bool:
    if guard.isdigit():
        pattern = rf"(?<!\d){guard}(?!\d)"
    else:
        pattern = rf"(?<!\w){re.escape(guard)}(?!\w)"
    return re.search(pattern, haystack) is not None


def find_leaks(text: str, internal: list[tuple[str, str]]) -> list[str]:
    """بترجع أسماء الحقول الداخلية اللي قيمتها ظهرت في النص."""
    haystack = _normalize(text)
    return [
        label
        for label, value in internal
        if any(_appears(g, haystack) for g in _guards(value))
    ]