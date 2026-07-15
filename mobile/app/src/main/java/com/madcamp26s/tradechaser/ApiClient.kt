package com.madcamp26s.tradechaser

import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.SocketTimeoutException
import java.net.URL

class ApiException(val statusCode: Int, override val message: String) : Exception(message)

class ApiClient(
    private val baseUrl: String = "https://api.trend-chaser.madcamp-kaist.org",
) {
    var token: String? = null

    fun login(email: String, password: String): AuthSession {
        val session = authSessionFromJson(
            requestObject(
                "/auth/login",
                method = "POST",
                body = JSONObject().put("email", email).put("password", password),
                authenticated = false,
            )
        )
        token = session.accessToken
        return session
    }

    fun register(email: String, password: String, nickname: String): AuthSession {
        val session = authSessionFromJson(
            requestObject(
                "/auth/register",
                method = "POST",
                body = JSONObject().put("email", email).put("password", password).put("nickname", nickname),
                authenticated = false,
            )
        )
        token = session.accessToken
        return session
    }

    fun getMe(): AppUser = appUserFromJson(requestObject("/users/me"))

    fun getTodayBriefing(): BriefingData {
        val briefing = requestObject("/briefings/today")
        val watchlist = requestArray("/watchlist")
        val stocks = requestArray("/stocks", authenticated = false)
        val sectors = requestArray("/sectors", authenticated = false)
        val sectorWatchlist = requestArray("/sector-watchlist")
        return briefingDataFromJson(briefing, watchlist, stocks, sectors, sectorWatchlist)
    }

    fun refreshBriefing(): BriefingData {
        requestObject("/briefings/refresh", method = "POST")
        return getTodayBriefing()
    }

    fun refreshStockBriefing(ticker: String): StockBriefing =
        stockBriefingFromJson(requestObject("/briefings/refresh/stocks/${encode(ticker)}", method = "POST"))

    fun refreshSectorBriefing(sectorId: Int): SectorBriefing =
        sectorBriefingFromJson(requestObject("/briefings/refresh/sectors/$sectorId", method = "POST"))

    fun refreshMarketOverview(): MarketOverview =
        marketOverviewFromJson(requestObject("/briefings/refresh/overview", method = "POST"))

    fun getBriefingHistory(): List<StockBriefing> =
        requestArray("/briefings/history").objects().map(::stockBriefingFromJson)

    fun getMarketOverviewHistory(): List<MarketOverview> =
        requestArray("/briefings/history/overview").objects().map(::marketOverviewFromJson)

    fun getSectorBriefingHistory(): List<SectorBriefing> =
        requestArray("/briefings/history/sectors").objects().map(::sectorBriefingFromJson)

    fun addWatchlist(ticker: String): WatchlistItem =
        requestObject("/watchlist", method = "POST", body = JSONObject().put("ticker", ticker))
            .let { json ->
                val stock = json.optJSONObject("stock")?.let(::stockItemFromJson)
                WatchlistItem(json.optInt("id"), json.optString("ticker"), stock, json.optString("created_at"))
            }

    fun removeWatchlist(ticker: String) {
        request("/watchlist/${encode(ticker)}", method = "DELETE")
    }

    fun addSectorWatchlist(sectorId: Int): SectorWatchlistItem {
        val json = requestObject("/sector-watchlist", method = "POST", body = JSONObject().put("sector_id", sectorId))
        return SectorWatchlistItem(
            id = json.optInt("id"),
            sectorId = json.optInt("sector_id"),
            sector = json.optJSONObject("sector")?.let(::sectorItemFromJson),
            createdAt = json.optString("created_at"),
        )
    }

    fun removeSectorWatchlist(sectorId: Int) {
        request("/sector-watchlist/$sectorId", method = "DELETE")
    }

    fun getTodayVolatility(): VolatilityData =
        volatilityDataFromJson(requestObject("/stocks/volatility/today", authenticated = false))

    fun getStock(ticker: String): StockItem =
        stockItemFromJson(requestObject("/stocks/${encode(ticker)}", authenticated = false))

    fun updateMe(nickname: String, investorType: String): AppUser =
        appUserFromJson(
            requestObject(
                "/users/me",
                method = "PATCH",
                body = JSONObject().put("nickname", nickname).put("investor_type", investorType),
            )
        )

    fun listAnalysisCategories(): List<AnalysisCategory> =
        requestArray("/analysis-categories", authenticated = false).objects().map(::analysisCategoryFromJson)

    fun listAnalysisPresets(): List<AnalysisPreset> =
        requestArray("/analysis-presets", authenticated = false).objects().map(::analysisPresetFromJson)

    fun watchlistRanking(limit: Int = 10): List<WatchlistRankingItem> =
        requestArray("/watchlist/ranking/top?limit=$limit", authenticated = false).objects().map(::watchlistRankingItemFromJson)

    private fun requestObject(
        path: String,
        method: String = "GET",
        body: JSONObject? = null,
        authenticated: Boolean = true,
    ) = request(path, method, body, authenticated) as? JSONObject ?: JSONObject()

    private fun requestArray(
        path: String,
        method: String = "GET",
        body: JSONObject? = null,
        authenticated: Boolean = true,
    ) = request(path, method, body, authenticated) as? JSONArray ?: JSONArray()

    private fun request(
        path: String,
        method: String = "GET",
        body: JSONObject? = null,
        authenticated: Boolean = true,
    ): Any? {
        val connection = (URL("$baseUrl$path").openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 10_000
            readTimeout = 120_000
            setRequestProperty("Content-Type", "application/json")
            if (authenticated) token?.let { setRequestProperty("Authorization", "Bearer $it") }
            if (body != null) {
                doOutput = true
                outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            }
        }

        try {
            val statusCode = connection.responseCode
            if (statusCode == 204) return null
            val stream = if (statusCode in 200..299) connection.inputStream else connection.errorStream
            val raw = stream?.use { input ->
                BufferedReader(InputStreamReader(input, Charsets.UTF_8)).readText()
            }.orEmpty()
            val decoded = raw.takeIf { it.isNotBlank() }?.let {
                if (it.trimStart().startsWith("[")) JSONArray(it) else JSONObject(it)
            }
            if (statusCode !in 200..299) {
                val detail = (decoded as? JSONObject)?.opt("detail")
                throw ApiException(statusCode, errorText(detail, statusCode))
            }
            return decoded
        } catch (error: SocketTimeoutException) {
            throw ApiException(0, "서버 응답 시간이 초과되었습니다.")
        } finally {
            connection.disconnect()
        }
    }

    private fun errorText(detail: Any?, statusCode: Int): String {
        if (detail is String) return detail
        if (detail is JSONArray) {
            return (0 until detail.length())
                .mapNotNull { index ->
                    val item = detail.opt(index)
                    if (item is JSONObject) item.optString("msg").takeIf { it.isNotBlank() } else item?.toString()
                }
                .joinToString(" / ")
                .ifBlank { "서버 요청에 실패했습니다. ($statusCode)" }
        }
        if (detail is JSONObject) return detail.optString("msg", detail.toString())
        return "서버 요청에 실패했습니다. ($statusCode)"
    }

    private fun encode(value: String) = java.net.URLEncoder.encode(value, Charsets.UTF_8.name())
}
