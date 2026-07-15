package com.madcamp26s.tradechaser

import org.json.JSONArray
import org.json.JSONObject

data class AuthSession(val accessToken: String, val user: AppUser)

data class AppUser(
    val id: Int,
    val email: String,
    val nickname: String,
    val investorType: String,
)

data class BriefingData(
    val briefingDate: String,
    val sessions: List<BriefingSession>,
    val marketOverview: MarketOverview?,
    val marketOverviews: List<MarketOverview>,
    val stocks: List<StockBriefing>,
    val missingTickers: List<String>,
    val watchlist: List<WatchlistItem>,
    val allStocks: List<StockItem>,
    val sectors: List<SectorItem>,
    val sectorWatchlist: List<SectorWatchlistItem>,
    val sectorBriefings: List<SectorBriefing>,
    val missingSectors: List<Int>,
)

data class BriefingSession(
    val key: String,
    val label: String,
    val available: Boolean,
    val scheduledAt: String,
)

data class SectorItem(val id: Int, val nameKo: String, val nameEn: String)

data class StockItem(
    val ticker: String,
    val nameKo: String,
    val nameEn: String,
    val exchange: String,
    val sectorId: Int?,
    val sector: SectorItem?,
) {
    val displayName: String get() = nameKo.ifBlank { nameEn }
    val sectorName: String get() = sector?.nameKo.orEmpty()
}

data class WatchlistItem(
    val id: Int,
    val ticker: String,
    val stock: StockItem?,
    val createdAt: String,
) {
    val name: String get() = stock?.displayName.orEmpty()
    val sectorName: String get() = stock?.sectorName.orEmpty()
}

data class SectorWatchlistItem(
    val id: Int,
    val sectorId: Int,
    val sector: SectorItem?,
    val createdAt: String,
)

data class FactorReason(
    val factor: String,
    val explain: String,
    val sourceUrl: String,
) {
    val displayText: String get() = factor.ifBlank { explain.ifBlank { sourceUrl } }
}

data class MarketOverview(
    val id: Int,
    val summary: String,
    val oneLineSummary: String,
    val briefingDate: String,
    val briefingSession: String,
    val sentiment: String,
    val positiveFactors: List<String>,
    val negativeFactors: List<String>,
    val watchIssues: List<String>,
    val reasons: List<FactorReason>,
    val todayActions: List<String>,
    val indices: Map<String, String>,
    val sectorMoves: Map<String, String>,
    val generatedAt: String,
)

data class StockBriefing(
    val id: Int,
    val ticker: String,
    val briefingDate: String,
    val briefingSession: String,
    val sentiment: String,
    val summary: String,
    val oneLineSummary: String,
    val positiveFactors: List<String>,
    val negativeFactors: List<String>,
    val watchIssues: List<String>,
    val reasons: List<FactorReason>,
    val todayActions: List<String>,
    val generatedAt: String,
)

data class SectorBriefing(
    val id: Int,
    val sectorId: Int,
    val briefingDate: String,
    val briefingSession: String,
    val sentiment: String,
    val summary: String,
    val oneLineSummary: String,
    val positiveFactors: List<String>,
    val negativeFactors: List<String>,
    val watchIssues: List<String>,
    val reasons: List<FactorReason>,
    val todayActions: List<String>,
    val generatedAt: String,
)

data class VolatilityData(
    val generatedAt: String?,
    val scoreName: String,
    val disclaimer: String,
    val criteria: Map<String, Double>,
    val blueChip: VolatilityGroup,
    val all: VolatilityGroup,
)

data class VolatilityGroup(val items: List<VolatilityItem>)

data class VolatilityItem(
    val ticker: String,
    val score: Double,
    val premarketGap: Double,
    val premarketDirection: String,
    val highLowSpread: Double,
    val relativeVolume: Double?,
    val marketCap: Double,
    val newsCount: Int,
    val newsConfirmed: Boolean,
)

data class AnalysisCategory(
    val id: Int,
    val code: String,
    val nameKo: String,
    val nameEn: String,
    val type: String,
    val description: String,
)

data class AnalysisPreset(
    val id: Int,
    val code: String,
    val nameKo: String,
    val personaText: String,
    val isDefault: Boolean,
)

data class WatchlistRankingItem(
    val ticker: String,
    val nameKo: String,
    val nameEn: String,
    val fans: Int,
)

data class LensSetting(
    val categoryCodes: Set<String>,
    val presetCode: String?,
    val depth: String?,
    val note: String,
    val whyKey: String?,
)

