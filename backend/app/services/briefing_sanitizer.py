"""LLM 출력에서 본문 URL과 출처 없는 근거를 제거하는 최종 안전망."""

from __future__ import annotations

import re

from app.schemas.llm import BriefingRender, MarketOverviewRender
from app.services.llm.output_validation import validate_one_line_summary

MARKDOWN_LINK = re.compile(r"\[([^\]]+)]\(https?://[^\s)]+\)", re.IGNORECASE)
RAW_URL = re.compile(r"https?://\S+", re.IGNORECASE)


def _clean_text(value: str) -> str:
    value = MARKDOWN_LINK.sub(r"\1", value)
    value = RAW_URL.sub("", value)
    return re.sub(r"\s+", " ", value).strip(" -–—·,;:")


def _clean_common(render) -> None:
    render.summary = _clean_text(render.summary)
    if hasattr(render, "one_line_summary"):
        render.one_line_summary = validate_one_line_summary(_clean_text(render.one_line_summary))
    render.positive_factors = [text for item in render.positive_factors if (text := _clean_text(item))]
    render.negative_factors = [text for item in render.negative_factors if (text := _clean_text(item))]
    render.watch_issues = [text for item in render.watch_issues if (text := _clean_text(item))]
    render.today_actions = [text for item in render.today_actions if (text := _clean_text(item))]
    render.disclaimer = _clean_text(render.disclaimer)

    cleaned_reasons = []
    for reason in render.reasons:
        source_url = (reason.source_url or "").strip()
        if not source_url.lower().startswith(("http://", "https://")):
            continue
        reason.factor = _clean_text(reason.factor) or "관련 근거"
        reason.explain = _clean_text(reason.explain)
        reason.source_url = source_url
        cleaned_reasons.append(reason)
    render.reasons = cleaned_reasons


def sanitize_briefing_render(render: BriefingRender) -> BriefingRender:
    cleaned = render.model_copy(deep=True)
    _clean_common(cleaned)
    return cleaned


def sanitize_market_overview_render(render: MarketOverviewRender) -> MarketOverviewRender:
    cleaned = render.model_copy(deep=True)
    _clean_common(cleaned)
    for item in cleaned.indices:
        item.name = _clean_text(item.name)
        item.description = _clean_text(item.description)
    for item in cleaned.sector_moves:
        item.name = _clean_text(item.name)
        item.description = _clean_text(item.description)
    return cleaned
