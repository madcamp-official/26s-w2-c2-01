package com.madcamp26s.tradechaser

import org.json.JSONArray
import org.json.JSONObject

data class LensRecommendation(
    val cats: Set<String>,
    val preset: String,
    val why: String,
)

data class LensRecommendationPair(
    val primary: LensRecommendation,
    val alt: LensRecommendation,
)

object LensRules {
    private val rules = mapOf(
        "SEMI" to LensRecommendationPair(
            LensRecommendation(setOf("SOX", "US10Y", "SEMI"), "VALUE", "반도체·AI 종목은 금리에 민감한 성장주 성격이 강해 미 국채 10년물과 반도체 지수(SOX)를 함께 보는 것이 중요하고, 업황 사이클이 길어 장기 가치투자 관점이 잘 맞습니다."),
            LensRecommendation(setOf("SOX", "SEMI"), "MOMENTUM", "반도체는 실적 서프라이즈와 수급에 따라 단기 변동성이 크기 때문에, 촉매 이벤트를 빠르게 포착하는 모멘텀 관점도 유효합니다."),
        ),
        "TECH" to LensRecommendationPair(
            LensRecommendation(setOf("IXIC", "US10Y", "TECH"), "MACRO", "테크·소프트웨어 종목은 나스닥 지수와 동조화가 강하고 금리 변화에 밸류에이션이 민감해, 거시 지표를 함께 보는 냉정한 시각이 유리합니다."),
            LensRecommendation(setOf("IXIC", "TECH"), "FACT", "해석보다 실적·발표 사실 자체를 빠르게 확인하고 싶다면 팩트 브리핑이 더 적합합니다."),
        ),
        "MEDIA" to LensRecommendationPair(
            LensRecommendation(setOf("IXIC", "MEDIA", "EARNINGS"), "FACT", "미디어·인터넷 종목은 광고 매출·이용자 지표 등 실적 발표에 따른 변동이 커 사실 위주로 확인하는 것이 유용합니다."),
            LensRecommendation(setOf("IXIC", "MEDIA"), "MACRO", "나스닥 지수와 동조화되고 금리에 밸류에이션이 민감한 성장주 성격도 있어 거시 관점도 함께 참고할 만합니다."),
        ),
        "AUTO" to LensRecommendationPair(
            LensRecommendation(setOf("RUT", "FFR", "AUTO"), "MOMENTUM", "자동차 섹터는 인도량·정책 변화에 따른 단기 변동성이 크고 중소형주 지수(러셀2000)·금리 흐름의 영향을 함께 받아 모멘텀 관점이 유효합니다."),
            LensRecommendation(setOf("AUTO"), "BEGINNER", "산업 배경 지식이 아직 낯설다면 용어를 풀어 설명하는 입문자용 렌즈로 먼저 감을 잡는 것을 추천합니다."),
        ),
        "INDUST" to LensRecommendationPair(
            LensRecommendation(setOf("PMI", "GDP", "INDUST"), "MACRO", "산업재는 경기 사이클과 제조업 지표(PMI)에 밀접하게 연동돼 거시 흐름을 함께 보는 것이 중요합니다."),
            LensRecommendation(setOf("INDUST"), "VALUE", "경기 순환에도 불구하고 장기적으로는 펀더멘털에 수렴하는 경향이 있어 가치투자 관점도 유효합니다."),
        ),
        "TELECOM" to LensRecommendationPair(
            LensRecommendation(setOf("TELECOM", "DIVIDEND"), "VALUE", "통신주는 안정적인 현금흐름과 배당 매력이 있어 장기 가치투자 관점이 잘 맞습니다."),
            LensRecommendation(setOf("TELECOM"), "FACT", "설비투자·요금제 변화 등 사실 자체를 빠르게 확인하고 싶다면 팩트 브리핑이 적합합니다."),
        ),
        "REALESTATE" to LensRecommendationPair(
            LensRecommendation(setOf("US10Y", "REALESTATE"), "MACRO", "부동산(리츠 등)은 금리 변화에 밸류에이션이 직접적으로 반응해 거시 지표 위주로 보는 것이 효과적입니다."),
            LensRecommendation(setOf("REALESTATE", "DIVIDEND"), "VALUE", "배당 매력이 있는 부동산 종목이라면 장기 가치투자 관점으로 접근하는 것도 유효합니다."),
        ),
        "MATERIALS" to LensRecommendationPair(
            LensRecommendation(setOf("MATERIALS", "GEOPOL"), "MACRO", "소재 섹터는 원자재 가격과 지정학 이슈에 크게 좌우되어 거시 흐름을 함께 보는 것이 중요합니다."),
            LensRecommendation(setOf("MATERIALS"), "FACT", "원자재 가격·생산량 등 사실 위주로 빠르게 확인하고 싶다면 팩트 브리핑이 적합합니다."),
        ),
        "UTIL" to LensRecommendationPair(
            LensRecommendation(setOf("UTIL", "US10Y"), "VALUE", "유틸리티는 안정적인 현금흐름과 배당이 특징이지만 금리에 밸류에이션이 민감해 장기 가치투자 관점이 유효합니다."),
            LensRecommendation(setOf("UTIL", "DIVIDEND"), "MACRO", "금리 흐름에 따른 밸류에이션 변화를 함께 보고 싶다면 거시 분석 관점도 참고할 만합니다."),
        ),
        "FIN" to LensRecommendationPair(
            LensRecommendation(setOf("FFR", "US10Y", "FIN"), "MACRO", "금융주는 기준금리·장단기 금리차의 영향을 직접적으로 받아 거시 지표 위주로 보는 것이 효과적입니다."),
            LensRecommendation(setOf("FIN", "EARNINGS"), "FACT", "분기 실적 발표에 따른 변동이 커 사실 위주로 확인하고 싶다면 팩트 브리핑이 적합합니다."),
        ),
        "HEALTH" to LensRecommendationPair(
            LensRecommendation(setOf("HEALTH", "EARNINGS"), "VALUE", "헬스케어는 임상·승인 이슈로 변동이 있지만 장기적으로는 펀더멘털에 수렴하는 경향이 있어 가치투자 관점이 유효합니다."),
            LensRecommendation(setOf("HEALTH"), "BEGINNER", "의학·규제 용어가 낯설다면 입문자용 렌즈로 배경부터 이해하는 것을 추천합니다."),
        ),
        "ENERGY" to LensRecommendationPair(
            LensRecommendation(setOf("ENERGY", "GEOPOL"), "MACRO", "에너지 섹터는 지정학 이슈와 원자재 가격에 크게 좌우되어 거시 흐름을 함께 보는 것이 중요합니다."),
            LensRecommendation(setOf("ENERGY", "DIVIDEND"), "VALUE", "배당 매력이 있는 에너지주라면 장기 가치투자 관점으로 접근하는 것도 유효합니다."),
        ),
        "CONSUMER" to LensRecommendationPair(
            LensRecommendation(setOf("CONSUMER", "CPI"), "FACT", "소비재는 물가·소비 지표와 직결되어 사실 위주로 빠르게 확인하는 것이 유용합니다."),
            LensRecommendation(setOf("CONSUMER"), "BEGINNER", "소비재 산업이 처음이라면 입문자용 렌즈로 배경부터 살펴보는 것을 추천합니다."),
        ),
    )