fun authSessionFromJson(json: JSONObject) = AuthSession(
    accessToken = json.optString("access_token"),
    user = appUserFromJson(json.optJSONObject("user") ?: JSONObject()),
)

fun appUserFromJson(json: JSONObject) = AppUser(
    id = json.optInt("id"),
    email = json.optString("email"),
    nickname = json.optString("nickname"),
    investorType = json.optString("investor_type", "balanced"),
)

fun briefingDataFromJson(
    json: JSONObject,
    watchlistJson: JSONArray,
    stocksJson: JSONArray,
    sectorsJson: JSONArray,
    sectorWatchlistJson: JSONArray,
) = BriefingData(
    briefingDate = json.optString("briefing_date"),
    sessions = json.optJSONArray("sessions").objects().map(::briefingSessionFromJson),
    marketOverview = json.optJSONObject("market_overview")?.let(::marketOverviewFromJson),
    marketOverviews = json.optJSONArray("market_overviews").objects().map(::marketOverviewFromJson),
    stocks = json.optJSONArray("stocks").objects().map(::stockBriefingFromJson),
    missingTickers = json.optJSONArray("missing_tickers").strings(),
    watchlist = watchlistJson.objects().map(::watchlistItemFromJson),
    allStocks = stocksJson.objects().map(::stockItemFromJson),
    sectors = sectorsJson.objects().map(::sectorItemFromJson),
    sectorWatchlist = sectorWatchlistJson.objects().map(::sectorWatchlistItemFromJson),
    sectorBriefings = json.optJSONArray("sector_briefings").objects().map(::sectorBriefingFromJson),
    missingSectors = json.optJSONArray("missing_sectors").ints(),
)

fun volatilityDataFromJson(json: JSONObject) = VolatilityData(
    generatedAt = json.optString("generated_at").takeIf { it.isNotBlank() },
    scoreName = json.optString("score_name", "변동성 주목 점수"),
    disclaimer = json.optString("score_disclaimer", "이 점수는 투자 추천이 아닙니다."),
    criteria = json.optJSONObject("criteria").stringDoubleMap(),
    blueChip = volatilityGroupFromJson(json.optJSONObject("blue_chip") ?: JSONObject()),
    all = volatilityGroupFromJson(json.optJSONObject("all") ?: JSONObject()),
)

fun stockBriefingFromJson(json: JSONObject) = StockBriefing(
    id = json.optInt("id"),
    ticker = json.optString("ticker"),
    briefingDate = json.optString("briefing_date"),
    briefingSession = json.optString("briefing_session"),
    sentiment = json.optString("sentiment", "neutral"),
    summary = json.optString("summary"),
    oneLineSummary = json.optString("one_line_summary"),
    positiveFactors = json.optJSONArray("positive_factors").strings(),
    negativeFactors = json.optJSONArray("negative_factors").strings(),
    watchIssues = json.optJSONArray("watch_issues").strings(),
    reasons = json.optJSONArray("reasons").objects().map(::reasonFromJson),
    todayActions = json.optJSONArray("today_actions").strings(),
    generatedAt = json.optString("generated_at"),
)

fun sectorBriefingFromJson(json: JSONObject) = SectorBriefing(
    id = json.optInt("id"),
    sectorId = json.optInt("sector_id"),
    briefingDate = json.optString("briefing_date"),
    briefingSession = json.optString("briefing_session"),
    sentiment = json.optString("sentiment", "neutral"),
    summary = json.optString("summary"),
    oneLineSummary = json.optString("one_line_summary"),
    positiveFactors = json.optJSONArray("positive_factors").strings(),
    negativeFactors = json.optJSONArray("negative_factors").strings(),
    watchIssues = json.optJSONArray("watch_issues").strings(),
    reasons = json.optJSONArray("reasons").objects().map(::reasonFromJson),
    todayActions = json.optJSONArray("today_actions").strings(),
    generatedAt = json.optString("generated_at"),
)

fun marketOverviewFromJson(json: JSONObject) = MarketOverview(
    id = json.optInt("id"),
    summary = json.optString("summary"),
    oneLineSummary = json.optString("one_line_summary"),
    briefingDate = json.optString("briefing_date"),
    briefingSession = json.optString("briefing_session"),
    sentiment = json.optString("sentiment", "neutral"),
    positiveFactors = json.optJSONArray("positive_factors").strings(),
    negativeFactors = json.optJSONArray("negative_factors").strings(),
    watchIssues = json.optJSONArray("watch_issues").strings(),
    reasons = json.optJSONArray("reasons").objects().map(::reasonFromJson),
    todayActions = json.optJSONArray("today_actions").strings(),
    indices = json.optJSONObject("indices").stringMap(),
    sectorMoves = json.optJSONObject("sector_moves").stringMap(),
    generatedAt = json.optString("generated_at"),
)

