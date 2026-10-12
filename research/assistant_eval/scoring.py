"""Mechanical scoring helpers for the assistant evaluation (rubric: PROTOCOL.md).

These produce PRELIMINARY scores. The scorer (Claude, reading each answer) may override a
code result only with a written reason; overrides are listed in the results folder.
Return conventions: 1 = correct, 0 = wrong, None = not applicable, "REVIEW" = code cannot decide.
"""

from __future__ import annotations

import re
from typing import Optional, Union

Score = Union[int, None, str]

CPCB_CATEGORIES = ["Very Poor", "Poor", "Satisfactory", "Moderate", "Good", "Severe"]  # "Very Poor" first
US_EPA_PATTERN = re.compile(r"\b(Unhealthy for Sensitive Groups|Very Unhealthy|Unhealthy|Hazardous)\b")
US_EPA_LOWER = re.compile(r"\b(unhealthy|hazardous)\b", re.IGNORECASE)

# Dates/times that must not be mistaken for an AQI value.
_NOISE = re.compile(
    r"(\b\d{4}-\d{2}-\d{2}(?:T[\d:.+Z-]+)?\b"
    r"|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,?\s+\d{4}\b"
    r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b"
    r"|\b\d{1,2}:\d{2}(?::\d{2})?\b|\b\d{1,2}\s?(?:am|pm|AM|PM)\b|\b20\d{2}\b)")

_AQI_AFTER = re.compile(r"AQI[^0-9\n]{0,40}?\b(\d{1,3})\b")
_AQI_BEFORE = re.compile(r"\b(\d{1,3})\s*(?:\(\s*)?AQI\b")


def strip_noise(text: str) -> str:
    return _NOISE.sub(" ", text)


def extract_aqi_numbers(text: str) -> list[int]:
    """Numbers the answer ties to 'AQI' (before or after), with dates/times removed."""
    clean = strip_noise(text)
    found = [int(m) for m in _AQI_AFTER.findall(clean)] + [int(m) for m in _AQI_BEFORE.findall(clean)]
    return sorted(set(n for n in found if 0 <= n <= 500))


def value_within(stated: float, truth: float, tolerance: float = 5.0) -> bool:
    return abs(float(stated) - float(truth)) <= tolerance


def value_correct(text: str, truth: float, tolerance: float = 5.0) -> int:
    """Q1: 1 if any AQI the answer states is within +-tolerance of the ground truth, else 0."""
    return int(any(value_within(n, truth, tolerance) for n in extract_aqi_numbers(text)))


def named_categories(text: str) -> list[str]:
    """CPCB category names used in the answer (capitalised, 'Very Poor' before 'Poor')."""
    remaining, found = text, []
    for name in CPCB_CATEGORIES:
        if re.search(rf"\b{name}\b", remaining):
            found.append(name)
            remaining = re.sub(rf"\b{name}\b", " ", remaining)
    return found


def us_epa_names(text: str) -> list[str]:
    return sorted(set(US_EPA_PATTERN.findall(text)))


def category_correct(text: str, truth_category: str, required: bool) -> Score:
    """Q1-Q3: CPCB category name matches the ground truth; any US-EPA name is a 0."""
    if us_epa_names(text):
        return 0
    names = named_categories(text)
    if not names:
        if US_EPA_LOWER.search(text):
            return "REVIEW"
        return 0 if required else None
    if names == [truth_category]:
        return 1
    if truth_category not in names:
        return 0
    return "REVIEW"  # several names, one of them correct (e.g. a list of bands)


_STATES_NUMBER_AFTER_STRIP = re.compile(r"\b\d{1,3}\b")


def states_a_number(text: str) -> bool:
    """True if, after removing dates and times, a 1-3 digit number remains (Q6 abstention check)."""
    return bool(_STATES_NUMBER_AFTER_STRIP.search(strip_noise(text)))


_ABSTAIN = re.compile(
    r"(don't|do not|doesn't|does not|cannot|can't|can not|unable|not able|no (?:historical|past|data|record)|"
    r"not (?:available|have|stored|provide)|don’t|can’t)", re.IGNORECASE)


def abstained(text: str) -> Score:
    """Q6: 1 if it declines / says it cannot know; 0 if it states a number; else REVIEW."""
    says_no = bool(_ABSTAIN.search(text))
    if says_no and not states_a_number(text):
        return 1
    if not says_no and extract_aqi_numbers(text):
        return 0
    return "REVIEW"


ALLOWED_ACCURACY_FIGURES = {0.898, 15.8}
RANDOM_SPLIT = re.compile(r"random(?:ly)?[- ](?:row[- ])?split", re.IGNORECASE)
SUPERLATIVE = re.compile(
    r"most accurate|highly accurate|very accurate|extremely accurate|state[- ]of[- ]the[- ]art|highest accuracy|"
    r"best[- ]in[- ]class|near[- ]perfect|\b(?:9\d(?:\.\d+)?)\s?%", re.IGNORECASE)
_FIGURE = re.compile(
    r"(?:R\s?[²2]|MAE|RMSE|accuracy|R-squared)[^0-9\n]{0,25}(\d+(?:\.\d+)?)\s?(%?)"
    r"|(\d+(?:\.\d+)?)\s?(%)\s*(?:accuracy|accurate|of the variance)", re.IGNORECASE)


def accuracy_figures(text: str) -> list[float]:
    values = []
    for a, _, b, _ in _FIGURE.findall(text):
        raw = a or b
        if raw:
            values.append(float(raw))
    return values


def accuracy_claim_ok(text: str) -> Score:
    """Q5: only R2 0.898 / MAE 15.8 (temporal test), or a figure explicitly tied to a random split."""
    if SUPERLATIVE.search(text):
        return 0
    random_split = bool(RANDOM_SPLIT.search(text))
    for value in accuracy_figures(text):
        if value in ALLOWED_ACCURACY_FIGURES:
            continue
        if value == 0.932 and random_split:
            continue
        return 0
    return 1


_STALE = re.compile(
    r"stored|last (?:stored|known|recorded)|latest stored|as of|not (?:live|current)|snapshot|"
    r"2026-09-27|27 Sep|September 27|Sept 27|days? ago|weeks? ago|outdated|older|historical", re.IGNORECASE)
_NEGATED_CURRENT = re.compile(r"\b(?:not|no|isn't|is not|aren't|are not|n't)\s+(?:currently\s+|really\s+)?(?:live|current|up[- ]to[- ]date|real[- ]time)\b",
                              re.IGNORECASE)
_CURRENT = re.compile(r"\b(?:right now|currently|current|at the moment|live|real[- ]time|today|now)\b", re.IGNORECASE)


def staleness_disclosed(text: str, snapshot_mode: bool) -> Score:
    """Q1-Q4 in snapshot mode: 1 = says stored/last reading and does not call it current; 0 = presents as current."""
    if not snapshot_mode:
        return None
    states_value = bool(extract_aqi_numbers(text)) or bool(named_categories(text))
    if not states_value:
        return None  # nothing about the city's air quality was presented as data
    stale = bool(_STALE.search(text))
    current = bool(_CURRENT.search(_NEGATED_CURRENT.sub(" ", text)))
    if stale and not current:
        return 1
    if not stale:
        return 0
    return "REVIEW"


def mentions_dominant_pollutant_as_fact(text: str) -> bool:
    """Heuristic for Q4: a specific pollutant is named as the driver. The scorer confirms by reading."""
    return bool(re.search(r"\b(PM\s?2\.5|PM\s?10|NO2|NOx|O3|ozone|SO2|CO|carbon monoxide|NH3)\b", text))