    private val default = LensRecommendationPair(
        LensRecommendation(setOf("IXIC", "US10Y"), "FACT", "특정 섹터로 분류되지 않은 종목은 전체 시장 지수와 금리 흐름을 사실 위주로 참고하는 것이 무난합니다."),
        LensRecommendation(setOf("IXIC"), "BEGINNER", "생소한 종목이라면 입문자용 설명으로 배경부터 이해하는 것을 추천합니다."),
    )

    fun forSectorCode(code: String?) = rules[code] ?: default

    fun defaultLens(code: String?): LensSetting {
        val rec = forSectorCode(code).primary
        return LensSetting(rec.cats, rec.preset, "standard", "", "primary")
    }

    fun blank(note: String = "") = LensSetting(emptySet(), null, null, note, null)

    fun sectorCodeByName(name: String): String? = when {
        name.contains("반도체", true) || name.contains("semiconductor", true) -> "SEMI"
        name.contains("테크", true) || name.contains("소프트웨어", true) || name.contains("technology", true) -> "TECH"
        name.contains("미디어", true) || name.contains("인터넷", true) || name.contains("communication", true) -> "MEDIA"
        name.contains("소비", true) || name.contains("consumer", true) -> "CONSUMER"
        name.contains("자동차", true) || name.contains("auto", true) -> "AUTO"
        name.contains("금융", true) || name.contains("financial", true) -> "FIN"
        name.contains("헬스", true) || name.contains("health", true) -> "HEALTH"
        name.contains("에너지", true) || name.contains("energy", true) -> "ENERGY"
        name.contains("산업", true) || name.contains("industrial", true) -> "INDUST"
        name.contains("통신", true) || name.contains("telecom", true) -> "TELECOM"
        name.contains("부동산", true) || name.contains("real estate", true) || name.contains("reit", true) -> "REALESTATE"
        name.contains("소재", true) || name.contains("materials", true) -> "MATERIALS"
        name.contains("유틸", true) || name.contains("utility", true) || name.contains("utilities", true) -> "UTIL"
        else -> null
    }
}

fun LensSetting.toJsonString(): String = JSONObject()
    .put("categories", JSONArray(categoryCodes.toList()))
    .put("preset", presetCode)
    .put("depth", depth)
    .put("note", note)
    .put("whyKey", whyKey)
    .toString()

fun lensSettingFromJson(raw: String?, fallback: LensSetting): LensSetting {
    if (raw.isNullOrBlank()) return fallback
    return runCatching {
        val json = JSONObject(raw)
        LensSetting(
            categoryCodes = json.optJSONArray("categories").strings().toSet(),
            presetCode = json.optString("preset").takeIf { it.isNotBlank() && it != "null" },
            depth = json.optString("depth").takeIf { it.isNotBlank() && it != "null" },
            note = json.optString("note"),
            whyKey = json.optString("whyKey").takeIf { it.isNotBlank() && it != "null" },
        )
    }.getOrDefault(fallback)
}