fun briefingSessionFromJson(json: JSONObject) = BriefingSession(
    key = json.optString("key"),
    label = json.optString("label"),
    available = json.optBoolean("available"),
    scheduledAt = json.optString("scheduled_at"),
)

fun stockItemFromJson(json: JSONObject): StockItem {
    val sector = json.optJSONObject("sector")?.let(::sectorItemFromJson)
    return StockItem(
        ticker = json.optString("ticker"),
        nameKo = json.optString("name_ko"),
        nameEn = json.optString("name_en"),
        exchange = json.optString("exchange"),
        sectorId = if (json.isNull("sector_id")) null else json.optInt("sector_id"),
        sector = sector,
    )
}

fun sectorItemFromJson(json: JSONObject) = SectorItem(
    id = json.optInt("id"),
    nameKo = json.optString("name_ko"),
    nameEn = json.optString("name_en"),
)

fun analysisCategoryFromJson(json: JSONObject) = AnalysisCategory(
    id = json.optInt("id"),
    code = json.optString("code"),
    nameKo = json.optString("name_ko"),
    nameEn = json.optString("name_en"),
    type = json.optString("type"),
    description = json.optString("description"),
)

fun analysisPresetFromJson(json: JSONObject) = AnalysisPreset(
    id = json.optInt("id"),
    code = json.optString("code"),
    nameKo = json.optString("name_ko"),
    personaText = json.optString("persona_text"),
    isDefault = json.optBoolean("is_default"),
)

fun watchlistRankingItemFromJson(json: JSONObject) = WatchlistRankingItem(
    ticker = json.optString("ticker"),
    nameKo = json.optString("name_ko"),
    nameEn = json.optString("name_en"),
    fans = json.optInt("fans"),
)

private fun watchlistItemFromJson(json: JSONObject) = WatchlistItem(
    id = json.optInt("id"),
    ticker = json.optString("ticker"),
    stock = json.optJSONObject("stock")?.let(::stockItemFromJson),
    createdAt = json.optString("created_at"),
)

private fun sectorWatchlistItemFromJson(json: JSONObject) = SectorWatchlistItem(
    id = json.optInt("id"),
    sectorId = json.optInt("sector_id"),
    sector = json.optJSONObject("sector")?.let(::sectorItemFromJson),
    createdAt = json.optString("created_at"),
)

private fun reasonFromJson(json: JSONObject) = FactorReason(
    factor = json.optString("factor"),
    explain = json.optString("explain"),
    sourceUrl = json.optString("source_url"),
)

private fun volatilityGroupFromJson(json: JSONObject): VolatilityGroup {
    val metrics = json.optJSONObject("metrics") ?: JSONObject()
    val items = json.optJSONArray("tickers").strings()
        .mapNotNull { metrics.optJSONObject(it) }
        .map { item ->
            VolatilityItem(
                ticker = item.optString("ticker"),
                score = item.optDouble("volatility_attention_score"),
                premarketGap = item.optDouble("premarket_gap_pct"),
                premarketDirection = item.optString("premarket_direction"),
                highLowSpread = item.optDouble("high_low_spread_pct"),
                relativeVolume = if (item.isNull("premarket_relative_volume")) null else item.optDouble("premarket_relative_volume"),
                marketCap = item.optDouble("market_cap_usd"),
                newsCount = item.optInt("news_catalyst_count"),
                newsConfirmed = item.optBoolean("news_catalyst_confirmed"),
            )
        }
        .take(5)
    return VolatilityGroup(items)
}

fun JSONArray?.objects(): List<JSONObject> {
    if (this == null) return emptyList()
    return (0 until length()).mapNotNull { optJSONObject(it) }
}

fun JSONArray?.strings(): List<String> {
    if (this == null) return emptyList()
    return (0 until length()).map { optString(it) }
}

fun JSONArray?.ints(): List<Int> {
    if (this == null) return emptyList()
    return (0 until length()).map { optInt(it) }
}

fun JSONObject?.stringMap(): Map<String, String> {
    if (this == null) return emptyMap()
    return keys().asSequence().associateWith { key -> opt(key)?.toString().orEmpty() }
}

fun JSONObject?.stringDoubleMap(): Map<String, Double> {
    if (this == null) return emptyMap()
    return keys().asSequence().associateWith { key -> optDouble(key) }
}
