import re

korean_pattern_str = "가-힣"
number_pattern_str = "0-9"
alphabet_pattern_str = "a-zA-Z"
puntuation_pattern_str = ".,?!"

doublespace_pattern = re.compile(r"\s+")
repeatchars_pattern = re.compile(r"(\w)\\1{3,}")


def normalize(
    doc: str,
    english: bool = False,
    number: bool = False,
    punctuation: bool = False,
    remove_repeat: int = 0,
    remains: str | None = None,
    pattern: re.Pattern[str] | None = None,
) -> str:
    """Normalize a Korean text string by removing unwanted characters.

    Keeps Korean characters (가-힣) by default. Additional character classes can
    be retained via the boolean flags or a custom *remains* string.

    Args:
        doc: Input string to be normalized.
        english: If True, keeps ASCII alphabet characters.
        number: If True, keeps digit characters (0-9).
        punctuation: If True, keeps ``.,?!`` punctuation marks.
        remove_repeat: If positive, shortens runs of the same character to this
            length (e.g. ``ㅋㅋㅋㅋ`` → ``ㅋㅋ`` when *remove_repeat* is 2).
        remains: Additional characters to keep, given as a regex character-class
            fragment (e.g. ``"#@"``).
        pattern: Pre-compiled regex pattern used for normalization. When
            provided, the boolean flags and *remains* are ignored.

    Returns:
        Normalized string with consecutive whitespace collapsed to a single
        space and leading/trailing whitespace stripped.

    Example:
        >>> normalize("한글과 alphabet 으로 이뤄진 20글자에 가까운..   문장이에요")
        '한글과  으로 이뤄진 글자에 가까운 문장이에요'
        >>> normalize("한글과 alphabet 으로 이뤄진 20글자에 가까운..   문장이에요", english=True)
        '한글과 alphabet 으로 이뤄진 글자에 가까운 문장이에요'
    """
    if not isinstance(pattern, re.Pattern):
        pattern = initialize_pattern(english, number, punctuation, remains)

    if remove_repeat > 0:
        doc = repeatchars_pattern.sub("\\1" * remove_repeat, doc)

    doc = pattern.sub(" ", doc)
    return doublespace_pattern.sub(" ", doc).strip()


def initialize_pattern(
    english: bool = False,
    number: bool = False,
    punctuation: bool = False,
    remains: str | None = None,
) -> re.Pattern[str]:
    """Build a compiled regex pattern that matches characters to be removed.

    The pattern matches any character *not* in the allowed set, so it can be
    used directly with ``re.Pattern.sub`` to strip unwanted characters.

    Args:
        english: If True, allows ASCII alphabet characters.
        number: If True, allows digit characters (0-9).
        punctuation: If True, allows ``.,?!`` punctuation marks.
        remains: Additional characters to allow, given as a regex
            character-class fragment (e.g. ``"#@"``).

    Returns:
        Compiled regex pattern ``re.compile(r'[^<allowed_chars>]')``.

    Example:
        >>> initialize_pattern(english=True)
        re.compile('[^가-힣a-zA-Z]')
    """
    pattern = korean_pattern_str
    if english:
        pattern += alphabet_pattern_str
    if number:
        pattern += number_pattern_str
    if punctuation:
        pattern += puntuation_pattern_str
    if isinstance(remains, str):
        pattern += remains
    return re.compile(r"[^%s]" % pattern)
