package com.madcamp26s.tradechaser

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.RemoteViews

class TradeStockWidgetProvider : AppWidgetProvider() {
    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        appWidgetIds.forEach { updateWidget(context, appWidgetManager, it) }
    }

    override fun onAppWidgetOptionsChanged(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetId: Int,
        newOptions: Bundle,
    ) {
        updateWidget(context, appWidgetManager, appWidgetId)
    }

    companion object {
        private const val PREFS_NAME = "trade_chaser"
        private const val WIDGET_TITLE = "widget_stock_title"
        private const val WIDGET_SUBTITLE = "widget_stock_subtitle"
        private const val WIDGET_DATE = "widget_stock_date"
        private const val WIDGET_ROW_COUNT = "widget_stock_row_count"

        fun updateFromBriefing(context: Context, data: BriefingData) {
            val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            val editor = prefs.edit()

            clearRows(prefs, editor)
            if (data.watchlist.isEmpty()) {
                editor
                    .remove(WIDGET_TITLE)
                    .remove(WIDGET_SUBTITLE)
                    .remove(WIDGET_DATE)
                    .putInt(WIDGET_ROW_COUNT, 0)
                    .apply()
            } else {
                data.watchlist.forEachIndexed { index, watch ->
                    val briefing = latestStockBriefingFor(data, watch.ticker)
                    val summary = cleanText(briefing?.oneLineSummary)
                        ?: cleanText(briefing?.summary)
                        ?: "아직 오늘 브리핑이 생성되지 않았습니다."

                    editor
                        .putString(rowNameKey(index), trimForWidget(watch.ticker, 10))
                        .putString(rowPositiveKey(index), "+${briefing?.positiveFactors?.size ?: 0}")
                        .putString(rowNegativeKey(index), "-${briefing?.negativeFactors?.size ?: 0}")
                        .putString(rowSummaryKey(index), trimForWidget(summary, 70))
                }

                val firstDate = data.stocks.firstOrNull { stock ->
                    data.watchlist.any { it.ticker == stock.ticker }
                }?.briefingDate.orEmpty()

                editor
                    .putString(WIDGET_TITLE, "오늘의 브리핑")
                    .putString(WIDGET_SUBTITLE, "${data.watchlist.size}개 관심종목")
                    .putString(WIDGET_DATE, firstDate)
                    .putInt(WIDGET_ROW_COUNT, data.watchlist.size)
                    .apply()
            }
            refreshAll(context)
        }

        fun refreshAll(context: Context) {
            val manager = AppWidgetManager.getInstance(context)
            val component = ComponentName(context, TradeStockWidgetProvider::class.java)
            manager.getAppWidgetIds(component).forEach { updateWidget(context, manager, it) }
        }

        private fun updateWidget(context: Context, manager: AppWidgetManager, widgetId: Int) {
            val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            val title = prefs.getString(WIDGET_TITLE, null).orEmpty()
            val subtitle = prefs.getString(WIDGET_SUBTITLE, null).orEmpty()
            val date = prefs.getString(WIDGET_DATE, null).orEmpty()
            val rowCount = prefs.getInt(WIDGET_ROW_COUNT, 0)
            val hasRows = rowCount > 0

            val views = RemoteViews(context.packageName, R.layout.widget_stock_briefing)
            views.setOnClickPendingIntent(R.id.widget_root, openAppIntent(context))
            views.removeAllViews(R.id.widget_rows)
            if (!hasRows) {
                views.setTextViewText(R.id.widget_ticker, "오늘의 브리핑")
                views.setTextViewText(R.id.widget_name, "표시할 종목이 없습니다")
                views.setTextViewText(R.id.widget_summary, "앱에서 관심종목을 추가하고 브리핑을 불러와 주세요.")
                views.setViewVisibility(R.id.widget_summary, View.VISIBLE)
                views.setViewVisibility(R.id.widget_rows, View.GONE)
                views.setTextViewText(R.id.widget_date, "")
            } else {
                views.setTextViewText(R.id.widget_ticker, title)
                views.setTextViewText(R.id.widget_name, subtitle)
                views.setViewVisibility(R.id.widget_summary, View.GONE)
                views.setViewVisibility(R.id.widget_rows, View.VISIBLE)
                val visibleRows = visibleRowCount(manager, widgetId, rowCount)
                (0 until visibleRows).forEach { index ->
                    val name = prefs.getString(rowNameKey(index), null).orEmpty()
                    val positive = prefs.getString(rowPositiveKey(index), null).orEmpty()
                    val negative = prefs.getString(rowNegativeKey(index), null).orEmpty()
                    val summary = prefs.getString(rowSummaryKey(index), null).orEmpty()
                    if (name.isBlank()) return@forEach
                    views.addView(R.id.widget_rows, RemoteViews(context.packageName, R.layout.widget_stock_row).apply {
                        setTextViewText(R.id.widget_row_name, name)
                        setTextViewText(R.id.widget_row_positive, positive)
                        setTextViewText(R.id.widget_row_negative, negative)
                        setTextViewText(R.id.widget_row_summary, summary)
                    })
                }
                views.setTextViewText(R.id.widget_date, date)
            }
            manager.updateAppWidget(widgetId, views)
        }

        private fun visibleRowCount(manager: AppWidgetManager, widgetId: Int, storedCount: Int): Int {
            val options = manager.getAppWidgetOptions(widgetId)
            val minHeight = options.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT, 110)
            val available = minHeight - 64
            val rowsByHeight = (available / 40).coerceAtLeast(1)
            return storedCount.coerceAtMost(rowsByHeight)
        }

        private fun clearRows(prefs: android.content.SharedPreferences, editor: android.content.SharedPreferences.Editor) {
            val previousCount = prefs.getInt(WIDGET_ROW_COUNT, 0)
            (0 until previousCount).forEach {
                editor.remove(rowNameKey(it))
                    .remove(rowPositiveKey(it))
                    .remove(rowNegativeKey(it))
                    .remove(rowFactorKey(it))
                    .remove(rowSummaryKey(it))
            }
        }

        private fun rowNameKey(index: Int) = "widget_stock_${index}_name"

        private fun rowFactorKey(index: Int) = "widget_stock_${index}_factors"

        private fun rowPositiveKey(index: Int) = "widget_stock_${index}_positive"

        private fun rowNegativeKey(index: Int) = "widget_stock_${index}_negative"

        private fun rowSummaryKey(index: Int) = "widget_stock_${index}_summary"

        private fun latestStockBriefingFor(data: BriefingData, ticker: String): StockBriefing? {
            val rows = data.stocks.filter { it.ticker.equals(ticker, ignoreCase = true) }
            return rows
                .filter { cleanText(it.oneLineSummary) != null }
                .maxByOrNull { parseIsoMillis(it.generatedAt) ?: Long.MIN_VALUE }
                ?: rows.maxByOrNull { parseIsoMillis(it.generatedAt) ?: Long.MIN_VALUE }
        }

        private fun parseIsoMillis(value: String?): Long? {
            val raw = value?.trim().orEmpty()
            if (raw.isBlank()) return null
            val normalized = if (Regex("""(Z|[+-]\d{2}:?\d{2})$""").containsMatchIn(raw)) raw else "${raw}Z"
            val patterns = listOf(
                "yyyy-MM-dd'T'HH:mm:ss.SSSX",
                "yyyy-MM-dd'T'HH:mm:ssX",
                "yyyy-MM-dd HH:mm:ss.SSSX",
                "yyyy-MM-dd HH:mm:ssX",
            )
            return patterns.firstNotNullOfOrNull { pattern ->
                runCatching {
                    java.text.SimpleDateFormat(pattern, java.util.Locale.US).apply {
                        timeZone = java.util.TimeZone.getTimeZone("UTC")
                    }.parse(normalized)?.time
                }.getOrNull()
            }
        }

        private fun openAppIntent(context: Context): PendingIntent {
            val intent = Intent(context, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
            return PendingIntent.getActivity(
                context,
                0,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
            )
        }

        private fun trimForWidget(value: String, maxLength: Int): String {
            val compact = value.replace(Regex("\\s+"), " ").trim()
            return if (compact.length <= maxLength) compact else compact.take(maxLength - 1) + "…"
        }

        private fun cleanText(value: String?): String? {
            val text = value?.trim().orEmpty()
            return text.takeIf { it.isNotBlank() && !it.equals("null", ignoreCase = true) }
        }
    }
}
