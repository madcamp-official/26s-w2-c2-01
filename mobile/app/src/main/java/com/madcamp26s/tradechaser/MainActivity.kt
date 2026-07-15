package com.madcamp26s.tradechaser

import android.content.SharedPreferences
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.text.SpannableString
import android.text.Spanned
import android.text.method.LinkMovementMethod
import android.text.style.ClickableSpan
import android.text.style.ForegroundColorSpan
import android.text.style.StyleSpan
import android.text.style.UnderlineSpan
import android.view.Gravity
import android.view.View
import android.widget.CheckBox
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.HorizontalScrollView
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import com.google.android.material.chip.Chip
import com.google.android.material.chip.ChipGroup
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.TimeZone

class MainActivity : AppCompatActivity() {
    private val api = ApiClient()
    private val handler = Handler(Looper.getMainLooper())
    private lateinit var prefs: SharedPreferences

    private var session: AuthSession? = null
    private var briefing: BriefingData? = null
    private var volatility: VolatilityData? = null
    private var categories: List<AnalysisCategory> = emptyList()
    private var presets: List<AnalysisPreset> = emptyList()
    private var ranking: List<WatchlistRankingItem> = emptyList()
    private var stockHistory: List<StockBriefing> = emptyList()
    private var overviewHistory: List<MarketOverview> = emptyList()
    private var sectorHistory: List<SectorBriefing> = emptyList()
    private var extraStocks: Map<String, StockItem> = emptyMap()
    private var stockLoadingTickers: Set<String> = emptySet()
    private var dataError: String? = null
    private var refreshBusy = false
    private var refreshError: String? = null
    private var refreshingTicker: String? = null
    private var refreshingSectorId: Int? = null
    private var refreshingOverview = false
    private var removingTicker: String? = null
    private var removingSectorId: Int? = null
    private var historyLoading = false
    private var historyError: String? = null
    private var volatilityLoading = false
    private var volatilityError: String? = null
    private var addingVolatilityTicker: String? = null
    private var mutationError: String? = null
    private var profileSaving = false
    private var profileSaved = false
    private var profileError: String? = null
    private var profileInvestorType: String? = null

    private var selectedTab = 0
    private var briefingMode = 0
    private var briefingTimeMode = 0
    private var briefingSearchOpen = false
    private var detailTimeMode = 0
    private var selectedDetailSession: String? = null
    private var selectedHistoryDate: String? = null
    private var selectedHistorySession: String? = null
    private var volatilityBlueChip = true
    private var detailTarget: DetailTarget? = null
    private var lensTarget: LensTarget? = null
    private var lensPreviewExpanded = false
    private var lensCategorySearchOpen: Set<String> = emptySet()
    private var lensCategorySearchQuery: Map<String, String> = emptyMap()
    private val scrollPositions = mutableMapOf<String, Int>()
    private var currentScrollKey: String? = null
    private var currentScrollView: ScrollView? = null
    private val screenBackStack = mutableListOf<ScreenState>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        supportActionBar?.hide()
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                handleSystemBack()
            }
        })
        prefs = getSharedPreferences("trade_chaser", MODE_PRIVATE)
        restoreSession()
    }

    private fun restoreSession() {
        val savedToken = prefs.getString(TOKEN_KEY, null)
        if (savedToken.isNullOrBlank()) {
            showAuth()
            return
        }
        api.token = savedToken
        setContentView(loadingScreen("로그인 정보를 확인하는 중입니다."))
        async(
            work = { api.getMe() },
            success = { user ->
                session = AuthSession(savedToken, user)
                clearScrollPositions()
                showHome()
                loadInitialData()
            },
            error = {
                prefs.edit().remove(TOKEN_KEY).apply()
                api.token = null
                clearScrollPositions()
                showAuth()
            },
        )
    }

    private fun showAuth(register: Boolean = false) {
        val root = vertical {
            gravity = Gravity.CENTER
            setPadding(dp(24), dp(24), dp(24), dp(24))
            setBackgroundColor(BG)
        }
        val email = input("이메일")
        val password = input("비밀번호", password = true)
        val nickname = input("닉네임").apply { visibility = if (register) View.VISIBLE else View.GONE }
        val investmentRiskCheck = CheckBox(this).apply {
            text = "모든 투자에 대한 책임은 투자자 본인에게 있습니다."
            textSize = 12.5f
            setTextColor(RED)
            visibility = if (register) View.VISIBLE else View.GONE
            setPadding(0, dp(2), 0, dp(8))
        }
        var isRegister = register
        var busy = false

        root.addView(authLogo())
        root.addView(label("오늘의 브리핑과 변동성 종목을 확인하세요.", MUTED, Gravity.CENTER))
        root.addSpace(24)

        val toggle = horizontal()
        val loginButton = smallButton("로그인")
        val registerButton = smallButton("회원가입")
        toggle.addWeighted(loginButton)
        toggle.addWeighted(registerButton)
        root.addView(toggle)
        root.addSpace(16)
        root.addView(nickname)
        root.addView(email)
        root.addView(password)
        root.addView(investmentRiskCheck)

        val submit = primaryButton("")
        fun syncToggle() {
            nickname.visibility = if (isRegister) View.VISIBLE else View.GONE
            investmentRiskCheck.visibility = if (isRegister) View.VISIBLE else View.GONE
            if (!isRegister) investmentRiskCheck.isChecked = false
            submit.text = if (isRegister) "회원가입" else "로그인"
            submit.isEnabled = !busy && (!isRegister || investmentRiskCheck.isChecked)
            submit.alpha = if (submit.isEnabled) 1f else 0.45f
            loginButton.setBackgroundColor(if (!isRegister) ACCENT else ACCENT_BG)
            loginButton.setTextColor(if (!isRegister) Color.WHITE else ACCENT)
            registerButton.setBackgroundColor(if (isRegister) ACCENT else ACCENT_BG)
            registerButton.setTextColor(if (isRegister) Color.WHITE else ACCENT)
        }
        investmentRiskCheck.setOnCheckedChangeListener { _, _ -> syncToggle() }
        loginButton.setOnClickListener { isRegister = false; syncToggle() }
        registerButton.setOnClickListener { isRegister = true; syncToggle() }
        root.addSpace(12)
        root.addView(submit)
        submit.setOnClickListener {
            if (busy) return@setOnClickListener
            val emailText = email.value()
            val passwordText = password.value()
            val nicknameText = nickname.value()
            if (emailText.isBlank() || passwordText.isBlank() || (isRegister && nicknameText.isBlank())) {
                toast("필수 항목을 입력해주세요.")
                return@setOnClickListener
            }
            if (isRegister && !investmentRiskCheck.isChecked) {
                toast("투자 책임 안내에 동의해주세요.")
                return@setOnClickListener
            }
            busy = true
            submit.text = "처리 중..."
            syncToggle()
            async(
                work = {
                    if (isRegister) api.register(emailText, passwordText, nicknameText)
                    else api.login(emailText, passwordText)
                },
                success = {
                    session = it
                    api.token = it.accessToken
                    prefs.edit().putString(TOKEN_KEY, it.accessToken).apply()
                    clearScrollPositions()
                    showHome()
                    loadInitialData()
                },
                error = { toast(friendlyError(it)) },
                complete = {
                    busy = false
                    syncToggle()
                },
            )
        }
        syncToggle()
        setContentView(root)
    }

    private fun authLogo() = vertical {
        gravity = Gravity.CENTER_HORIZONTAL
        addView(ImageView(this@MainActivity).apply {
            setImageResource(R.drawable.app_logo)
            adjustViewBounds = true
            scaleType = ImageView.ScaleType.FIT_CENTER
        }, LinearLayout.LayoutParams(dp(190), dp(145)).apply {
            gravity = Gravity.CENTER_HORIZONTAL
        })
        addView(TextView(this@MainActivity).apply {
            text = "TRAND CHASER"
            textSize = 28f
            typeface = android.graphics.Typeface.create("sans-serif-black", android.graphics.Typeface.NORMAL)
            gravity = Gravity.CENTER
            letterSpacing = 0.02f
            includeFontPadding = false
            setTextColor(TEXT)
        }, LinearLayout.LayoutParams(-1, -2).apply {
            topMargin = dp(4)
        })
        addSpace(10)
    }

    private fun showHome() {
        saveCurrentScrollPosition()
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(BG)
        }
        val content = FrameLayout(this)
        var initializingNav = true
        val nav = BottomNavigationView(this).apply {
            setBackgroundColor(CARD)
            itemIconTintList = navigationTint()
            itemTextColor = navigationTint()
            menu.add(0, 0, 0, "오늘의 브리핑").setIcon(R.drawable.ic_nav_briefing)
            menu.add(0, 1, 1, "오늘의 변동성").setIcon(R.drawable.ic_nav_volatility)
            menu.add(0, 2, 2, "마이페이지").setIcon(R.drawable.ic_nav_mypage)
            setOnItemSelectedListener {
                if (initializingNav) return@setOnItemSelectedListener true
                selectTab(it.itemId, content)
            }
        }
        root.addView(content, LinearLayout.LayoutParams(-1, 0, 1f))
        root.addView(nav, LinearLayout.LayoutParams(-1, -2))
        setContentView(root)
        nav.selectedItemId = selectedTab
        initializingNav = false
        renderContent(content)
    }

    private fun selectTab(tabId: Int, container: FrameLayout): Boolean {
        val alreadyOnMain = selectedTab == tabId && detailTarget == null && lensTarget == null
        if (alreadyOnMain) return true

        saveCurrentScrollPosition()
        pushScreenState()
        selectedTab = tabId
        detailTarget = null
        lensTarget = null

        if (selectedTab == 1 && volatility == null && !volatilityLoading) {
            loadVolatility()
        } else {
            renderContent(container)
        }
        return true
    }

    private fun renderContent(container: FrameLayout) {
        saveCurrentScrollPosition()
        container.removeAllViews()
        val key = currentScreenKey()
        val view = when {
            lensTarget != null -> lensView(lensTarget!!)
            detailTarget != null -> detailView(detailTarget!!)
            selectedTab == 1 -> volatilityView()
            selectedTab == 2 -> myPageView()
            else -> briefingView()
        }
        container.addView(view)
        bindScrollRestoration(key, view)
    }

    private fun pushScreenState() {
        val state = currentScreenState()
        if (screenBackStack.lastOrNull() != state) {
            screenBackStack.add(state)
        }
    }

    private fun currentScreenState() = ScreenState(
        selectedTab = selectedTab,
        briefingMode = briefingMode,
        detailTarget = detailTarget,
        lensTarget = lensTarget,
        detailTimeMode = detailTimeMode,
        selectedDetailSession = selectedDetailSession,
        selectedHistoryDate = selectedHistoryDate,
        selectedHistorySession = selectedHistorySession,
    )

    private fun restoreScreenState(state: ScreenState) {
        selectedTab = state.selectedTab
        briefingMode = state.briefingMode
        detailTarget = state.detailTarget
        lensTarget = state.lensTarget
        detailTimeMode = state.detailTimeMode
        selectedDetailSession = state.selectedDetailSession
        selectedHistoryDate = state.selectedHistoryDate
        selectedHistorySession = state.selectedHistorySession
        showHome()
    }

    private fun handleSystemBack() {
        saveCurrentScrollPosition()
        val previous = screenBackStack.removeLastOrNull()
        if (previous != null) {
            restoreScreenState(previous)
            return
        }
        when {
            lensTarget != null || detailTarget != null -> {
                lensTarget = null
                detailTarget = null
                detailTimeMode = 0
                selectedDetailSession = null
                selectedHistoryDate = null
                selectedHistorySession = null
                selectedTab = 0
                showHome()
            }
            selectedTab != 0 -> {
                selectedTab = 0
                lensTarget = null
                detailTarget = null
                showHome()
            }
            else -> {
                finish()
            }
        }
    }

    private fun currentScreenKey(): String = when {
        lensTarget != null -> when (val target = lensTarget!!) {
            is LensTarget.Stock -> "lens:stock:${target.ticker}"
            is LensTarget.Sector -> "lens:sector:${target.sectorId}"
        }
        detailTarget != null -> {
            val targetKey = when (val target = detailTarget!!) {
                is DetailTarget.Stock -> "stock:${target.ticker}"
                is DetailTarget.Sector -> "sector:${target.sectorId}"
                is DetailTarget.Overview -> "overview"
            }
            "detail:$targetKey:mode:$detailTimeMode"
        }
        selectedTab == 0 -> "briefing:mode:$briefingMode"
        selectedTab == 1 -> "volatility"
        selectedTab == 2 -> "mypage"
        else -> "tab:$selectedTab"
    }

    private fun saveCurrentScrollPosition() {
        val key = currentScrollKey ?: return
        val scroll = currentScrollView ?: return
        scrollPositions[key] = scroll.scrollY
    }

    private fun clearScrollPositions() {
        scrollPositions.clear()
        currentScrollKey = null
        currentScrollView = null
        screenBackStack.clear()
    }

    private fun bindScrollRestoration(key: String, view: View) {
        val scroll = findScrollView(view)
        currentScrollKey = key
        currentScrollView = scroll
        if (scroll == null) return
        scroll.setOnScrollChangeListener { _, _, scrollY, _, _ ->
            scrollPositions[key] = scrollY
        }
        val savedY = scrollPositions[key] ?: 0
        scroll.post {
            scroll.scrollTo(0, savedY)
        }
    }

    private fun findScrollView(view: View): ScrollView? {
        if (view is ScrollView) return view
        if (view is android.view.ViewGroup) {
            for (index in 0 until view.childCount) {
                findScrollView(view.getChildAt(index))?.let { return it }
            }
        }
        return null
    }

    private fun loadInitialData() {
        dataError = null
        async(
            work = {
                InitialData(
                    briefing = api.getTodayBriefing(),
                    categories = api.listAnalysisCategories(),
                    presets = api.listAnalysisPresets(),
                    ranking = api.watchlistRanking(),
                )
            },
            success = {
                briefing = it.briefing
                categories = it.categories
                presets = it.presets
                ranking = it.ranking
                TradeStockWidgetProvider.updateFromBriefing(this, it.briefing)
                showHome()
            },
            error = {
                dataError = friendlyError(it)
                showHome()
            },
        )
    }

    private fun loadBriefing(clear: Boolean = true) {
        if (clear) briefing = null
        if (clear) dataError = null
        showHome()
        async(
            work = { api.getTodayBriefing() },
            success = {
                briefing = it
                dataError = null
                TradeStockWidgetProvider.updateFromBriefing(this, it)
                showHome()
            },
            error = {
                dataError = friendlyError(it)
                showHome()
            },
        )
    }

    private fun refreshBriefing() {
        if (refreshBusy) return
        refreshBusy = true
        refreshError = null
        showHome()
        async(
            work = { api.refreshBriefing() },
            success = {
                briefing = it
                refreshError = null
                TradeStockWidgetProvider.updateFromBriefing(this, it)
                showHome()
            },
            error = {
                refreshError = friendlyError(it)
                showHome()
            },
            complete = {
                refreshBusy = false
                showHome()
            },
        )
    }

    private fun refreshStockBriefing(ticker: String) {
        if (refreshingTicker != null) return
        refreshingTicker = ticker
        refreshError = null
        showHome()
        async(
            work = { api.refreshStockBriefing(ticker) },
            success = { updated ->
                briefing = briefing?.let { current ->
                    current.copy(
                        stocks = current.stocks.filterNot { it.ticker == ticker } + updated,
                        missingTickers = current.missingTickers.filterNot { it == ticker },
                    )
                }
                briefing?.let { TradeStockWidgetProvider.updateFromBriefing(this, it) }
                refreshError = null
                showHome()
            },
            error = {
                refreshError = friendlyError(it)
                showHome()
            },
            complete = {
                refreshingTicker = null
                showHome()
            },
        )
    }

    private fun refreshSectorBriefing(sectorId: Int) {
        if (refreshingSectorId != null) return
        refreshingSectorId = sectorId
        refreshError = null
        showHome()
        async(
            work = { api.refreshSectorBriefing(sectorId) },
            success = { updated ->
                briefing = briefing?.let { current ->
                    current.copy(
                        sectorBriefings = current.sectorBriefings.filterNot { it.sectorId == sectorId } + updated,
                        missingSectors = current.missingSectors.filterNot { it == sectorId },
                    )
                }
                briefing?.let { TradeStockWidgetProvider.updateFromBriefing(this, it) }
                refreshError = null
                showHome()
            },
            error = {
                refreshError = friendlyError(it)
                showHome()
            },
            complete = {
                refreshingSectorId = null
                showHome()
            },
        )
    }

    private fun refreshOverviewBriefing() {
        if (refreshingOverview) return
        refreshingOverview = true
        refreshError = null
        showHome()
        async(
            work = { api.refreshMarketOverview() },
            success = { updated ->
                briefing = briefing?.copy(marketOverview = updated)
                briefing?.let { TradeStockWidgetProvider.updateFromBriefing(this, it) }
                refreshError = null
                showHome()
            },
            error = {
                refreshError = friendlyError(it)
                showHome()
            },
            complete = {
                refreshingOverview = false
                showHome()
            },
        )
    }

    private fun loadHistory() {
        if (historyLoading) return
        historyLoading = true
        historyError = null
        showHome()
        async(
            work = { Triple(api.getBriefingHistory(), api.getMarketOverviewHistory(), api.getSectorBriefingHistory()) },
            success = {
                stockHistory = it.first
                overviewHistory = it.second
                sectorHistory = it.third
                historyError = null
                showHome()
            },
            error = {
                historyError = friendlyError(it)
                showHome()
            },
            complete = {
                historyLoading = false
                showHome()
            },
        )
    }

    private fun loadVolatility() {
        if (volatilityLoading) return
        volatility = null
        volatilityLoading = true
        volatilityError = null
        showHome()
        async(
            work = { api.getTodayVolatility() },
            success = {
                volatility = it
                volatilityError = null
                showHome()
            },
            error = {
                volatilityError = friendlyError(it)
                showHome()
            },
            complete = {
                volatilityLoading = false
                showHome()
            },
        )
    }

    private fun briefingView(): View {
        val data = briefing
        val root = scrollColumn()
        val header = horizontal()
        header.addWeighted(title("오늘의 브리핑", 27, TEXT, Gravity.NO_GRAVITY))
        root.addView(header)
        root.addView(label("안 본 사이 있었던 일만 간단히 정리했습니다.", MUTED, Gravity.NO_GRAVITY).apply {
            textSize = 13f
        })
        root.addView(label("장시작·장중·장마감·휴장 중 하루 4번 자동으로 갱신됩니다.", MUTED, Gravity.NO_GRAVITY).apply {
            textSize = 12f
            maxLines = 1
            isSingleLine = true
        })
        refreshError?.let { root.addView(statusCard(it, RED)) }
        mutationError?.let { root.addView(statusCard(it, RED)) }
        dataError?.let { root.addView(statusCard(it, RED)) }
        root.addSpace(12)
        val briefingTabs = horizontal()
        briefingTabs.addWeighted(chips(listOf("관심 종목", "관심 섹터", "전체"), briefingMode) {
            briefingMode = it
            if (it == 2) briefingSearchOpen = false
            showHome()
        })
        root.addView(briefingTabs)
        root.addSpace(12)

        if (data == null) {
            root.addView(loading("오늘의 브리핑을 불러오는 중입니다."))
            return root.parent as View
        }
        when (briefingMode) {
            0 -> stockBriefing(root, data)
            1 -> sectorBriefing(root, data)
            else -> root.addView(overviewCard(data.marketOverview).apply {
                setOnClickListener { openDetail(DetailTarget.Overview()) }
            })
        }
        return root.parent as View
    }

    private fun historyContent(root: LinearLayout) {
        val data = briefing
        if (historyLoading) {
            root.addView(loading("이전 기록을 불러오는 중입니다."))
            return
        }
        historyError?.let {
            root.addView(statusCard(it, RED))
            root.addView(smallButton("다시 불러오기").apply { setOnClickListener { loadHistory() } })
            return
        }
        when (briefingMode) {
            0 -> {
                if (stockHistory.isEmpty()) root.addView(empty("아직 종목 브리핑 기록이 없습니다."))
                stockHistory.forEach { row ->
                    root.addView(card {
                        addView(title("${row.briefingDate} · ${row.ticker}", 16, TEXT, Gravity.NO_GRAVITY))
                        addView(label(row.summary, MUTED, Gravity.NO_GRAVITY))
                    }.apply { setOnClickListener { openDetail(DetailTarget.Stock(row.ticker, row)) } })
                }
            }
            1 -> {
                if (sectorHistory.isEmpty()) root.addView(empty("아직 섹터 브리핑 기록이 없습니다."))
                sectorHistory.forEach { row ->
                    val sector = data?.sectors?.firstOrNull { it.id == row.sectorId }
                    root.addView(card {
                        addView(title("${row.briefingDate} · ${sector?.nameKo ?: "섹터 #${row.sectorId}"}", 16, TEXT, Gravity.NO_GRAVITY))
                        addView(label(row.summary, MUTED, Gravity.NO_GRAVITY))
                    }.apply { setOnClickListener { openDetail(DetailTarget.Sector(row.sectorId, row)) } })
                }
            }
            else -> {
                if (overviewHistory.isEmpty()) root.addView(empty("아직 전체 시황 기록이 없습니다."))
                overviewHistory.forEach { row ->
                    root.addView(card {
                        addView(title("${row.briefingDate} · 전체 시황", 16, TEXT, Gravity.NO_GRAVITY))
                        addView(label(row.summary, MUTED, Gravity.NO_GRAVITY))
                    }.apply { setOnClickListener { openDetail(DetailTarget.Overview(row)) } })
                }
            }
        }
    }

    private fun stockBriefing(root: LinearLayout, data: BriefingData) {
        root.addView(briefingSectionHeader("관심 종목 ${data.watchlist.size}", showSearch = true))
        if (briefingSearchOpen) {
            val search = input("티커 또는 종목명으로 검색해서 추가")
            val results = vertical()
            root.addView(search)
            root.addView(results)
            fun renderResults(query: String) {
                results.removeAllViews()
                val watched = data.watchlist.map { it.ticker }.toSet()
                data.allStocks
                    .filter {
                        query.isNotBlank() && it.ticker !in watched &&
                            (it.ticker.contains(query, true) || it.nameKo.contains(query, true) || it.nameEn.contains(query, true))
                    }
                    .take(12)
                    .forEach { stock ->
                        results.addView(resultRow(stock.ticker, listOf(stock.displayName, stock.sectorName).filter { it.isNotBlank() }.joinToString(" · ")) {
                            mutate({ api.addWatchlist(stock.ticker) }, "관심 종목을 추가했습니다.") { openLens(LensTarget.Stock(stock.ticker)) }
                        })
                    }
            }
            search.edit().addTextChangedListener(SimpleWatcher { renderResults(it) })
            root.addSpace(16)
        }
        if (data.watchlist.isEmpty()) {
            root.addView(empty("검색해서 관심 종목을 추가하면 브리핑이 생성됩니다."))
        } else {
            data.watchlist.forEach { watch ->
                val item = latestStockBriefingFor(data, watch.ticker)
                root.addView(stockCard(watch, item))
            }
        }
    }

    private fun sectorBriefing(root: LinearLayout, data: BriefingData) {
        root.addView(briefingSectionHeader("관심 섹터 ${data.sectorWatchlist.size}", showSearch = true))
        if (briefingSearchOpen) {
            val search = input("섹터명으로 검색해서 추가")
            val results = vertical()
            root.addView(search)
            root.addView(results)
            fun renderResults(query: String) {
                results.removeAllViews()
                val watched = data.sectorWatchlist.map { it.sectorId }.toSet()
                val available = data.sectors.filter { it.id !in watched }
                val filtered = available.filter {
                    query.isBlank() || it.nameKo.contains(query, true) || it.nameEn.contains(query, true)
                }
                when {
                    available.isEmpty() -> results.addView(label("모든 섹터를 이미 관심 섹터에 추가했습니다.", MUTED, Gravity.NO_GRAVITY).apply {
                        setPadding(dp(2), dp(8), dp(2), dp(8))
                        textSize = 12.5f
                    })
                    filtered.isEmpty() -> results.addView(label("검색 결과가 없습니다.", MUTED, Gravity.NO_GRAVITY).apply {
                        setPadding(dp(2), dp(8), dp(2), dp(8))
                        textSize = 12.5f
                    })
                    else -> filtered.forEach { sector ->
                        results.addView(resultRow(sector.nameKo, "") {
                            mutate({ api.addSectorWatchlist(sector.id) }, "관심 섹터를 추가했습니다.") { openLens(LensTarget.Sector(sector.id)) }
                        })
                    }
                }
            }
            search.edit().addTextChangedListener(SimpleWatcher { renderResults(it) })
            renderResults("")
            root.addSpace(16)
        }
        if (data.sectorWatchlist.isEmpty()) {
            root.addView(empty("검색해서 관심 섹터를 추가하면 여기 섹터 브리핑이 생성됩니다."))
        } else {
            data.sectorWatchlist.forEach { watch ->
                val item = latestSectorBriefingFor(data, watch.sectorId)
                root.addView(sectorCard(watch, item))
            }
        }
    }

    private fun latestStockBriefingFor(data: BriefingData, ticker: String): StockBriefing? {
        val rows = data.stocks.filter { it.ticker.equals(ticker, ignoreCase = true) }
        return rows
            .filter { cleanDisplayText(it.oneLineSummary) != null }
            .maxByOrNull { parseIsoMillis(it.generatedAt) ?: Long.MIN_VALUE }
            ?: rows.maxByOrNull { parseIsoMillis(it.generatedAt) ?: Long.MIN_VALUE }
    }

    private fun latestSectorBriefingFor(data: BriefingData, sectorId: Int): SectorBriefing? {
        val rows = data.sectorBriefings.filter { it.sectorId == sectorId }
        return rows
            .filter { cleanDisplayText(it.oneLineSummary) != null }
            .maxByOrNull { parseIsoMillis(it.generatedAt) ?: Long.MIN_VALUE }
            ?: rows.maxByOrNull { parseIsoMillis(it.generatedAt) ?: Long.MIN_VALUE }
    }

    private fun volatilityView(): View {
        val data = volatility
        val root = scrollColumn()
        root.addView(volatilityHero(data))
        root.addSpace(16)
        val threshold = data?.criteria?.get("blue_chip_market_cap_usd") ?: 2_000_000_000.0
        val liquidity = data?.criteria?.get("all_stock_min_dollar_volume") ?: 1_000_000.0
        root.addView(volatilityTabs(threshold, liquidity) {
            volatilityBlueChip = it == 0
            showHome()
        })
        root.addSpace(12)
        root.addView(volatilityPanel(data))
        val disclaimer = data?.disclaimer?.takeIf { it.isNotBlank() }
            ?: "이 점수는 투자 추천이나 미래 수익을 예측하지 않습니다."
        root.addView(label("$disclaimer \n프리마켓 가격은 정규장 시가와 다를 수 있습니다.", SOFT_MUTED, Gravity.RIGHT).apply {
            textSize = 11f
            setPadding(0, dp(10), 0, 0)
        })
        return root.parent as View
    }

    private fun myPageView(): View {
        val current = session?.user ?: return empty("로그인이 필요합니다.")
        val data = briefing
        val root = scrollColumn()
        val nickname = input("닉네임").apply { edit().setText(current.nickname) }
        val investorType = profileInvestorType ?: current.investorType
        root.addView(card {
            addView(sectionTitle("프로필"))
            addSpace(16)
            val profileHead = horizontal()
            profileHead.addView(profileAvatar(current.nickname))
            profileHead.addView(vertical {
                setPadding(dp(16), 0, 0, 0)
                addView(title(current.nickname.ifBlank { "사용자" }, 16, TEXT, Gravity.NO_GRAVITY))
                addView(label(current.email, SOFT_MUTED, Gravity.NO_GRAVITY).apply { textSize = 12f })
            })
            addView(profileHead)
            addSpace(20)
            addView(profileGroupTitle("닉네임"))
            addView(nickname)
            addView(profileGroupTitle("투자 성향"))
            addView(chips(listOf("안정형", "균형형", "공격형"), typeIndex(investorType)) {
                profileInvestorType = listOf("stable", "balanced", "aggressive")[it]
                showHome()
            })
            addView(label(investorTypeDescription(investorType), SOFT_MUTED, Gravity.NO_GRAVITY).apply {
                textSize = 11.5f
                setPadding(0, dp(8), 0, 0)
            })
            profileError?.let { addView(statusCard(it, RED)) }
            if (profileSaved) addView(statusCard("프로필을 저장했습니다.", ACCENT))
            addSpace(14)
            addView(primaryButton(if (profileSaving) "저장 중..." else "프로필 저장").apply {
                isEnabled = !profileSaving
                setOnClickListener {
                    profileSaving = true
                    profileSaved = false
                    profileError = null
                    showHome()
                    async(
                        work = { api.updateMe(nickname.value(), investorType) },
                        success = { user ->
                            session = session?.copy(user = user)
                            profileInvestorType = user.investorType
                            profileSaved = true
                            showHome()
                        },
                        error = {
                            profileError = friendlyError(it)
                            showHome()
                        },
                        complete = {
                            profileSaving = false
                            showHome()
                            if (profileSaved) handler.postDelayed({
                                profileSaved = false
                                if (selectedTab == 2) showHome()
                            }, 1200)
                        },
                    )
                }
            })
        })
        root.addSpace(18)
        root.addView(card {
            val head = horizontal()
            head.addWeighted(sectionTitle("관심 종목"))
            head.addView(label("${data?.watchlist?.size ?: 0}개", SOFT_MUTED, Gravity.RIGHT).apply { textSize = 12f })
            addView(head)
            addSpace(12)
            if (data == null || data.watchlist.isEmpty()) {
                addView(myPageStrip("아직 관심 종목이 없습니다."))
            } else {
                data.watchlist.forEachIndexed { index, watch ->
                    if (index > 0) addSpace(10)
                    addView(myPageWatchRow(watch))
                }
            }
            addView(myPageHint())
        })
        root.addSpace(12)
        root.addView(smallButton("로그아웃").apply {
            setOnClickListener {
                prefs.edit().remove(TOKEN_KEY).apply()
                api.token = null
                session = null
                briefing = null
                volatility = null
                selectedTab = 0
                clearScrollPositions()
                showAuth()
            }
        })
        return root.parent as View
    }

    private fun detailView(target: DetailTarget): View {
        val root = scrollColumn()
        root.addView(textMutedBackButton("< 오늘의 브리핑으로") {
            detailTarget = null
            showHome()
        })
        root.addSpace(12)
        root.addView(detailTimeTabsV2(detailTimeMode) {
            detailTimeMode = it
            if (it == 1 && stockHistory.isEmpty() && overviewHistory.isEmpty() && sectorHistory.isEmpty()) loadHistory()
            showHome()
        })
        root.addSpace(12)
        if (detailTimeMode == 0) {
            ensureSelectedDetailSession(target)
            root.addView(detailSessionTabs(target))
            root.addSpace(12)
        }
        if (detailTimeMode == 1) detailHistoryContent(root, target)
        else detailTodayContent(root, target)
        if (target is DetailTarget.Overview) addOverviewDisclaimer(root)
        return root.parent as View
    }

    private fun ensureSelectedDetailSession(target: DetailTarget) {
        val sessions = detailSessionItems(target)
        if (sessions.isEmpty()) return
        val latest = detailRowsFor(target)
            .filter { row -> sessions.any { it.key == row.key && it.available } }
            .maxByOrNull { parseIsoMillis(it.generatedAt) ?: Long.MIN_VALUE }
            ?.key
            ?: sessions.asReversed().firstOrNull { it.available }?.key
            ?: sessions.lastOrNull()?.key
        if (selectedDetailSession == null || sessions.none { it.key == selectedDetailSession }) {
            selectedDetailSession = latest
        }
    }

    private fun detailSessionTabs(target: DetailTarget) = vertical {
        val sessions = detailSessionItems(target)
        if (sessions.isEmpty()) return@vertical
        sessions.forEach { session ->
            addView(detailSessionButton(session, selectedDetailSession == session.key))
            addSpace(7)
        }
    }

    private data class DetailSessionItem(
        val key: String,
        val label: String,
        val available: Boolean,
        val scheduledAt: String,
        val generatedAt: String?,
    )

    private data class DetailSessionRow(val key: String, val generatedAt: String)

    private fun detailSessionItems(target: DetailTarget): List<DetailSessionItem> {
        val rows = detailRowsFor(target)
        val byKey = rows.associateBy { it.key }
        val base = briefing?.sessions.orEmpty().map { session ->
            val generatedAt = byKey[session.key]?.generatedAt
            DetailSessionItem(
                key = session.key,
                label = session.label,
                available = session.available,
                scheduledAt = session.scheduledAt,
                generatedAt = generatedAt,
            )
        }
        val additional = byKey["additional"] ?: return base
        return base + DetailSessionItem(
            key = "additional",
            label = additionalSessionLabel(additional.generatedAt),
            available = true,
            scheduledAt = additional.generatedAt,
            generatedAt = additional.generatedAt,
        )
    }

    private fun detailRowsFor(target: DetailTarget): List<DetailSessionRow> {
        val data = briefing ?: return emptyList()
        return when (target) {
            is DetailTarget.Overview -> data.marketOverviews
                .map { DetailSessionRow(it.briefingSession, it.generatedAt) }
            is DetailTarget.Stock -> data.stocks
                .filter { it.ticker == target.ticker }
                .map { DetailSessionRow(it.briefingSession, it.generatedAt) }
            is DetailTarget.Sector -> data.sectorBriefings
                .filter { it.sectorId == target.sectorId }
                .map { DetailSessionRow(it.briefingSession, it.generatedAt) }
        }
    }

    private fun detailSessionButton(session: DetailSessionItem, selected: Boolean) = horizontal().apply {
        setPadding(dp(14), dp(11), dp(14), dp(11))
        background = roundedStrokeBackground(
            fill = if (selected) ACCENT_BG else CARD,
            stroke = if (selected) ACCENT else LINE,
            radius = dp(10).toFloat(),
        )
        alpha = if (session.available) 1f else 0.42f
        addWeighted(title(session.label, 14, if (selected) ACCENT else TEXT, Gravity.NO_GRAVITY))
        addView(label(detailSessionSubText(session), MUTED, Gravity.RIGHT).apply { textSize = 11.5f })
        isEnabled = session.available
        setOnClickListener {
            if (!session.available) return@setOnClickListener
            selectedDetailSession = session.key
            showHome()
        }
    }

    private fun detailSessionSubText(session: DetailSessionItem): String {
        return if (session.available) {
            session.generatedAt?.takeIf { it.isNotBlank() }?.let {
                "KST ${formatTimeInZone(it, "Asia/Seoul")} · ET ${formatTimeInZone(it, "America/New_York")}"
            } ?: "업데이트 대기"
        } else {
            "${formatTimeInZone(session.scheduledAt, "Asia/Seoul")} 예정"
        }
    }

    private fun additionalSessionLabel(generatedAt: String): String {
        val marketOpenAt = briefing?.sessions?.firstOrNull { it.key == "market_open" }?.scheduledAt ?: return "추가"
        val generated = parseIsoMillis(generatedAt) ?: return "추가"
        val open = parseIsoMillis(marketOpenAt) ?: return "추가"
        val hours = (generated - open) / 3_600_000.0
        val sign = if (hours < 0) "-" else "+"
        return "장시작 $sign${"%.1f".format(Locale.US, kotlin.math.abs(hours))}h"
    }

    private fun formatTimeInZone(value: String, zoneId: String): String {
        val millis = parseIsoMillis(value) ?: return "--:--"
        return SimpleDateFormat("HH:mm", Locale.KOREA).apply {
            timeZone = TimeZone.getTimeZone(zoneId)
        }.format(java.util.Date(millis))
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
                SimpleDateFormat(pattern, Locale.US).apply {
                    timeZone = TimeZone.getTimeZone("UTC")
                }.parse(normalized)?.time
            }.getOrNull()
        }
    }

    private fun detailTimeTabsV2(selected: Int, onSelected: (Int) -> Unit): View {
        val outer = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(dp(5), dp(5), dp(5), dp(5))
            background = roundedStrokeBackground(CARD, LINE, dp(12).toFloat())
        }
        listOf("오늘", "이전 기록").forEachIndexed { index, text ->
            outer.addView(TextView(this).apply {
                this.text = text
                textSize = 13.5f
                gravity = Gravity.CENTER
                typeface = if (selected == index) android.graphics.Typeface.DEFAULT_BOLD else android.graphics.Typeface.DEFAULT
                setTextColor(if (selected == index) Color.WHITE else MUTED)
                setPadding(0, dp(9), 0, dp(9))
                background = if (selected == index) {
                    roundedStrokeBackground(ACCENT, ACCENT, dp(8).toFloat())
                } else {
                    roundedStrokeBackground(Color.TRANSPARENT, Color.TRANSPARENT, dp(8).toFloat())
                }
                setOnClickListener { onSelected(index) }
            }, LinearLayout.LayoutParams(0, -2, 1f))
        }
        return outer
    }

    private fun oldDetailView(target: DetailTarget): View {
        val root = scrollColumn()
        root.addView(textBackButton("< 브리핑으로") {
            detailTarget = null
            showHome()
        })
        root.addSpace(12)
        when (target) {
            is DetailTarget.Overview -> {
                val overview = target.item ?: briefing?.marketOverview
                root.addView(pageTitle("전체 시황", overview?.briefingDate.orEmpty()))
                if (overview == null) {
                    root.addView(empty("전체 시황 브리핑이 없습니다."))
                } else {
                    if (overview.indices.isNotEmpty()) {
                        root.addView(sectionTitle("주요 지수"))
                        overview.indices.forEach { (k, v) -> root.addView(metricRow(k, v)) }
                    }
                    root.addView(card { addView(label(overview.summary, TEXT, Gravity.NO_GRAVITY)) })
                }
            }
            is DetailTarget.Stock -> {
                val data = briefing
                val item = target.item ?: data?.stocks?.firstOrNull { it.ticker == target.ticker }
                val stock = data?.allStocks?.firstOrNull { it.ticker == target.ticker } ?: extraStocks[target.ticker]
                if (stock == null && target.ticker !in stockLoadingTickers) loadStock(target.ticker)
                root.addView(pageTitle(target.ticker, listOf(stock?.displayName, stock?.sectorName).filterNotNull().filter { it.isNotBlank() }.joinToString(" · ")))
                root.addView(detailActions(
                    onLens = { openLens(LensTarget.Stock(target.ticker)) },
                    onToggle = { toggleWatch(target.ticker) },
                    toggleLabel = if (data?.watchlist?.any { it.ticker == target.ticker } == true) "관심 종목 제거" else "관심 종목 추가",
                ))
                root.addSpace(12)
                if (stock == null) root.addView(statusCard("종목 정보를 불러오는 중입니다.", ACCENT))
                if (item == null) root.addView(empty("이 종목의 브리핑이 아직 없습니다."))
                else root.addView(stockDetailCard(item))
            }
            is DetailTarget.Sector -> {
                val data = briefing
                val item = target.item ?: data?.sectorBriefings?.firstOrNull { it.sectorId == target.sectorId }
                val sector = data?.sectors?.firstOrNull { it.id == target.sectorId }
                root.addView(pageTitle(sector?.nameKo ?: "섹터 #${target.sectorId}", sector?.nameEn.orEmpty()))
                root.addView(detailActions(
                    onLens = { openLens(LensTarget.Sector(target.sectorId)) },
                    onToggle = { toggleSectorWatch(target.sectorId) },
                    toggleLabel = if (data?.sectorWatchlist?.any { it.sectorId == target.sectorId } == true) "관심 섹터 제거" else "관심 섹터 추가",
                ))
                root.addSpace(12)
                if (item == null) root.addView(empty("이 섹터의 브리핑이 아직 없습니다."))
                else root.addView(sectorDetailCard(item))
            }
        }
        return root.parent as View
    }

    private fun detailTodayContent(root: LinearLayout, target: DetailTarget) {
        val data = briefing
        val selectedSession = selectedDetailSession
        when (target) {
            is DetailTarget.Overview -> {
                val overview = target.item
                    ?: data?.marketOverviews?.firstOrNull { it.briefingSession == selectedSession }
                    ?: data?.marketOverview
                if (overview == null) {
                    root.addView(empty("아직 전체 시황 브리핑이 생성되지 않았습니다. 뉴스 수집·분석 파이프라인이 연결되면 이곳에 표시됩니다."))
                    return
                }
                root.addView(detailBlockV2(
                    titleText = "전체 시황",
                    subtitle = "",
                    sentiment = overview.sentiment,
                    oneLineSummary = overview.oneLineSummary,
                    summary = overview.summary,
                    positive = overview.positiveFactors,
                    negative = overview.negativeFactors,
                    watch = overview.watchIssues,
                    reasons = overview.reasons,
                    indices = overview.indices,
                    sectorMoves = overview.sectorMoves,
                    indexColumns = 1,
                ))
            }
            is DetailTarget.Stock -> {
                val item = target.item
                    ?: data?.stocks?.firstOrNull { it.ticker == target.ticker && it.briefingSession == selectedSession }
                    ?: data?.stocks?.lastOrNull { it.ticker == target.ticker }
                val stock = data?.allStocks?.firstOrNull { it.ticker == target.ticker } ?: extraStocks[target.ticker]
                if (stock == null && target.ticker !in stockLoadingTickers) loadStock(target.ticker)
                if (item == null) {
                    root.addView(empty("이 종목의 오늘 브리핑이 아직 없습니다."))
                } else {
                    val name = cleanDisplayText(stock?.nameKo) ?: cleanDisplayText(stock?.nameEn)
                    val sector = cleanDisplayText(stock?.sectorName) ?: "섹터 미지정"
                    val exchange = cleanDisplayText(stock?.exchange)?.uppercase() ?: "거래소 미지정"
                    root.addView(detailBlockV2(
                        titleText = listOfNotNull(target.ticker, name).joinToString(" · "),
                        subtitle = "섹터: $sector · 거래소: $exchange",
                        sentiment = item.sentiment,
                        oneLineSummary = item.oneLineSummary,
                        summary = item.summary,
                        positive = item.positiveFactors,
                        negative = item.negativeFactors,
                        watch = item.watchIssues,
                        reasons = item.reasons,
                    ) {
                        detailActions(
                            onLens = { openLens(LensTarget.Stock(target.ticker)) },
                            onToggle = { toggleWatch(target.ticker) },
                            toggleLabel = if (data?.watchlist?.any { it.ticker == target.ticker } == true) "관심종목에서 제거" else "관심종목에 추가",
                        ).also { addView(it) }
                    })
                }
            }
            is DetailTarget.Sector -> {
                val item = target.item
                    ?: data?.sectorBriefings?.firstOrNull { it.sectorId == target.sectorId && it.briefingSession == selectedSession }
                    ?: data?.sectorBriefings?.lastOrNull { it.sectorId == target.sectorId }
                val sector = data?.sectors?.firstOrNull { it.id == target.sectorId }
                if (item == null) {
                    root.addView(empty("이 섹터의 오늘 브리핑이 아직 없습니다."))
                } else {
                    root.addView(detailBlockV2(
                        titleText = "${sector?.nameKo ?: "섹터 #${target.sectorId}"} 섹터",
                        subtitle = "",
                        sentiment = item.sentiment,
                        oneLineSummary = item.oneLineSummary,
                        summary = item.summary,
                        positive = item.positiveFactors,
                        negative = item.negativeFactors,
                        watch = item.watchIssues,
                        reasons = item.reasons,
                        sectorEtfs = representativeSectorEtfs(sector?.nameEn),
                    ) {
                        detailActions(
                            onLens = { openLens(LensTarget.Sector(target.sectorId)) },
                            onToggle = { toggleSectorWatch(target.sectorId) },
                            toggleLabel = if (data?.sectorWatchlist?.any { it.sectorId == target.sectorId } == true) "관심섹터에서 제거" else "관심섹터에 추가",
                        ).also { addView(it) }
                    })
                }
            }
        }
    }

    private fun detailHistoryContent(root: LinearLayout, target: DetailTarget) {
        if (historyLoading) {
            root.addView(loading("이전 기록을 불러오는 중입니다."))
            return
        }
        historyError?.let {
            root.addView(statusCard(it, RED))
            root.addView(smallButton("다시 불러오기").apply { setOnClickListener { loadHistory() } })
            return
        }
        val rows = historyRowsFor(target)
        if (rows.isEmpty()) {
            root.addView(empty(historyEmptyText(target)))
            return
        }
        val dates = rows.map { it.briefingDate }.distinct().sortedDescending()
        if (selectedHistoryDate !in dates) selectedHistoryDate = dates.firstOrNull()
        val date = selectedHistoryDate ?: return
        val dateRows = rows.filter { it.briefingDate == date }
        val sessions = historySessionItems(date, dateRows)
        val available = sessions.filter { it.available }
        if (selectedHistorySession == null || available.none { it.key == selectedHistorySession }) {
            selectedHistorySession = available.firstOrNull()?.key
        }
        root.addView(historyDateTabs(dates))
        root.addSpace(4)
        root.addView(historySessionTabs(sessions))
        root.addSpace(12)
        val selectedRow = dateRows.firstOrNull { it.briefingSession == selectedHistorySession }
        if (selectedRow == null) {
            root.addView(statusCard("해당 세션의 기록이 없습니다.", ACCENT))
            return
        }
        root.addView(detailBlockV2(
            titleText = selectedRow.briefingDate,
            subtitle = selectedRow.subtitle,
            sentiment = selectedRow.sentiment,
            oneLineSummary = selectedRow.oneLineSummary,
            summary = selectedRow.summary,
            positive = selectedRow.positive,
            negative = selectedRow.negative,
            watch = selectedRow.watch,
            reasons = selectedRow.reasons,
            indices = selectedRow.indices,
            sectorMoves = selectedRow.sectorMoves,
        ))
    }

    private data class DetailHistoryRow(
        val briefingDate: String,
        val briefingSession: String,
        val generatedAt: String,
        val subtitle: String,
        val sentiment: String?,
        val oneLineSummary: String,
        val summary: String,
        val positive: List<String>,
        val negative: List<String>,
        val watch: List<String>,
        val reasons: List<FactorReason>,
        val indices: Map<String, String> = emptyMap(),
        val sectorMoves: Map<String, String> = emptyMap(),
    )

    private fun historyRowsFor(target: DetailTarget): List<DetailHistoryRow> = when (target) {
        is DetailTarget.Overview -> {
            val todayDate = (target.item ?: briefing?.marketOverview)?.briefingDate
            overviewHistory.filter { it.briefingDate != todayDate }.map {
                DetailHistoryRow(it.briefingDate, it.briefingSession, it.generatedAt, "", it.sentiment, it.oneLineSummary, it.summary, it.positiveFactors, it.negativeFactors, it.watchIssues, it.reasons, it.indices, it.sectorMoves)
            }
        }
        is DetailTarget.Stock -> {
            val todayDate = (target.item ?: briefing?.stocks?.firstOrNull { it.ticker == target.ticker })?.briefingDate
            stockHistory.filter { it.ticker == target.ticker && it.briefingDate != todayDate }.map {
                DetailHistoryRow(it.briefingDate, it.briefingSession, it.generatedAt, target.ticker, it.sentiment, it.oneLineSummary, it.summary, it.positiveFactors, it.negativeFactors, it.watchIssues, it.reasons)
            }
        }
        is DetailTarget.Sector -> {
            val todayDate = (target.item ?: briefing?.sectorBriefings?.firstOrNull { it.sectorId == target.sectorId })?.briefingDate
            val sectorName = briefing?.sectors?.firstOrNull { it.id == target.sectorId }?.nameKo.orEmpty()
            sectorHistory.filter { it.sectorId == target.sectorId && it.briefingDate != todayDate }.map {
                DetailHistoryRow(it.briefingDate, it.briefingSession, it.generatedAt, sectorName, it.sentiment, it.oneLineSummary, it.summary, it.positiveFactors, it.negativeFactors, it.watchIssues, it.reasons)
            }
        }
    }

    private fun historyEmptyText(target: DetailTarget) = when (target) {
        is DetailTarget.Overview -> "이전 전체 시황 기록이 없습니다."
        is DetailTarget.Stock -> "이 종목의 이전 브리핑 기록이 없습니다."
        is DetailTarget.Sector -> "이 섹터의 이전 브리핑 기록이 없습니다."
    }

    private fun addOverviewDisclaimer(root: LinearLayout) {
        root.addSpace(10)
        root.addView(label("본 브리핑은 정보 제공 목적이며 투자 권유가 아닙니다.", SOFT_MUTED, Gravity.NO_GRAVITY).apply {
            textSize = 11f
        })
        root.addView(label("모든 투자에 대한 책임은 투자자 본인에게 있습니다.", SOFT_MUTED, Gravity.NO_GRAVITY).apply {
            textSize = 11f
        })
    }

    private fun historyDateTabs(dates: List<String>): View {
        val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        dates.forEach { date ->
            row.addView(historyDateButton(date, selectedHistoryDate == date))
            row.addHorizontalSpace(dp(7))
        }
        return HorizontalScrollView(this).apply {
            isHorizontalScrollBarEnabled = false
            addView(row)
        }
    }

    private fun historyDateButton(date: String, selected: Boolean) = TextView(this).apply {
        text = date.replace("-", ".")
        textSize = 13f
        gravity = Gravity.CENTER
        typeface = if (selected) android.graphics.Typeface.DEFAULT_BOLD else android.graphics.Typeface.DEFAULT
        setTextColor(if (selected) Color.WHITE else MUTED)
        setPadding(dp(13), dp(9), dp(13), dp(9))
        background = roundedStrokeBackground(
            if (selected) ACCENT else CARD,
            if (selected) ACCENT else LINE,
            dp(9).toFloat(),
        )
        setOnClickListener {
            selectedHistoryDate = date
            selectedHistorySession = null
            showHome()
        }
    }

    private fun historySessionItems(date: String, rows: List<DetailHistoryRow>): List<DetailSessionItem> {
        val byKey = rows.associateBy { it.briefingSession }
        val todayDay = date.split("-").getOrNull(2)?.toIntOrNull() ?: 0
        val marketDay = previousDayOfMonth(date)
        val base = listOf(
            "market_open" to "${marketDay}일 장시작",
            "intraday" to "${marketDay}일 장중",
            "market_close" to "${marketDay}일 장마감",
            "after_hours" to "${marketDay}~${todayDay}일 시간외",
        ).map { (key, labelText) ->
            val row = byKey[key]
            DetailSessionItem(
                key = key,
                label = labelText,
                available = row != null,
                scheduledAt = row?.generatedAt.orEmpty(),
                generatedAt = row?.generatedAt,
            )
        }
        val additional = byKey["additional"] ?: return base
        return base + DetailSessionItem(
            key = "additional",
            label = additionalSessionLabelForHistory(date, additional.generatedAt),
            available = true,
            scheduledAt = additional.generatedAt,
            generatedAt = additional.generatedAt,
        )
    }

    private fun historySessionTabs(sessions: List<DetailSessionItem>) = vertical {
        sessions.forEach { session ->
            addView(detailSessionButton(session, selectedHistorySession == session.key).apply {
                setOnClickListener {
                    if (!session.available) return@setOnClickListener
                    selectedHistorySession = session.key
                    showHome()
                }
            })
            addSpace(7)
        }
    }

    private fun previousDayOfMonth(date: String): Int {
        val parsed = runCatching { SimpleDateFormat("yyyy-MM-dd", Locale.US).parse(date) }.getOrNull() ?: return 0
        val cal = java.util.Calendar.getInstance(TimeZone.getTimeZone("UTC")).apply {
            time = parsed
            add(java.util.Calendar.DATE, -1)
        }
        return cal.get(java.util.Calendar.DAY_OF_MONTH)
    }

    private fun additionalSessionLabelForHistory(date: String, generatedAt: String): String {
        val parsed = runCatching { SimpleDateFormat("yyyy-MM-dd", Locale.US).parse(date) }.getOrNull() ?: return "추가"
        val cal = java.util.Calendar.getInstance(TimeZone.getTimeZone("UTC")).apply {
            time = parsed
            add(java.util.Calendar.DATE, -1)
            set(java.util.Calendar.HOUR_OF_DAY, 13)
            set(java.util.Calendar.MINUTE, 0)
            set(java.util.Calendar.SECOND, 0)
            set(java.util.Calendar.MILLISECOND, 0)
        }
        val generated = parseIsoMillis(generatedAt) ?: return "추가"
        val hours = (generated - cal.timeInMillis) / 3_600_000.0
        val sign = if (hours < 0) "-" else "+"
        return "장시작 $sign${"%.1f".format(Locale.US, kotlin.math.abs(hours))}h"
    }

    private fun detailBlockV2(
        titleText: String,
        subtitle: String,
        sentiment: String?,
        oneLineSummary: String?,
        summary: String,
        positive: List<String>,
        negative: List<String>,
        watch: List<String>,
        reasons: List<FactorReason>,
        indices: Map<String, String> = emptyMap(),
        sectorMoves: Map<String, String> = emptyMap(),
        indexColumns: Int = 2,
        sectorEtfs: List<String> = emptyList(),
        actions: LinearLayout.() -> Unit = {},
    ) = card {
        val head = horizontal()
        head.addWeighted(title(titleText, 18, TEXT, Gravity.NO_GRAVITY))
        sentiment?.let { head.addView(sentimentPill(it)) }
        addView(head)
        if (subtitle.isNotBlank()) addView(label(subtitle, MUTED, Gravity.NO_GRAVITY).apply { textSize = 13f })
        if (sectorEtfs.isNotEmpty()) {
            addSpace(10)
            addView(sectorEtfRow(sectorEtfs))
        }
        if (indices.isNotEmpty()) {
            addSpace(16)
            addView(indexGrid(indices, columns = indexColumns))
        }
        if (sectorMoves.isNotEmpty()) {
            addSpace(12)
            addView(indexGrid(sectorMoves, compact = true, columns = indexColumns))
        }
        cleanDisplayText(oneLineSummary)?.let {
            addSpace(14)
            addView(oneLineSummaryLabel(it))
        }
        if (summary.isNotBlank()) {
            addSpace(if (cleanDisplayText(oneLineSummary) == null) 14 else 2)
            addView(label(summary, MUTED, Gravity.NO_GRAVITY).apply { textSize = 13.5f })
        }
        addFactorBoxes(positive, negative, watch)
        addReasonsV2(reasons)
        val actionRow = vertical { actions() }
        if (actionRow.childCount > 0) {
            addSpace(18)
            addView(actionRow)
        }
    }

    private fun representativeSectorEtfs(nameEn: String?): List<String> = when (nameEn) {
        "Semiconductors & AI" -> listOf("SOXX", "SMH", "BOTZ")
        "Technology & Software" -> listOf("XLK", "VGT", "IGV")
        "Media & Internet" -> listOf("XLC", "VOX", "FDN")
        "Consumer & Retail" -> listOf("XLY", "XLP", "XRT")
        "Automobiles" -> listOf("CARZ", "DRIV", "IDRV")
        "Financials" -> listOf("XLF", "VFH", "KRE")
        "Health Care" -> listOf("XLV", "VHT", "XBI")
        "Energy" -> listOf("XLE", "VDE", "OIH")
        "Industrials" -> listOf("XLI", "VIS", "IYT")
        "Telecommunications" -> listOf("XLC", "VOX", "IYZ")
        "Real Estate" -> listOf("XLRE", "VNQ", "IYR")
        "Materials" -> listOf("XLB", "VAW", "GDX")
        "Utilities" -> listOf("XLU", "VPU", "FUTY")
        else -> emptyList()
    }

    private fun sectorEtfRow(etfs: List<String>) = horizontal().apply {
        gravity = Gravity.CENTER_VERTICAL
        setPadding(0, 0, 0, dp(14))
        addView(label("대표 ETF", SOFT_MUTED, Gravity.NO_GRAVITY).apply {
            textSize = 11.5f
            typeface = android.graphics.Typeface.DEFAULT_BOLD
        })
        addHorizontalSpace(dp(10))
        etfs.forEach { ticker ->
            addView(label(ticker, ACCENT, Gravity.CENTER).apply {
                textSize = 11.5f
                typeface = android.graphics.Typeface.DEFAULT_BOLD
                letterSpacing = 0.02f
                setPadding(dp(8), dp(4), dp(8), dp(4))
                background = roundedStrokeBackground(ACCENT_BG, ACCENT_LINE, dp(999).toFloat())
            })
            addHorizontalSpace(dp(6))
        }
    }

    private fun oneLineSummaryLabel(value: String) = label("한 줄 요약: $value", TEXT, Gravity.NO_GRAVITY).apply {
        textSize = 13.5f
        setLineSpacing(2f, 1.18f)
        text = SpannableString(text).apply {
            setSpan(
                StyleSpan(android.graphics.Typeface.BOLD),
                0,
                "한 줄 요약:".length,
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE,
            )
        }
    }

    private fun indexGrid(values: Map<String, String>, compact: Boolean = false, columns: Int = 2) = vertical {
        val columnCount = columns.coerceAtLeast(1)
        values.entries.chunked(columnCount).forEach { rowItems ->
            val row = horizontal()
            rowItems.forEach { (name, value) ->
                row.addWeighted(indexCard(name, value, compact))
            }
            repeat(columnCount - rowItems.size) { row.addWeighted(View(this@MainActivity)) }
            addView(row)
            addSpace(8)
        }
    }

    private fun indexCard(name: String, value: String, compact: Boolean) = vertical {
        setPadding(dp(14), dp(12), dp(14), dp(12))
        background = roundedStrokeBackground(if (isDarkMode) Color.rgb(22, 23, 30) else Color.rgb(249, 250, 252), LINE, dp(10).toFloat())
        addView(label(name, MUTED, Gravity.NO_GRAVITY).apply { textSize = 12f })
        addView(title(value, if (compact) 13 else 18, TEXT, Gravity.NO_GRAVITY))
    }

    private fun LinearLayout.addReasonsV2(reasons: List<FactorReason>) {
        if (reasons.isEmpty()) return
        addSpace(14)
        reasons.forEach { reason ->
            val text = "🔗 ${reason.displayText}"
            addView(label(text, ACCENT, Gravity.NO_GRAVITY).apply {
                textSize = 12f
                if (reason.sourceUrl.isNotBlank()) setOnClickListener {
                    runCatching { startActivity(android.content.Intent(android.content.Intent.ACTION_VIEW, Uri.parse(reason.sourceUrl))) }
                }
            })
        }
    }

    private fun detailBlock(
        titleText: String,
        subtitle: String,
        sentiment: String?,
        summary: String,
        positive: List<String>,
        negative: List<String>,
        watch: List<String>,
        reasons: List<FactorReason>,
        indices: Map<String, String> = emptyMap(),
        actions: LinearLayout.() -> Unit = {},
    ) = card {
        val head = horizontal()
        head.addWeighted(vertical {
            addView(title(titleText, 18, TEXT, Gravity.NO_GRAVITY))
            if (subtitle.isNotBlank()) addView(label(subtitle, MUTED, Gravity.NO_GRAVITY))
        })
        sentiment?.let { head.addView(sentimentPill(it)) }
        addView(head)
        if (indices.isNotEmpty()) {
            addSpace(14)
            indices.forEach { (name, value) -> addView(metricRow(name, value)) }
        }
        if (summary.isNotBlank()) {
            addSpace(12)
            addView(label(summary, MUTED, Gravity.NO_GRAVITY))
        }
        addFactorBoxes(positive, negative, watch)
        addReasons(reasons)
        val actionRow = vertical { actions() }
        if (actionRow.childCount > 0) {
            addSpace(18)
            addView(actionRow)
        }
    }

    private fun LinearLayout.addFactorBoxes(positive: List<String>, negative: List<String>, watch: List<String>) {
        if (positive.isEmpty() && negative.isEmpty() && watch.isEmpty()) return
        addSpace(14)
        val boxes = listOfNotNull(
            positive.takeIf { it.isNotEmpty() }?.let { factorBox("긍정 요인", it, FactorTone.Positive) },
            negative.takeIf { it.isNotEmpty() }?.let { factorBox("부정 요인", it, FactorTone.Negative) },
            watch.takeIf { it.isNotEmpty() }?.let { factorBox("확인할 것", it, FactorTone.Neutral) },
        )
        boxes.forEachIndexed { index, view ->
            if (index > 0) addSpace(30)
            addView(view)
        }
    }

    private fun factorBox(titleText: String, items: List<String>, tone: FactorTone) = vertical {
        setPadding(dp(12), dp(10), dp(12), dp(10))
        background = roundedStrokeBackground(factorBg(tone), factorBorder(tone), dp(10).toFloat())
        addView(title(titleText, 13, factorText(tone), Gravity.NO_GRAVITY))
        items.forEach { addView(label(it, factorText(tone), Gravity.NO_GRAVITY).apply { textSize = 12.5f }) }
    }

    private enum class FactorTone { Positive, Negative, Neutral }

    private fun lensView(target: LensTarget): View {
        val root = scrollColumn()
        val sectorCode = sectorCodeFor(target)
        var lens = lensFor(target)
        val catByCode = categories.associateBy { it.code }
        val presetByCode = presets.associateBy { it.code }
        val rec = LensRules.forSectorCode(sectorCode)

        fun persist(next: LensSetting) {
            lens = next
            saveLens(target, next)
            showHome()
        }

        root.addView(textMutedBackButton("< 오늘의 브리핑으로") {
            lensTarget = null
            showHome()
        })
        root.addSpace(12)
        root.addView(lensCompactHeader(target) {
            saveLens(target, LensRules.blank(lens.note))
            toast("렌즈 설정을 초기화했습니다.")
            showHome()
        })
        root.addSpace(14)

        root.addView(lensRecommendationBox(rec, catByCode, presetByCode, lens.whyKey) { key ->
            val chosen = if (key == "alt") rec.alt else rec.primary
            persist(LensSetting(chosen.cats, chosen.preset, "standard", lens.note, key))
        })

        root.addView(lensCategorySectionV2(lens) { code ->
            val next = if (code in lens.categoryCodes) lens.categoryCodes - code else lens.categoryCodes + code
            persist(lens.copy(categoryCodes = next, whyKey = null))
        })

        root.addView(card {
            addView(stepHeader("2. 분석 성향", "하나 선택"))
            if (presets.isEmpty()) {
                addView(label("분석 성향을 불러오지 못했습니다.", MUTED, Gravity.NO_GRAVITY))
            } else {
                presets.forEach { preset ->
                    addView(lensPresetOptionV2(preset, preset.code == lens.presetCode) {
                        persist(lens.copy(presetCode = preset.code, whyKey = null))
                    })
                    addSpace(8)
                }
            }
        })

        root.addView(card {
            addView(stepHeader("3. 심층도", "분석 분량"))
            val depths = listOf("요약" to "brief", "표준" to "standard", "심층" to "deep")
            addView(chips(depths.map { it.first }, depths.indexOfFirst { it.second == lens.depth }.coerceAtLeast(1)) { index ->
                persist(lens.copy(depth = depths[index].second, whyKey = null))
            })
        })

        val note = input("참고 리포트 또는 메모").apply { edit().setText(lens.note) }
        root.addView(card {
            addView(stepHeader("참고 리포트 / 메모", "선택"))
            addView(label("증권사 리포트 요약, 실적 메모, 개인 체크포인트를 붙여 넣으면 프롬프트에 반영됩니다.", MUTED, Gravity.NO_GRAVITY))
            addView(note)
            note.edit().addTextChangedListener(SimpleWatcher {
                lens = lens.copy(note = it)
            })
        })

        root.addView(lensPreviewCard(lens, catByCode, presetByCode, lensPreviewExpanded) {
            lensPreviewExpanded = !lensPreviewExpanded
            showHome()
        })
        root.addView(primaryButton("저장하기").apply {
            setOnClickListener {
                saveLens(target, lens)
                toast("렌즈 설정을 저장했습니다.")
                showHome()
            }
        })
        root.addView(label("렌즈 설정은 현재 기기에 저장됩니다. 서버 저장 API가 준비되면 같은 구조로 동기화할 수 있습니다.", MUTED, Gravity.NO_GRAVITY))
        return root.parent as View
    }

    private fun lensTopActionCard(
        onReset: () -> Unit,
        onRecommend: () -> Unit,
        onSave: () -> Unit,
    ) = card {
        val row = horizontal()
        row.addWeighted(detailActionButton("초기화", primary = false, onReset))
        row.addHorizontalSpace(dp(8))
        row.addWeighted(detailActionButton("추천", primary = false, onRecommend))
        row.addHorizontalSpace(dp(8))
        row.addWeighted(detailActionButton("저장", primary = true, onSave))
        addView(row)
    }

    private fun lensSubjectCardV2(target: LensTarget) = card {
        val data = briefing
        when (target) {
            is LensTarget.Stock -> {
                val stock = data?.allStocks?.firstOrNull { it.ticker == target.ticker } ?: extraStocks[target.ticker]
                addView(title(target.ticker, 20, TEXT, Gravity.NO_GRAVITY))
                val subtitle = listOf(
                    cleanDisplayText(stock?.displayName),
                    cleanDisplayText(stock?.sectorName),
                    cleanDisplayText(stock?.exchange)?.uppercase(),
                ).filterNotNull().joinToString(" · ")
                addView(label(subtitle.ifBlank { "종목 정보를 불러오는 중입니다." }, MUTED, Gravity.NO_GRAVITY))
            }
            is LensTarget.Sector -> {
                val sector = data?.sectors?.firstOrNull { it.id == target.sectorId }
                addView(title(sector?.nameKo ?: "섹터 #${target.sectorId}", 20, TEXT, Gravity.NO_GRAVITY))
                if (!sector?.nameEn.isNullOrBlank()) addView(label(sector!!.nameEn, MUTED, Gravity.NO_GRAVITY))
            }
        }
        addSpace(10)
        addView(label("웹 서비스의 분석 렌즈 설정 화면과 동일하게 카테고리, 성향, 심층도, 메모를 조합합니다.", MUTED, Gravity.NO_GRAVITY))
    }

    private fun lensCompactHeader(target: LensTarget, onReset: () -> Unit) = horizontal().apply {
        val data = briefing
        addWeighted(vertical {
            when (target) {
                is LensTarget.Stock -> {
                    val stock = data?.allStocks?.firstOrNull { it.ticker == target.ticker } ?: extraStocks[target.ticker]
                    val sector = cleanDisplayText(stock?.sectorName) ?: "섹터 미정"
                    val exchange = cleanDisplayText(stock?.exchange)?.uppercase() ?: "거래소 미정"
                    addView(title(target.ticker, 30, TEXT, Gravity.NO_GRAVITY))
                    addView(label("$sector · $exchange", MUTED, Gravity.NO_GRAVITY))
                }
                is LensTarget.Sector -> {
                    val sector = data?.sectors?.firstOrNull { it.id == target.sectorId }
                    addView(title(sector?.nameKo ?: "섹터 #${target.sectorId}", 30, TEXT, Gravity.NO_GRAVITY))
                }
            }
        })
        addView(iconOnlyActionButton("↺", onReset))
    }

    private fun lensRecommendationBox(
        rec: LensRecommendationPair,
        catByCode: Map<String, AnalysisCategory>,
        presetByCode: Map<String, AnalysisPreset>,
        selectedKey: String?,
        onApply: (String) -> Unit,
    ): MaterialCardView {
        val box = MaterialCardView(this).apply {
            radius = dp(14).toFloat()
            strokeColor = ACCENT_LINE
            strokeWidth = 1
            setCardBackgroundColor(ACCENT_BG)
            useCompatPadding = true
        }
        val inner = vertical {
            setPadding(dp(16), dp(14), dp(16), dp(14))
            addView(label("★ 추천 렌즈", ACCENT, Gravity.NO_GRAVITY).apply {
                textSize = 12f
                typeface = android.graphics.Typeface.DEFAULT_BOLD
            })
            addSpace(10)
            val row = horizontal()
            val primaryChip = lensRecommendationChip("기본 추천", rec.primary, catByCode, presetByCode, accentTitle = true, selected = selectedKey == "primary") {
                onApply("primary")
            }
            val altChip = lensRecommendationChip("대안 추천", rec.alt, catByCode, presetByCode, accentTitle = false, selected = selectedKey == "alt") {
                onApply("alt")
            }
            row.addView(primaryChip, LinearLayout.LayoutParams(0, -2, 1f))
            row.addHorizontalSpace(dp(8))
            row.addView(altChip, LinearLayout.LayoutParams(0, -2, 1f))
            addView(row)
            selectedKey?.let { key ->
                val chosen = if (key == "alt") rec.alt else rec.primary
                addSpace(12)
                addView(lensRecommendationWhyBox(key, chosen.why))
            }
            row.post {
                val maxHeight = maxOf(primaryChip.height, altChip.height)
                if (maxHeight > 0) {
                    primaryChip.layoutParams = primaryChip.layoutParams.apply { height = maxHeight }
                    altChip.layoutParams = altChip.layoutParams.apply { height = maxHeight }
                }
            }
        }
        box.addView(inner)
        return box
    }

    private fun lensRecommendationWhyBox(key: String, why: String) = vertical {
        setPadding(0, 0, 0, 0)
        addView(label("ⓘ 왜 ${if (key == "alt") "대안 추천" else "기본 추천"}인가요?", ACCENT, Gravity.NO_GRAVITY).apply {
            textSize = 12f
            typeface = android.graphics.Typeface.DEFAULT_BOLD
        })
        addSpace(8)
        addView(label(why, TEXT, Gravity.NO_GRAVITY).apply { textSize = 12.5f })
    }

    private fun lensRecommendationChip(
        titleText: String,
        recommendation: LensRecommendation,
        catByCode: Map<String, AnalysisCategory>,
        presetByCode: Map<String, AnalysisPreset>,
        accentTitle: Boolean,
        selected: Boolean,
        onClick: () -> Unit,
    ) = vertical {
        setPadding(dp(13), dp(10), dp(13), dp(10))
        background = recommendationChipBackground(selected)
        setOnClickListener { onClick() }
        addView(title(titleText, 13, if (selected || accentTitle) ACCENT else MUTED, Gravity.NO_GRAVITY))
        addSpace(3)
        val cats = recommendation.cats.joinToString(" · ") { catByCode[it]?.nameKo ?: it }
        val preset = presetByCode[recommendation.preset]?.nameKo ?: recommendation.preset
        addView(label("$cats + $preset", TEXT, Gravity.NO_GRAVITY).apply { textSize = 12.5f })
    }

    private fun recommendationSubjectText(target: LensTarget): String {
        val data = briefing
        return when (target) {
            is LensTarget.Stock -> {
                val stock = data?.allStocks?.firstOrNull { it.ticker == target.ticker } ?: extraStocks[target.ticker]
                val name = cleanDisplayText(stock?.nameKo) ?: cleanDisplayText(stock?.nameEn) ?: target.ticker
                val sector = cleanDisplayText(stock?.sectorName) ?: "섹터 미정"
                "$name($sector)"
            }
            is LensTarget.Sector -> {
                val sector = data?.sectors?.firstOrNull { it.id == target.sectorId }
                "${sector?.nameKo ?: "섹터 #${target.sectorId}"} 섹터"
            }
        }
    }

    private fun recommendationChipBackground(selected: Boolean) = GradientDrawable().apply {
        setColor(CARD)
        cornerRadius = dp(12).toFloat()
        setStroke(dp(if (selected) 2 else 1), if (selected) ACCENT else ACCENT_LINE)
    }

    private fun lensCategorySectionV2(lens: LensSetting, onToggle: (String) -> Unit) = card {
        addView(stepHeader("1. 분석 카테고리", "그룹별 + 로 추가"))
        if (categories.isEmpty()) {
            addView(label("분석 카테고리를 불러오지 못했습니다.", MUTED, Gravity.NO_GRAVITY))
            return@card
        }
        lensCategoryGroups().forEach { (type, items) ->
            addView(lensCategoryGroupV2(type, items, lens, onToggle))
            addSpace(10)
        }
    }

    private fun lensCategoryGroupV2(
        type: String,
        items: List<AnalysisCategory>,
        lens: LensSetting,
        onToggle: (String) -> Unit,
    ) = vertical {
        val groupKey = type
        addView(title(categoryTypeLabel(type), 14, TEXT, Gravity.NO_GRAVITY))
        val selected = items.filter { it.code in lens.categoryCodes }
        val group = ChipGroup(this@MainActivity).apply { isSingleSelection = false }
        fun addCategoryChip(cat: AnalysisCategory) {
            group.addView(Chip(this@MainActivity).apply {
                text = cat.nameKo.ifBlank { cat.code }
                isCheckable = true
                isChecked = cat.code in lens.categoryCodes
                isCheckedIconVisible = false
                setTextColor(Color.WHITE)
                chipBackgroundColor = ColorStateList.valueOf(ACCENT)
                chipStrokeColor = ColorStateList.valueOf(ACCENT)
                chipStrokeWidth = dp(1).toFloat()
                setOnClickListener { onToggle(cat.code) }
            })
        }
        if (selected.isEmpty()) {
            group.addView(label("선택된 항목이 없습니다.", MUTED, Gravity.NO_GRAVITY).apply {
                textSize = 12.5f
                setPadding(0, dp(6), dp(6), dp(6))
            })
        } else {
            selected.forEach(::addCategoryChip)
        }
        group.addView(Chip(this@MainActivity).apply {
            val open = groupKey in lensCategorySearchOpen
            text = "+"
            textSize = 16f
            minWidth = dp(38)
            isCheckable = false
            isCheckedIconVisible = false
            setTextColor(ACCENT)
            chipBackgroundColor = ColorStateList.valueOf(if (open) ACCENT_BG else CARD)
            chipStrokeColor = ColorStateList.valueOf(if (open) ACCENT else ACCENT_LINE)
            chipStrokeWidth = dp(1).toFloat()
            setOnClickListener {
                lensCategorySearchOpen = if (open) emptySet() else setOf(groupKey)
                lensCategorySearchQuery = if (open) {
                    lensCategorySearchQuery - groupKey
                } else {
                    mapOf(groupKey to "")
                }
                showHome()
            }
        })
        addView(group)

        if (groupKey in lensCategorySearchOpen) {
            addSpace(6)
            addView(lensCategorySearchBox(groupKey, categoryTypeLabel(type), items, lens, onToggle))
        }
    }

    private fun lensCategorySearchBox(
        groupKey: String,
        labelText: String,
        items: List<AnalysisCategory>,
        lens: LensSetting,
        onToggle: (String) -> Unit,
    ) = vertical {
        val query = lensCategorySearchQuery[groupKey].orEmpty()
        val searchRow = horizontal()
        val search = input("$labelText 검색").apply { edit().setText(query) }
        searchRow.addWeighted(search)
        searchRow.addHorizontalSpace(dp(8))
        searchRow.addView(rowActionButton("×", danger = false) {
            lensCategorySearchOpen = lensCategorySearchOpen - groupKey
            lensCategorySearchQuery = lensCategorySearchQuery - groupKey
            showHome()
        })
        addView(searchRow)

        val results = ChipGroup(this@MainActivity).apply { isSingleSelection = false }
        fun render(queryText: String) {
            results.removeAllViews()
            val available = items.filter { it.code !in lens.categoryCodes }
            val matches = if (queryText.isBlank()) available else available
                .filter { it.code.contains(queryText, true) || it.nameKo.contains(queryText, true) || it.nameEn.contains(queryText, true) }
            when {
                available.isEmpty() -> results.addView(disabledCategoryChip("모든 항목을 추가했습니다."))
                matches.isEmpty() -> results.addView(disabledCategoryChip("검색 결과가 없습니다."))
                else -> matches.take(10).forEach { cat ->
                    results.addView(Chip(this@MainActivity).apply {
                        text = cat.nameKo.ifBlank { cat.code }
                        setTextColor(TEXT)
                        chipBackgroundColor = ColorStateList.valueOf(CARD)
                        chipStrokeColor = ColorStateList.valueOf(LINE)
                        chipStrokeWidth = dp(1).toFloat()
                        setOnClickListener {
                            lensCategorySearchQuery = lensCategorySearchQuery + (groupKey to "")
                            onToggle(cat.code)
                        }
                    })
                }
            }
        }
        search.edit().addTextChangedListener(SimpleWatcher {
            lensCategorySearchQuery = lensCategorySearchQuery + (groupKey to it)
            render(it)
        })
        render(query)
        addView(results)
    }

    private fun disabledCategoryChip(textValue: String) = Chip(this).apply {
        text = textValue
        isEnabled = false
        setTextColor(MUTED)
        chipBackgroundColor = ColorStateList.valueOf(CARD)
        chipStrokeColor = ColorStateList.valueOf(LINE)
        chipStrokeWidth = dp(1).toFloat()
    }

    private fun lensPresetOptionV2(preset: AnalysisPreset, selected: Boolean, onClick: () -> Unit) = vertical {
        setPadding(dp(12), dp(10), dp(12), dp(10))
        background = roundedStrokeBackground(if (selected) ACCENT_BG else CARD, if (selected) ACCENT_LINE else LINE, dp(8).toFloat())
        setOnClickListener { onClick() }
        val row = horizontal()
        row.addWeighted(title(preset.nameKo, 16, if (selected) ACCENT else TEXT, Gravity.NO_GRAVITY))
        if (selected) row.addView(checkCircle())
        addView(row)
        if (preset.personaText.isNotBlank()) addView(label(preset.personaText, MUTED, Gravity.NO_GRAVITY).apply { textSize = 12.5f })
    }

    private fun iconOnlyActionButton(symbol: String, onClick: () -> Unit) = TextView(this).apply {
        text = symbol
        textSize = 24f
        gravity = Gravity.CENTER
        typeface = android.graphics.Typeface.DEFAULT_BOLD
        setTextColor(ACCENT)
        minWidth = dp(42)
        minHeight = dp(42)
        setPadding(dp(8), 0, dp(8), dp(2))
        background = null
        setOnClickListener { onClick() }
    }

    private fun iconOnlyMutedActionButton(symbol: String, onClick: () -> Unit) = TextView(this).apply {
        text = symbol
        textSize = 24f
        gravity = Gravity.CENTER
        typeface = android.graphics.Typeface.DEFAULT_BOLD
        setTextColor(MUTED)
        minWidth = dp(42)
        minHeight = dp(42)
        setPadding(dp(8), 0, dp(8), dp(2))
        background = null
        setOnClickListener { onClick() }
    }

    private fun inlineRefreshActionButton(onClick: () -> Unit) = TextView(this).apply {
        text = "↻ 새로고침"
        textSize = 11f
        gravity = Gravity.CENTER
        typeface = android.graphics.Typeface.DEFAULT_BOLD
        setTextColor(MUTED)
        minHeight = dp(22)
        setPadding(dp(4), 0, 0, 0)
        background = null
        setOnClickListener { onClick() }
    }

    private fun briefingSectionHeader(textValue: String, showSearch: Boolean) = horizontal().apply {
        addWeighted(sectionTitle(textValue))
        if (showSearch) addView(briefingSearchIconButton(briefingSearchOpen) {
            briefingSearchOpen = !briefingSearchOpen
            showHome()
        })
    }

    private fun briefingSearchIconButton(selected: Boolean, onClick: () -> Unit) = TextView(this).apply {
        text = "⌕"
        textSize = 24f
        gravity = Gravity.CENTER
        typeface = android.graphics.Typeface.DEFAULT_BOLD
        setTextColor(if (selected) ACCENT else MUTED)
        minWidth = dp(42)
        minHeight = dp(42)
        setPadding(dp(8), 0, dp(8), dp(2))
        background = null
        setOnClickListener { onClick() }
    }

    private fun checkCircle() = TextView(this).apply {
        text = "✓"
        textSize = 9f
        gravity = Gravity.CENTER
        typeface = android.graphics.Typeface.DEFAULT_BOLD
        setTextColor(Color.WHITE)
        background = GradientDrawable().apply {
            shape = GradientDrawable.OVAL
            setColor(ACCENT)
        }
        layoutParams = LinearLayout.LayoutParams(dp(19), dp(19))
    }

    private fun lensPreviewCard(
        lens: LensSetting,
        catByCode: Map<String, AnalysisCategory>,
        presetByCode: Map<String, AnalysisPreset>,
        expanded: Boolean,
        onToggle: () -> Unit,
    ) = card(ACCENT_BG) {
        setOnClickListener { onToggle() }
        val row = horizontal()
        row.addWeighted(label("</> 조립된 렌즈 프롬프트", MUTED, Gravity.NO_GRAVITY).apply {
            textSize = 12f
            typeface = android.graphics.Typeface.DEFAULT_BOLD
        })
        row.addView(label(if (expanded) "접기" else "펼치기", ACCENT, Gravity.RIGHT).apply {
            textSize = 13f
            typeface = android.graphics.Typeface.DEFAULT_BOLD
        })
        addView(row)
        if (expanded) {
            addSpace(10)
            addView(label("", TEXT, Gravity.NO_GRAVITY).apply {
                text = buildLensPreviewSpannable(lens, catByCode, presetByCode)
            })
            addSpace(10)
            addView(label("▣ 근거 인용 필수 · 매매 지시 금지", MUTED, Gravity.NO_GRAVITY).apply { textSize = 11f })
        }
    }

    private fun buildLensPreviewSpannable(
        lens: LensSetting,
        catByCode: Map<String, AnalysisCategory>,
        presetByCode: Map<String, AnalysisPreset>,
    ): SpannableString {
        val preset = lens.presetCode?.let { presetByCode[it] }
        if (lens.categoryCodes.isEmpty() || preset == null) {
            return SpannableString("카테고리와 성향을 선택하면\n프롬프트가 여기에 조립됩니다.")
        }
        val catText = lens.categoryCodes.joinToString(", ") { catByCode[it]?.nameKo ?: it }
        val depth = when (lens.depth) {
            "brief" -> "요약"
            "deep" -> "심층"
            else -> "표준"
        }
        val noteLine = if (lens.note.isNotBlank()) "\n참고 리포트/메모를 함께 반영해줘." else ""
        val categoryPart = "[$catText]"
        val presetPart = preset.nameKo
        val depthPart = depth
        val raw = "이 문서를 $categoryPart 관점에서\n$presetPart 성향(${preset.personaText})으로\n$depthPart 분석해줘.$noteLine"
        return SpannableString(raw).apply {
            highlight(raw, categoryPart)
            highlight(raw, presetPart)
            highlight(raw, depthPart)
        }
    }

    private fun SpannableString.highlight(raw: String, target: String) {
        val start = raw.indexOf(target)
        if (start < 0) return
        val end = start + target.length
        setSpan(ForegroundColorSpan(ACCENT), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
        setSpan(StyleSpan(android.graphics.Typeface.BOLD), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
    }

    private fun stepHeader(text: String, hint: String) = horizontal().apply {
        val match = Regex("""^(\d+)\.\s*(.+)$""").find(text)
        if (match != null) {
            addView(stepNumberBadge(match.groupValues[1]))
            addView(View(context), LinearLayout.LayoutParams(dp(9), 1))
            addWeighted(title(match.groupValues[2], 16, TEXT, Gravity.NO_GRAVITY))
        } else {
            addWeighted(title(text, 17, TEXT, Gravity.NO_GRAVITY))
        }
        if (hint.isNotBlank()) addView(label(hint, MUTED, Gravity.RIGHT).apply { textSize = 12f })
    }

    private fun stepNumberBadge(value: String) = TextView(this).apply {
        text = value
        textSize = 12f
        typeface = android.graphics.Typeface.DEFAULT_BOLD
        gravity = Gravity.CENTER
        setTextColor(ACCENT)
        background = roundedStrokeBackground(ACCENT_BG, ACCENT_BG, dp(7).toFloat())
        layoutParams = LinearLayout.LayoutParams(dp(22), dp(22))
    }

    private fun categoryTypeLabel(type: String) = when (type) {
        "index" -> "지수"
        "indicator" -> "지표"
        "sector_theme" -> "섹터/테마"
        "sector" -> "섹터"
        "theme" -> "테마"
        else -> type
    }

    private fun lensCategoryGroups(): List<Pair<String, List<AnalysisCategory>>> {
        val grouped = categories.groupBy { if (it.type == "sector" || it.type == "theme") "sector_theme" else it.type }
        val order = listOf("index", "indicator", "sector_theme")
        return order.mapNotNull { key -> grouped[key]?.let { key to it } } +
            grouped.filterKeys { it !in order }.map { it.key to it.value }
    }

    private fun lensOptionBg() = if (isDarkMode) Color.rgb(35, 35, 64) else Color.rgb(248, 248, 255)

    private fun legacyLensView(target: LensTarget): View {
        val root = scrollColumn()
        val sectorCode = sectorCodeFor(target)
        var lens = lensFor(target)
        val catByCode = categories.associateBy { it.code }
        val presetByCode = presets.associateBy { it.code }
        val rec = LensRules.forSectorCode(sectorCode)
        root.addView(textBackButton("< 돌아가기") {
            lensTarget = null
            showHome()
        })
        root.addSpace(12)
        root.addView(pageTitle(lensTitle(target), "분석 카테고리와 성향을 앱에 저장합니다."))
        root.addView(lensSubjectCard(target))
        root.addSpace(14)
        root.addView(card {
            addView(sectionTitle("추천 렌즈"))
            addView(label("종목/섹터 특성에 맞는 기본 조합을 바로 적용할 수 있습니다.", MUTED, Gravity.NO_GRAVITY))
            addSpace(8)
            lens.whyKey?.let { key ->
                val why = if (key == "alt") rec.alt.why else rec.primary.why
                addView(statusCard("왜 ${if (key == "alt") "대안 추천" else "기본 추천"}인가요?\n$why", ACCENT))
            } ?: addView(label("추천을 선택하면 선택 이유를 함께 보여줍니다.", MUTED, Gravity.NO_GRAVITY))
            addSpace(10)
            addView(recommendationOption("기본 추천", rec.primary, catByCode, presetByCode, lens.whyKey == "primary") {
                lens = LensSetting(rec.primary.cats, rec.primary.preset, "standard", lens.note, "primary")
                saveLens(target, lens)
                toast("기본 추천을 적용했습니다.")
                showHome()
            })
            addView(recommendationOption("대안 추천", rec.alt, catByCode, presetByCode, lens.whyKey == "alt") {
                lens = LensSetting(rec.alt.cats, rec.alt.preset, "standard", lens.note, "alt")
                saveLens(target, lens)
                toast("대안 추천을 적용했습니다.")
                showHome()
            })
            val row = horizontal()
            row.addWeighted(smallButton("추천 다시 적용").apply {
                setOnClickListener {
                    val chosen = if (lens.whyKey == "alt") rec.alt else rec.primary
                    lens = LensSetting(chosen.cats, chosen.preset, "standard", lens.note, lens.whyKey ?: "primary")
                    saveLens(target, lens)
                    toast("추천 렌즈를 다시 적용했습니다.")
                    showHome()
                }
            })
            addSpace(8)
            addView(row)
            addSpace(8)
            addView(smallButton("초기화").apply {
                setOnClickListener {
                    saveLens(target, LensRules.blank(lens.note))
                    toast("렌즈를 초기화했습니다.")
                    showHome()
                }
            })
        })
        root.addView(lensCategorySection("분석 카테고리", lens) { code ->
            val next = if (code in lens.categoryCodes) lens.categoryCodes - code else lens.categoryCodes + code
            saveLens(target, lens.copy(categoryCodes = next, whyKey = null))
            showHome()
        })
        root.addView(card {
            addView(sectionTitle("분석 성향"))
            if (presets.isEmpty()) {
                addView(label("분석 성향을 불러오지 못했습니다.", MUTED, Gravity.NO_GRAVITY))
            } else {
                presets.forEach { preset ->
                    addView(presetOption(preset, preset.code == lens.presetCode) {
                        saveLens(target, lens.copy(presetCode = preset.code, whyKey = null))
                        showHome()
                    })
                }
            }
        })
        root.addView(card {
            addView(sectionTitle("깊이"))
            val depths = listOf("요약" to "brief", "표준" to "standard", "심층" to "deep")
            addView(chips(depths.map { it.first }, depths.indexOfFirst { it.second == lens.depth }.coerceAtLeast(1)) { index ->
                saveLens(target, lens.copy(depth = depths[index].second, whyKey = null))
                showHome()
            })
        })
        val note = input("참고 리포트 또는 메모").apply { edit().setText(lens.note) }
        root.addView(card {
            addView(sectionTitle("메모"))
            addView(label("증권사 리포트나 메모를 붙여넣으면 프롬프트에 함께 반영됩니다.", MUTED, Gravity.NO_GRAVITY))
            addView(note)
        })
        root.addView(card(ACCENT_DARK) {
            addView(title("프롬프트 미리보기", 17, Color.WHITE, Gravity.NO_GRAVITY))
            val catText = lens.categoryCodes.map { catByCode[it]?.nameKo ?: it }.joinToString(", ").ifBlank { "카테고리 미선택" }
            val preset = presetByCode[lens.presetCode]?.nameKo ?: "성향 미선택"
            val persona = presetByCode[lens.presetCode]?.personaText.orEmpty()
            val depth = when (lens.depth) {
                "brief" -> "요약"
                "deep" -> "심층"
                else -> "표준"
            }
            addSpace(8)
            addView(label(
                "이 문서를 [$catText] 관점에서,\n$preset 성향${if (persona.isNotBlank()) "($persona)" else ""}으로\n$depth 분석해줘.${if (lens.note.isNotBlank()) "\n참고 리포트/메모를 함께 반영해줘." else ""}",
                ACCENT_BG,
                Gravity.NO_GRAVITY,
            ))
            addSpace(10)
            addView(label("근거 인용 필수 · 매매 지시 금지", ACCENT_LINE, Gravity.NO_GRAVITY))
        })
        root.addView(primaryButton("렌즈 설정 저장").apply {
            setOnClickListener {
                saveLens(target, lens.copy(note = note.value()))
                toast("렌즈 설정을 저장했습니다.")
                showHome()
            }
        })
        root.addView(label("저장된 렌즈는 마이페이지와 브리핑 상세의 분석 렌즈에서 다시 확인할 수 있습니다.", MUTED, Gravity.NO_GRAVITY))
        return root.parent as View
    }

    private fun lensSubjectCard(target: LensTarget) = card {
        val data = briefing
        when (target) {
            is LensTarget.Stock -> {
                val stock = data?.allStocks?.firstOrNull { it.ticker == target.ticker } ?: extraStocks[target.ticker]
                addView(title(target.ticker, 18, TEXT, Gravity.NO_GRAVITY))
                addView(label(listOf(stock?.displayName, stock?.sectorName, stock?.exchange).filterNotNull().filter { it.isNotBlank() }.joinToString(" · ").ifBlank { "종목 정보를 불러오는 중입니다." }, MUTED, Gravity.NO_GRAVITY))
            }
            is LensTarget.Sector -> {
                val sector = data?.sectors?.firstOrNull { it.id == target.sectorId }
                addView(title(sector?.nameKo ?: "섹터 #${target.sectorId}", 18, TEXT, Gravity.NO_GRAVITY))
                if (!sector?.nameEn.isNullOrBlank()) addView(label(sector!!.nameEn, MUTED, Gravity.NO_GRAVITY))
            }
        }
        addSpace(10)
        addView(label("이 렌즈 설정은 현재 앱에만 저장됩니다. 서버 저장 API가 준비되면 동기화 대상으로 연결할 수 있습니다.", MUTED, Gravity.NO_GRAVITY))
    }

    private fun recommendationOption(
        titleText: String,
        recommendation: LensRecommendation,
        catByCode: Map<String, AnalysisCategory>,
        presetByCode: Map<String, AnalysisPreset>,
        selected: Boolean,
        onClick: () -> Unit,
    ) = vertical {
        setPadding(dp(12), dp(10), dp(12), dp(10))
        setBackgroundColor(if (selected) ACCENT_BG else CARD)
        setOnClickListener { onClick() }
        addView(title(titleText, 16, if (selected) ACCENT else TEXT, Gravity.NO_GRAVITY))
        addView(label(
            recommendation.cats.joinToString(" · ") { catByCode[it]?.nameKo ?: it } +
                " + " + (presetByCode[recommendation.preset]?.nameKo ?: recommendation.preset),
            MUTED,
            Gravity.NO_GRAVITY,
        ))
        addView(label(recommendation.why, MUTED, Gravity.NO_GRAVITY))
    }

    private fun presetOption(preset: AnalysisPreset, selected: Boolean, onClick: () -> Unit) = vertical {
        setPadding(dp(12), dp(10), dp(12), dp(10))
        setBackgroundColor(if (selected) ACCENT_BG else CARD)
        setOnClickListener { onClick() }
        val row = horizontal()
        row.addWeighted(title(preset.nameKo, 16, if (selected) ACCENT else TEXT, Gravity.NO_GRAVITY))
        row.addView(pill(if (selected) "선택됨" else preset.code))
        addView(row)
        if (preset.personaText.isNotBlank()) addView(label(preset.personaText, MUTED, Gravity.NO_GRAVITY))
    }

    private fun lensCategorySection(title: String, lens: LensSetting, onToggle: (String) -> Unit) = card {
        addView(sectionTitle(title))
        if (categories.isEmpty()) {
            addView(label("분석 카테고리를 불러오지 못했습니다.", MUTED, Gravity.NO_GRAVITY))
        } else {
            val catByCode = categories.associateBy { it.code }
            val selectedLabels = lens.categoryCodes.map { catByCode[it]?.nameKo ?: it }
            addView(label(
                if (selectedLabels.isEmpty()) "선택한 카테고리가 없습니다. 아래 그룹에서 추가하세요."
                else "선택됨: ${selectedLabels.joinToString(" · ")}",
                if (selectedLabels.isEmpty()) MUTED else ACCENT,
                Gravity.NO_GRAVITY,
            ))
            addSpace(10)
            categories.groupBy { it.type }.forEach { (type, items) ->
                addView(label(type, MUTED, Gravity.NO_GRAVITY))
                val search = input("$type 검색")
                val group = ChipGroup(this@MainActivity).apply { isSingleSelection = false }
                fun render(query: String) {
                    group.removeAllViews()
                    val selected = items.filter { it.code in lens.categoryCodes }
                    val candidates = if (query.isBlank()) emptyList() else items
                        .filter { it.code !in lens.categoryCodes }
                        .filter { it.code.contains(query, true) || it.nameKo.contains(query, true) || it.nameEn.contains(query, true) }
                    val visible = (selected + candidates).distinctBy { it.code }
                    if (visible.isEmpty()) {
                        group.addView(Chip(this@MainActivity).apply {
                            text = if (query.isBlank()) "선택한 항목 없음" else "검색 결과 없음"
                            isEnabled = false
                            setTextColor(MUTED)
                            chipBackgroundColor = ColorStateList.valueOf(CARD)
                            chipStrokeColor = ColorStateList.valueOf(LINE)
                            chipStrokeWidth = dp(1).toFloat()
                        })
                        return
                    }
                    visible.forEach { cat ->
                        group.addView(Chip(this@MainActivity).apply {
                            text = cat.nameKo
                            isCheckable = true
                            isChecked = cat.code in lens.categoryCodes
                            setTextColor(navigationTint())
                            chipBackgroundColor = ColorStateList(
                                arrayOf(intArrayOf(android.R.attr.state_checked), intArrayOf()),
                                intArrayOf(ACCENT_BG, CARD),
                            )
                            chipStrokeColor = ColorStateList.valueOf(LINE)
                            chipStrokeWidth = dp(1).toFloat()
                            setOnClickListener { onToggle(cat.code) }
                        })
                    }
                }
                search.edit().addTextChangedListener(SimpleWatcher { render(it) })
                addView(search)
                render("")
                addView(group)
            }
        }
    }

    private fun stockCard(watch: WatchlistItem, item: StockBriefing?) = briefingRowCard(
        titleText = watch.ticker,
        subtitle = stockSubtitle(watch),
        sentiment = item?.sentiment,
        summary = cleanDisplayText(item?.oneLineSummary)
            ?: cleanDisplayText(item?.summary)
            ?: "아직 오늘의 브리핑이 생성되지 않았습니다.",
        issueCount = item?.let { it.positiveFactors.size + it.negativeFactors.size },
        refreshing = refreshingTicker == watch.ticker,
        removing = removingTicker == watch.ticker,
        onOpen = { openDetail(DetailTarget.Stock(watch.ticker)) },
        onRefresh = { refreshStockBriefing(watch.ticker) },
        onRemove = { removeWatchFromCard(watch.ticker) },
    )

    private fun oldStockCard(watch: WatchlistItem, item: StockBriefing?) = card {
        setOnClickListener { openDetail(DetailTarget.Stock(watch.ticker)) }
        val top = horizontal()
        top.addWeighted(vertical {
            addView(title(watch.ticker, 19, TEXT, Gravity.NO_GRAVITY))
            val subtitle = listOf(watch.name, watch.sectorName).filter { it.isNotBlank() }.joinToString(" · ")
            if (subtitle.isNotBlank()) addView(label(subtitle, MUTED, Gravity.NO_GRAVITY))
        })
        item?.sentiment?.let { top.addView(sentimentPill(it)) }
        top.addView(iconTextButton("삭제") { mutate({ api.removeWatchlist(watch.ticker) }, "관심 종목을 삭제했습니다.") })
        addView(top)
        addSpace(10)
        addView(label(item?.summary?.takeIf { it.isNotBlank() } ?: "아직 오늘의 브리핑이 생성되지 않았습니다.", TEXT, Gravity.NO_GRAVITY))
        item?.todayActions?.take(2)?.forEach { addView(label("- $it", TEXT, Gravity.NO_GRAVITY)) }
    }

    private fun sectorCard(watch: SectorWatchlistItem, item: SectorBriefing?) = briefingRowCard(
        titleText = watch.sector?.nameKo ?: "섹터 #${watch.sectorId}",
        subtitle = "",
        sentiment = item?.sentiment,
        summary = cleanDisplayText(item?.oneLineSummary)
            ?: cleanDisplayText(item?.summary)
            ?: "아직 브리핑이 생성되지 않았습니다.",
        issueCount = item?.let { it.positiveFactors.size + it.negativeFactors.size },
        refreshing = refreshingSectorId == watch.sectorId,
        removing = removingSectorId == watch.sectorId,
        onOpen = { openDetail(DetailTarget.Sector(watch.sectorId)) },
        onRefresh = { refreshSectorBriefing(watch.sectorId) },
        onRemove = { removeSectorFromCard(watch.sectorId) },
    )

    private fun oldSectorCard(watch: SectorWatchlistItem, item: SectorBriefing?) = card {
        setOnClickListener { openDetail(DetailTarget.Sector(watch.sectorId)) }
        val top = horizontal()
        top.addWeighted(vertical {
            addView(title(watch.sector?.nameKo ?: "섹터 #${watch.sectorId}", 18, TEXT, Gravity.NO_GRAVITY))
            if (!watch.sector?.nameEn.isNullOrBlank()) addView(label(watch.sector!!.nameEn, MUTED, Gravity.NO_GRAVITY))
        })
        item?.sentiment?.let { top.addView(sentimentPill(it)) }
        top.addView(iconTextButton("삭제") { mutate({ api.removeSectorWatchlist(watch.sectorId) }, "관심 섹터를 삭제했습니다.") })
        addView(top)
        addSpace(10)
        addView(label(item?.summary?.takeIf { it.isNotBlank() } ?: "아직 오늘의 섹터 브리핑이 생성되지 않았습니다.", TEXT, Gravity.NO_GRAVITY))
    }

    private fun overviewCard(overview: MarketOverview?) = MaterialCardView(this).apply {
        setCardBackgroundColor(CARD)
        strokeColor = LINE
        strokeWidth = dp(1)
        radius = dp(13).toFloat()
        cardElevation = 0f
        useCompatPadding = true
        setOnClickListener { openDetail(DetailTarget.Overview()) }
        addView(horizontal().apply {
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(14), dp(14), dp(14), dp(14))
            addView(vertical {
                val titleRow = horizontal()
                titleRow.addView(title("전체 시황", 15, TEXT, Gravity.NO_GRAVITY))
                overview?.sentiment?.takeIf { it.isNotBlank() }?.let {
                    titleRow.addHorizontalSpace(dp(9))
                    titleRow.addView(sentimentPill(it))
                }
                addView(titleRow)
                addView(summaryLabel(
                    cleanDisplayText(overview?.oneLineSummary)
                        ?: cleanDisplayText(overview?.summary)
                        ?: "아직 전체 시황 브리핑이 생성되지 않았습니다.",
                    MUTED,
                ).apply {
                    textSize = 13f
                    setPadding(0, dp(5), 0, 0)
                }, LinearLayout.LayoutParams(-1, -2))
            }, LinearLayout.LayoutParams(0, -2, 1f).apply { rightMargin = dp(14) })
            addView(cardActions(
                issueCount = overviewIssueCount(overview),
                refreshing = refreshingOverview,
                removing = false,
                onRefresh = { refreshOverviewBriefing() },
                onRemove = null,
            ), LinearLayout.LayoutParams(-2, -2))
        })
    }

    private fun overviewIssueCount(overview: MarketOverview?): Int? {
        if (overview == null) return null
        val count = overview.positiveFactors.size + overview.negativeFactors.size
        return count.takeIf { it > 0 }
    }

    private fun stockSubtitle(watch: WatchlistItem): String {
        val stock = watch.stock
            ?: briefing?.allStocks?.firstOrNull { it.ticker == watch.ticker }
            ?: extraStocks[watch.ticker]
        val name = cleanDisplayText(stock?.nameKo)
            ?: cleanDisplayText(stock?.nameEn)
            ?: cleanDisplayText(watch.name)
        val sector = cleanDisplayText(stock?.sectorName)
            ?: cleanDisplayText(watch.sectorName)
            ?: "섹터 미지정"
        return listOfNotNull(name, sector).joinToString(" · ")
    }

    private fun cleanDisplayText(value: String?): String? {
        val text = value?.trim().orEmpty()
        return text.takeIf { it.isNotBlank() && !it.equals("null", ignoreCase = true) }
    }

    private fun profileAvatar(nickname: String) = TextView(this).apply {
        text = nickname.trim().take(2).ifBlank { "?" }
        textSize = 18f
        typeface = android.graphics.Typeface.DEFAULT_BOLD
        gravity = Gravity.CENTER
        setTextColor(ACCENT)
        background = roundedStrokeBackground(ACCENT_BG, ACCENT_BG, dp(16).toFloat())
        layoutParams = LinearLayout.LayoutParams(dp(58), dp(58))
    }

    private fun profileGroupTitle(textValue: String) = label(textValue, SOFT_MUTED, Gravity.NO_GRAVITY).apply {
        textSize = 12f
        typeface = android.graphics.Typeface.DEFAULT_BOLD
        setPadding(0, dp(10), 0, dp(2))
    }

    private fun myPageWatchRow(watch: WatchlistItem) = horizontal().apply {
        setPadding(dp(14), dp(12), dp(14), dp(12))
        background = roundedStrokeBackground(CARD, LINE, dp(13).toFloat())
        setOnClickListener { openLens(LensTarget.Stock(watch.ticker)) }
        val stock = briefing?.allStocks?.firstOrNull { it.ticker == watch.ticker } ?: extraStocks[watch.ticker]
        val name = cleanDisplayText(stock?.nameKo) ?: cleanDisplayText(stock?.nameEn) ?: cleanDisplayText(watch.name)
        val sector = cleanDisplayText(stock?.sectorName) ?: cleanDisplayText(watch.sectorName) ?: "섹터 미정"
        val lens = lensFor(LensTarget.Stock(watch.ticker))
        val preset = lens.presetCode?.let { code -> presets.firstOrNull { it.code == code }?.nameKo } ?: "미설정"
        addWeighted(vertical {
            val tickerRow = horizontal()
            tickerRow.addView(title(watch.ticker, 15, TEXT, Gravity.NO_GRAVITY))
            tickerRow.addView(label(listOfNotNull(name, sector).joinToString(" · "), SOFT_MUTED, Gravity.NO_GRAVITY).apply {
                textSize = 12f
                setPadding(dp(9), 0, 0, 0)
                maxLines = 1
            })
            addView(tickerRow)
            addView(lensBadge("$preset · 카테고리 ${lens.categoryCodes.size}개"))
        })
        addView(rowActionButton("×", danger = true) {
            mutate({ api.removeWatchlist(watch.ticker) }, "관심 종목을 삭제했습니다.")
        })
    }

    private fun lensBadge(textValue: String) = TextView(this).apply {
        text = "≡ $textValue"
        textSize = 11f
        setTextColor(ACCENT)
        background = roundedStrokeBackground(ACCENT_BG, ACCENT_BG, dp(10).toFloat())
        setPadding(dp(9), dp(3), dp(9), dp(3))
        layoutParams = LinearLayout.LayoutParams(-2, -2).apply { topMargin = dp(6) }
    }

    private fun myPageStrip(textValue: String) = label(textValue, ACCENT, Gravity.NO_GRAVITY).apply {
        textSize = 14f
        background = roundedStrokeBackground(ACCENT_BG, ACCENT_BG, dp(12).toFloat())
        setPadding(dp(14), dp(11), dp(14), dp(11))
    }

    private fun myPageHint() = TextView(this).apply {
        val raw = "종목을 클릭하면 해당 종목의 분석 렌즈로 이동합니다. \n종목 추가는 오늘의 브리핑에서 검색으로 할 수 있습니다."
        val link = "오늘의 브리핑"
        val start = raw.indexOf(link)
        text = SpannableString(raw).apply {
            if (start >= 0) {
                val end = start + link.length
                setSpan(ForegroundColorSpan(ACCENT), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                setSpan(UnderlineSpan(), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                setSpan(object : ClickableSpan() {
                    override fun onClick(widget: View) {
                        selectedTab = 0
                        showHome()
                    }
                }, start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
            }
        }
        textSize = 11.5f
        setTextColor(SOFT_MUTED)
        setLinkTextColor(ACCENT)
        movementMethod = LinkMovementMethod.getInstance()
        highlightColor = Color.TRANSPARENT
        setLineSpacing(2f, 1.15f)
        setPadding(0, dp(14), 0, 0)
    }

    private fun oldOverviewCard(overview: MarketOverview?) = card {
        addView(title("전체 시황", 18, TEXT, Gravity.NO_GRAVITY))
        if (!overview?.briefingDate.isNullOrBlank()) addView(label(overview!!.briefingDate, MUTED, Gravity.NO_GRAVITY))
        addSpace(10)
        addView(label(overview?.summary?.takeIf { it.isNotBlank() } ?: "아직 전체 시황 브리핑이 생성되지 않았습니다.", TEXT, Gravity.NO_GRAVITY))
    }

    private fun volatilityHero(data: VolatilityData?) = vertical {
        val kicker = horizontal()
        kicker.addView(View(context).apply {
            background = roundedStrokeBackground(GREEN, GREEN, dp(999).toFloat())
        }, LinearLayout.LayoutParams(dp(7), dp(7)))
        kicker.addView(label("PRE-MARKET SCANNER", ACCENT, Gravity.NO_GRAVITY).apply {
            textSize = 11f
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            setPadding(dp(7), 0, 0, 0)
        })
        addView(kicker)
        addSpace(7)
        addView(title("오늘 움직임이 큰 종목", 25, TEXT, Gravity.NO_GRAVITY))
        addView(label("상승과 하락을 함께 탐지하고, \n5개 지표를 합산한 변동성 주목 점수로 순위를 매깁니다.", MUTED, Gravity.NO_GRAVITY).apply {
            textSize = 13f
        })
        data?.generatedAt?.takeIf { it.isNotBlank() }?.let {
            addView(label("${formatUpdatedAt(it)} 기준", SOFT_MUTED, Gravity.NO_GRAVITY).apply {
                textSize = 12f
                setPadding(0, dp(4), 0, 0)
            })
        }
    }

    private fun volatilityTabs(threshold: Double, liquidity: Double, onSelect: (Int) -> Unit) = horizontal().apply {
        addWeighted(volatilityTab(
            "우량·중대형주",
            "시총 ${formatMarketCap(threshold)} 이상 \n유동성 적용",
            volatilityBlueChip,
        ) { onSelect(0) })
        addSpace(8)
        addWeighted(volatilityTab(
            "전체 종목",
            "시총 제한 없음 \n일평균 거래대금 ${formatMarketCap(liquidity)} 이상",
            !volatilityBlueChip,
        ) { onSelect(1) })
    }

    private fun volatilityTab(titleText: String, subtitle: String, selected: Boolean, onClick: () -> Unit) = vertical {
        setPadding(dp(14), dp(11), dp(14), dp(11))
        minimumHeight = dp(76)
        background = roundedStrokeBackground(
            if (selected) ACCENT_BG else CARD,
            if (selected) ACCENT else LINE,
            dp(14).toFloat(),
        )
        addView(title(titleText, 14, if (selected) ACCENT else TEXT, Gravity.NO_GRAVITY))
        addView(label(subtitle, if (selected) ACCENT else SOFT_MUTED, Gravity.NO_GRAVITY).apply {
            textSize = 11f
            maxLines = 2
        })
        setOnClickListener { onClick() }
    }

    private fun volatilityPanel(data: VolatilityData?) = MaterialCardView(this).apply {
        setCardBackgroundColor(CARD)
        strokeColor = LINE
        strokeWidth = dp(1)
        radius = dp(16).toFloat()
        cardElevation = 0f
        addView(vertical {
            val head = horizontal().apply {
                setPadding(dp(18), dp(14), dp(18), dp(14))
                addWeighted(title("${data?.scoreName ?: "변동성 주목 점수"} 상위 종목", 12, MUTED, Gravity.NO_GRAVITY))
                addView(label("최대 5개 · 100점 만점", SOFT_MUTED, Gravity.RIGHT).apply { textSize = 11f })
            }
            addView(head)
            addView(View(context).apply { setBackgroundColor(LINE) }, LinearLayout.LayoutParams(-1, dp(1)))
            when {
                volatilityLoading && data == null -> addView(volatilityState("종목을 불러오는 중입니다.", loading = true))
                volatilityError != null && data == null -> addView(volatilityErrorState(volatilityError!!))
                data == null -> addView(volatilityState("표시할 종목이 없습니다.\n장 시작 전 다음 스캔 결과를 기다려 주세요."))
                else -> {
                    val items = if (volatilityBlueChip) data.blueChip.items else data.all.items
                    if (items.isEmpty()) {
                        addView(volatilityState("표시할 종목이 없습니다.\n장 시작 전 다음 스캔 결과를 기다려 주세요."))
                    } else {
                        items.forEachIndexed { index, item ->
                            addView(volatilityRow(index + 1, item))
                            if (index < items.lastIndex) {
                                addView(View(context).apply { setBackgroundColor(LINE) }, LinearLayout.LayoutParams(-1, dp(1)))
                            }
                        }
                    }
                }
            }
        })
    }

    private fun volatilityState(message: String, loading: Boolean = false) = horizontal().apply {
        gravity = Gravity.CENTER
        setPadding(dp(22), dp(32), dp(22), dp(32))
        if (loading) addView(ProgressBar(context).apply { isIndeterminate = true }, LinearLayout.LayoutParams(dp(24), dp(24)))
        addView(label(message, MUTED, Gravity.CENTER).apply {
            textSize = 13f
            if (loading) setPadding(dp(10), 0, 0, 0)
        })
    }

    private fun volatilityErrorState(message: String) = vertical {
        gravity = Gravity.CENTER
        setPadding(dp(22), dp(28), dp(22), dp(28))
        addView(title("아직 오늘의 스캔 결과가 없습니다.", 14, TEXT, Gravity.CENTER))
        addView(label(message, RED, Gravity.CENTER).apply {
            textSize = 12f
            setPadding(0, dp(4), 0, dp(10))
        })
        addView(smallButton("다시 불러오기").apply { setOnClickListener { loadVolatility() } })
    }

    private fun volatilityRow(rank: Int, item: VolatilityItem) = vertical {
        setPadding(dp(18), dp(14), dp(18), dp(14))
        val inWatch = briefing?.watchlist?.any { it.ticker == item.ticker } == true
        val top = horizontal()
        top.addView(volatilityRank(rank))
        top.addView(vertical {
            setPadding(dp(10), 0, 0, 0)
            minimumHeight = dp(32)
            addView(title(item.ticker, 15, TEXT, Gravity.NO_GRAVITY))
            if (item.newsConfirmed) addView(label("뉴스 ${item.newsCount}건", ACCENT, Gravity.NO_GRAVITY).apply { textSize = 10f })
        }, LinearLayout.LayoutParams(0, -2, 1f))
        top.addView(vertical {
            gravity = Gravity.RIGHT
            addView(title(item.score.toInt().toString(), 20, ACCENT, Gravity.RIGHT))
        })
        top.addView(View(context), LinearLayout.LayoutParams(dp(1), 1))
        top.addView(volatilityActionButton(inWatch, addingVolatilityTicker == item.ticker) {
            handleVolatilityStock(item.ticker)
        })
        addView(top)
        addSpace(12)
        val metrics = horizontal()
        metrics.addWeighted(volatilityMetric("프리마켓 갭", signed(item.premarketGap), if (item.premarketDirection == "down") RED else GREEN))
        metrics.addWeighted(volatilityMetric("전일 변동폭", "%.1f%%".format(item.highLowSpread), TEXT))
        metrics.addWeighted(volatilityMetric("시가총액", formatMarketCap(item.marketCap), TEXT))
        addView(metrics)
    }

    private fun volatilityRank(rank: Int) = TextView(this).apply {
        text = rank.toString()
        textSize = 12f
        typeface = android.graphics.Typeface.DEFAULT_BOLD
        gravity = Gravity.CENTER
        setTextColor(if (rank == 1) Color.WHITE else SOFT_MUTED)
        background = roundedStrokeBackground(if (rank == 1) ACCENT else BG, if (rank == 1) ACCENT else BG, dp(9).toFloat())
        layoutParams = LinearLayout.LayoutParams(dp(28), dp(28))
    }

    private fun volatilityActionButton(inWatch: Boolean, loading: Boolean, onClick: () -> Unit) = TextView(this).apply {
        text = when {
            loading -> "…"
            inWatch -> "✓"
            else -> "+"
        }
        textSize = 18f
        typeface = android.graphics.Typeface.DEFAULT_BOLD
        gravity = Gravity.CENTER
        setTextColor(if (inWatch) Color.WHITE else ACCENT)
        background = roundedStrokeBackground(if (inWatch) ACCENT else ACCENT_BG, ACCENT_LINE, dp(9).toFloat())
        setOnClickListener { onClick() }
        isEnabled = !loading
        layoutParams = LinearLayout.LayoutParams(dp(30), dp(30)).apply { leftMargin = dp(10) }
    }

    private fun volatilityMetric(labelText: String, value: String, color: Int) = vertical {
        gravity = Gravity.CENTER
        addView(title(value, 14, color, Gravity.CENTER).apply {
            maxLines = 1
        })
        addView(label(labelText, SOFT_MUTED, Gravity.CENTER).apply {
            textSize = 10.5f
            maxLines = 1
        })
    }

    private fun stockDetailCard(item: StockBriefing) = card {
        addView(sentimentPill(item.sentiment))
        addSpace(8)
        addView(label(item.summary, TEXT, Gravity.NO_GRAVITY))
        addFactors("긍정 요인", item.positiveFactors)
        addFactors("부정 요인", item.negativeFactors)
        addFactors("확인할 것", item.watchIssues)
        addReasons(item.reasons)
    }

    private fun sectorDetailCard(item: SectorBriefing) = card {
        addView(sentimentPill(item.sentiment))
        addSpace(8)
        addView(label(item.summary, TEXT, Gravity.NO_GRAVITY))
        addFactors("긍정 요인", item.positiveFactors)
        addFactors("부정 요인", item.negativeFactors)
        addFactors("확인할 것", item.watchIssues)
        addReasons(item.reasons)
    }

    private fun LinearLayout.addFactors(titleText: String, items: List<String>) {
        if (items.isEmpty()) return
        addSpace(12)
        addView(sectionTitle(titleText))
        items.forEach { addView(label("- $it", TEXT, Gravity.NO_GRAVITY)) }
    }

    private fun LinearLayout.addReasons(reasons: List<FactorReason>) {
        if (reasons.isEmpty()) return
        addSpace(12)
        addView(sectionTitle("근거"))
        reasons.forEach { reason ->
            val text = if (reason.sourceUrl.isBlank()) reason.displayText else "${reason.displayText}\n${reason.sourceUrl}"
            addView(label(text, ACCENT, Gravity.NO_GRAVITY).apply {
                if (reason.sourceUrl.isNotBlank()) setOnClickListener {
                    runCatching { startActivity(android.content.Intent(android.content.Intent.ACTION_VIEW, Uri.parse(reason.sourceUrl))) }
                }
            })
        }
    }

    private fun detailActions(
        onLens: () -> Unit,
        onToggle: () -> Unit,
        toggleLabel: String
    ) = horizontal().apply {

        addWeighted(detailActionButton("분석 렌즈 편집", primary = true) { onLens() })

        addHorizontalSpace(dp(10))

        addView(detailActionButton(toggleLabel, primary = false) { onToggle() })
    }

    private fun detailActionButton(text: String, primary: Boolean, onClick: () -> Unit) = MaterialButton(this).apply {
        this.text = if (primary) "\u2261 $text" else text
        textSize = 13f
        minHeight = dp(38)
        minimumHeight = dp(38)
        insetTop = 0
        insetBottom = 0
        cornerRadius = dp(10)
        setPadding(dp(12), 0, dp(12), 0)
        if (primary) {
            setTextColor(Color.WHITE)
            setBackgroundColor(ACCENT)
            strokeColor = ColorStateList.valueOf(ACCENT)
        } else {
            setTextColor(MUTED)
            setBackgroundColor(CARD)
            strokeColor = ColorStateList.valueOf(LINE)
        }
        strokeWidth = dp(1)
        setOnClickListener { onClick() }
    }

    private fun oldDetailActions(onLens: () -> Unit, onToggle: () -> Unit, toggleLabel: String) = horizontal().apply {
        addWeighted(primaryButton("분석 렌즈 편집").apply { setOnClickListener { onLens() } })
        addView(smallButton(toggleLabel).apply { setOnClickListener { onToggle() } })
    }


    private fun toggleWatch(ticker: String) {
        val exists = briefing?.watchlist?.any { it.ticker == ticker } == true
        if (exists) mutate({ api.removeWatchlist(ticker) }, "관심 종목을 삭제했습니다.")
        else mutate({ api.addWatchlist(ticker) }, "관심 종목을 추가했습니다.")
    }

    private fun toggleSectorWatch(sectorId: Int) {
        val exists = briefing?.sectorWatchlist?.any { it.sectorId == sectorId } == true
        if (exists) mutate({ api.removeSectorWatchlist(sectorId) }, "관심 섹터를 삭제했습니다.")
        else mutate({ api.addSectorWatchlist(sectorId) }, "관심 섹터를 추가했습니다.")
    }

    private fun handleVolatilityStock(ticker: String) {
        if (addingVolatilityTicker != null) return
        val exists = briefing?.watchlist?.any { it.ticker == ticker } == true
        if (exists) {
            openDetail(DetailTarget.Stock(ticker))
            return
        }
        addingVolatilityTicker = ticker
        mutate({ api.addWatchlist(ticker) }, "관심 종목을 추가했습니다.") {
            addingVolatilityTicker = null
            openDetail(DetailTarget.Stock(ticker))
        }
    }

    private fun removeWatchFromCard(ticker: String) {
        if (removingTicker != null) return
        removingTicker = ticker
        mutate({ api.removeWatchlist(ticker) }, "관심 종목을 삭제했습니다.") {
            removingTicker = null
        }
    }

    private fun removeSectorFromCard(sectorId: Int) {
        if (removingSectorId != null) return
        removingSectorId = sectorId
        mutate({ api.removeSectorWatchlist(sectorId) }, "관심 섹터를 삭제했습니다.") {
            removingSectorId = null
        }
    }

    private fun <T> mutate(action: () -> T, message: String, after: (T) -> Unit = {}) {
        mutationError = null
        async(
            work = action,
            success = {
                after(it)
                toast(message)
                loadBriefing(clear = false)
            },
            error = {
                mutationError = friendlyError(it)
                removingTicker = null
                removingSectorId = null
                addingVolatilityTicker = null
                showHome()
            },
        )
    }

    private fun loadStock(ticker: String) {
        stockLoadingTickers = stockLoadingTickers + ticker
        async(
            work = { api.getStock(ticker) },
            success = {
                extraStocks = extraStocks + (ticker to it)
                showHome()
            },
            complete = {
                stockLoadingTickers = stockLoadingTickers - ticker
            },
        )
    }

    private fun openDetail(target: DetailTarget) {
        pushScreenState()
        detailTarget = target
        lensTarget = null
        detailTimeMode = 0
        selectedDetailSession = null
        selectedHistoryDate = null
        selectedHistorySession = null
        showHome()
    }

    private fun openLens(target: LensTarget) {
        pushScreenState()
        lensTarget = target
        detailTarget = null
        lensPreviewExpanded = false
        lensCategorySearchOpen = emptySet()
        lensCategorySearchQuery = emptyMap()
        showHome()
    }

    private fun lensFor(target: LensTarget): LensSetting {
        val fallback = LensRules.defaultLens(sectorCodeFor(target))
        return lensSettingFromJson(prefs.getString(lensKey(target), null), fallback)
    }

    private fun saveLens(target: LensTarget, setting: LensSetting) {
        prefs.edit().putString(lensKey(target), setting.toJsonString()).apply()
    }

    private fun sectorCodeFor(target: LensTarget): String? {
        val data = briefing
        val sectorName = when (target) {
            is LensTarget.Stock -> data?.allStocks?.firstOrNull { it.ticker == target.ticker }?.sectorName
            is LensTarget.Sector -> data?.sectors?.firstOrNull { it.id == target.sectorId }?.nameKo
        }
        return sectorName?.let { LensRules.sectorCodeByName(it) }
    }

    private fun lensTitle(target: LensTarget) = when (target) {
        is LensTarget.Stock -> "${target.ticker} 분석 렌즈"
        is LensTarget.Sector -> "${briefing?.sectors?.firstOrNull { it.id == target.sectorId }?.nameKo ?: "섹터 #${target.sectorId}"} 분석 렌즈"
    }

    private fun lensKey(target: LensTarget) = when (target) {
        is LensTarget.Stock -> "lens_stock_${target.ticker}"
        is LensTarget.Sector -> "lens_sector_${target.sectorId}"
    }

    private fun metricRow(name: String, value: String) = card {
        val row = horizontal()
        row.addWeighted(label(name, MUTED, Gravity.NO_GRAVITY))
        row.addView(title(value, 16, TEXT, Gravity.NO_GRAVITY))
        addView(row)
    }

    private fun loadingScreen(text: String): View = vertical {
        gravity = Gravity.CENTER
        setBackgroundColor(BG)
        addView(ProgressBar(this@MainActivity))
        addSpace(12)
        addView(label(text, TEXT, Gravity.CENTER))
    }

    private fun scrollColumn(): LinearLayout {
        val scroll = ScrollView(this).apply { setBackgroundColor(BG) }
        val column = vertical { setPadding(dp(20), dp(18), dp(20), dp(28)) }
        scroll.addView(column)
        return column
    }

    private fun pageTitle(text: String, subtitle: String) = vertical {
        addView(title(text, 27, TEXT, Gravity.NO_GRAVITY))
        if (subtitle.isNotBlank()) addView(label(subtitle, MUTED, Gravity.NO_GRAVITY))
    }

    private fun loading(text: String) = vertical {
        gravity = Gravity.CENTER
        setPadding(0, dp(70), 0, dp(70))
        addView(ProgressBar(this@MainActivity))
        addSpace(16)
        addView(label(text, TEXT, Gravity.CENTER))
    }

    private fun empty(text: String) = card {
        gravity = Gravity.CENTER
        addView(label(text, MUTED, Gravity.CENTER))
    }

    private fun statusCard(text: String, color: Int) = TextView(this).apply {
        this.text = text
        textSize = 13f
        setTextColor(color)
        setBackgroundColor(if (color == RED) RED_BG else ACCENT_BG)
        setPadding(dp(12), dp(10), dp(12), dp(10))
        setLineSpacing(2f, 1.12f)
    }

    private fun resultRow(title: String, subtitle: String, onAdd: () -> Unit) = card {
        val row = horizontal()
        row.addWeighted(vertical {
            addView(title(title, 16, TEXT, Gravity.NO_GRAVITY))
            if (subtitle.isNotBlank()) addView(label(subtitle, MUTED, Gravity.NO_GRAVITY))
        })
        row.addView(iconTextButton("추가", onAdd))
        addView(row)
    }

    private fun card(color: Int = Color.WHITE, build: LinearLayout.() -> Unit): MaterialCardView {
        val card = MaterialCardView(this).apply {
            radius = dp(8).toFloat()
            strokeColor = LINE
            strokeWidth = 1
            setCardBackgroundColor(if (color == Color.WHITE) CARD else color)
            useCompatPadding = true
        }
        val inner = vertical {
            setPadding(dp(16), dp(16), dp(16), dp(16))
            build()
        }
        card.addView(inner)
        return card
    }

    private fun input(label: String, password: Boolean = false): TextInputLayout {
        val layout = TextInputLayout(this).apply {
            hint = label
            setPadding(0, dp(6), 0, dp(6))
            boxBackgroundColor = CARD
            defaultHintTextColor = ColorStateList.valueOf(MUTED)
            setBoxStrokeColorStateList(navigationTint())
        }
        val edit = TextInputEditText(layout.context).apply {
            setSingleLine(true)
            setTextColor(TEXT)
            setHintTextColor(MUTED)
            if (password) inputType = android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD
        }
        layout.addView(edit)
        return layout
    }

    private fun chips(labels: List<String>, selected: Int, onSelected: (Int) -> Unit): ChipGroup {
        val group = ChipGroup(this).apply {
            isSingleSelection = true
            isSelectionRequired = true
        }
        labels.forEachIndexed { index, text ->
            group.addView(Chip(this).apply {
                id = View.generateViewId()
                this.text = text
                isCheckable = true
                isChecked = index == selected
                isCheckedIconVisible = false
                setTextColor(selectedButtonTextTint())
                chipBackgroundColor = ColorStateList(
                    arrayOf(intArrayOf(android.R.attr.state_checked), intArrayOf()),
                    intArrayOf(ACCENT, CARD),
                )
                chipStrokeColor = ColorStateList.valueOf(LINE)
                chipStrokeWidth = dp(1).toFloat()
                setOnClickListener { onSelected(index) }
            })
        }
        return group
    }

    private fun searchToggleButton(selected: Boolean, enabled: Boolean, onClick: () -> Unit) = TextView(this).apply {
        text = "검색"
        textSize = 13f
        gravity = Gravity.CENTER
        setPadding(dp(14), dp(8), dp(14), dp(8))
        setTextColor(
            when {
                !enabled -> MUTED
                selected -> Color.WHITE
                else -> MUTED
            }
        )
        alpha = if (enabled) 1f else 0.45f
        background = roundedStrokeBackground(
            fill = if (selected && enabled) ACCENT else CARD,
            stroke = if (selected && enabled) ACCENT else LINE,
            radius = dp(20).toFloat(),
        )
        isEnabled = enabled
        setOnClickListener {
            if (enabled) onClick()
        }
    }

    private fun briefingRowCard(
        titleText: String,
        subtitle: String,
        sentiment: String?,
        summary: String,
        issueCount: Int?,
        refreshing: Boolean,
        removing: Boolean,
        onOpen: () -> Unit,
        onRefresh: () -> Unit,
        onRemove: (() -> Unit)?,
        extraContent: LinearLayout.() -> Unit = {},
    ) = card {
        setOnClickListener { onOpen() }
        val top = horizontal()
        top.addWeighted(vertical {
            val titleRow = horizontal()
            titleRow.addView(title(titleText, 18, TEXT, Gravity.NO_GRAVITY))
            sentiment?.let {
                titleRow.addHorizontalSpace(dp(10))
                titleRow.addView(sentimentPill(it))
            }
            addView(titleRow)
            if (subtitle.isNotBlank()) addView(label(subtitle, MUTED, Gravity.NO_GRAVITY))
        })
        top.addView(cardActions(issueCount, refreshing, removing, onRefresh, onRemove))
        addView(top)
        addSpace(10)
        addView(summaryLabel(summary, TEXT), LinearLayout.LayoutParams(-1, -2))
        extraContent()
    }

    private fun summaryLabel(text: String, color: Int) = label(text, color, Gravity.NO_GRAVITY).apply {
        isSingleLine = false
        maxLines = Int.MAX_VALUE
        setHorizontallyScrolling(false)
    }

    private fun cardActions(
        issueCount: Int?,
        refreshing: Boolean,
        removing: Boolean,
        onRefresh: () -> Unit,
        onRemove: (() -> Unit)?,
    ) = vertical {
        gravity = Gravity.RIGHT
        issueCount?.let { addView(label("이슈 ${it}건", MUTED, Gravity.RIGHT).apply { textSize = 11f }) }
        val row = horizontal()
        val busy = refreshing || removing
        row.addView(rowActionButton(if (refreshing) "…" else "↻", danger = false) { onRefresh() }.apply { isEnabled = !busy })
        onRemove?.let { remove ->
            row.addView(rowActionButton(if (removing) "…" else "×", danger = true) { remove() }.apply { isEnabled = !busy })
        }
        addView(row)
    }

    private fun rowActionButton(text: String, danger: Boolean, onClick: () -> Unit) = TextView(this).apply {
        this.text = text
        textSize = 17f
        gravity = Gravity.CENTER
        minWidth = dp(34)
        minHeight = dp(34)
        setPadding(0, 0, 0, dp(1))
        setTextColor(MUTED)
        background = roundedStrokeBackground(CARD, LINE, dp(10).toFloat())
        setOnClickListener { onClick() }
    }

    private fun roundedStrokeBackground(fill: Int, stroke: Int, radius: Float) = GradientDrawable().apply {
        setColor(fill)
        cornerRadius = radius
        setStroke(dp(1), stroke)
    }

    private fun metric(label: String, value: String, color: Int) = vertical {
        gravity = Gravity.CENTER
        addView(title(value, 15, color, Gravity.CENTER))
        addView(label(label, MUTED, Gravity.CENTER).apply { textSize = 11f })
    }

    private fun primaryButton(text: String) = MaterialButton(this).apply {
        this.text = text
        setBackgroundColor(ACCENT)
        setTextColor(Color.WHITE)
    }

    private fun smallButton(text: String) = MaterialButton(this).apply { this.text = text }

    private fun textBackButton(text: String, onClick: () -> Unit) = TextView(this).apply {
        this.text = text
        textSize = 14f
        typeface = android.graphics.Typeface.DEFAULT_BOLD
        setTextColor(ACCENT)
        setPadding(0, dp(4), dp(8), dp(4))
        setOnClickListener { onClick() }
    }

    private fun textMutedBackButton(text: String, onClick: () -> Unit) = TextView(this).apply {
        this.text = text
        textSize = 14f
        typeface = android.graphics.Typeface.DEFAULT_BOLD
        setTextColor(SOFT_MUTED)
        setPadding(0, dp(4), dp(8), dp(4))
        setOnClickListener { onClick() }
    }

    private fun iconTextButton(text: String, onClick: () -> Unit) = MaterialButton(this).apply {
        this.text = text
        setOnClickListener { onClick() }
    }

    private fun pill(text: String) = TextView(this).apply {
        this.text = text
        setTextColor(ACCENT)
        setBackgroundColor(ACCENT_BG)
        setPadding(dp(9), dp(5), dp(9), dp(5))
    }

    private fun sentimentPill(sentiment: String) = TextView(this).apply {
        this.text = sentimentText(sentiment)
        textSize = 11f
        setTextColor(sentimentTextColor(sentiment))
        background = roundedStrokeBackground(sentimentBgColor(sentiment), sentimentBorderColor(sentiment), dp(999).toFloat())
        setPadding(dp(8), dp(3), dp(8), dp(3))
    }

    private fun sectionTitle(text: String) = title(text, 16, TEXT, Gravity.NO_GRAVITY)

    private fun title(text: String, size: Int, color: Int, gravityValue: Int) = TextView(this).apply {
        this.text = text
        textSize = size.toFloat()
        setTextColor(color)
        gravity = gravityValue
        typeface = android.graphics.Typeface.DEFAULT_BOLD
    }

    private fun label(text: String, color: Int, gravityValue: Int) = TextView(this).apply {
        this.text = text
        textSize = 14f
        setTextColor(color)
        gravity = gravityValue
        setLineSpacing(2f, 1.12f)
    }

    private fun vertical(build: LinearLayout.() -> Unit = {}) = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        build()
    }

    private fun horizontal() = LinearLayout(this).apply {
        orientation = LinearLayout.HORIZONTAL
        gravity = Gravity.CENTER_VERTICAL
    }

    private fun LinearLayout.addSpace(height: Int) {
        addView(View(context), LinearLayout.LayoutParams(1, height))
    }

    private fun LinearLayout.addWeighted(view: View) {
        addView(view, LinearLayout.LayoutParams(0, -2, 1f))
    }

    private fun TextInputLayout.value() = edit().text?.toString()?.trim().orEmpty()

    private fun TextInputLayout.edit() = editText as EditText

    private fun typeIndex(type: String) = when (type) {
        "stable" -> 0
        "aggressive" -> 2
        else -> 1
    }

    private fun investorTypeDescription(type: String) = when (type) {
        "stable" -> "변동성보다 안정적인 흐름을 선호합니다."
        "aggressive" -> "높은 변동성을 감수하고 수익을 추구합니다."
        else -> "수익과 안정의 균형을 추구합니다."
    }

    private fun sentimentText(sentiment: String?) = when (sentiment) {
        "positive" -> "긍정"
        "negative" -> "주의"
        "neutral" -> "중립"
        else -> "중립"
    }

    private fun sentimentTextColor(sentiment: String?) = when (sentiment) {
        "positive" -> if (isDarkMode) Color.rgb(159, 225, 203) else Color.rgb(15, 110, 86)
        "negative" -> if (isDarkMode) Color.rgb(250, 199, 117) else Color.rgb(133, 79, 11)
        else -> MUTED
    }

    private fun sentimentBgColor(sentiment: String?) = when (sentiment) {
        "positive" -> if (isDarkMode) Color.rgb(13, 67, 53) else Color.rgb(225, 245, 238)
        "negative" -> if (isDarkMode) Color.rgb(77, 44, 5) else Color.rgb(250, 238, 218)
        else -> if (isDarkMode) Color.rgb(22, 23, 30) else Color.rgb(249, 250, 252)
    }

    private fun sentimentBorderColor(sentiment: String?) = when (sentiment) {
        "neutral", null -> if (isDarkMode) Color.rgb(53, 54, 67) else Color.rgb(222, 222, 230)
        else -> sentimentBgColor(sentiment)
    }

    private fun factorText(tone: FactorTone) = when (tone) {
        FactorTone.Positive -> if (isDarkMode) Color.rgb(159, 225, 203) else Color.rgb(15, 110, 86)
        FactorTone.Negative -> if (isDarkMode) Color.rgb(240, 149, 149) else Color.rgb(163, 45, 45)
        FactorTone.Neutral -> MUTED
    }

    private fun factorBg(tone: FactorTone) = when (tone) {
        FactorTone.Positive -> if (isDarkMode) Color.rgb(13, 67, 53) else Color.rgb(225, 245, 238)
        FactorTone.Negative -> if (isDarkMode) Color.rgb(74, 20, 20) else Color.rgb(252, 235, 235)
        FactorTone.Neutral -> if (isDarkMode) Color.rgb(22, 23, 30) else Color.rgb(249, 250, 252)
    }

    private fun factorBorder(tone: FactorTone) = when (tone) {
        FactorTone.Neutral -> if (isDarkMode) Color.rgb(53, 54, 67) else Color.rgb(222, 222, 230)
        else -> factorBg(tone)
    }

    private fun signed(value: Double) = "${if (value > 0) "+" else ""}%.1f%%".format(value)

    private fun formatUpdatedAt(value: String): String {
        if (value.isBlank()) return ""
        return value
            .replace("T", " ")
            .replace("Z", "")
            .take(16)
    }

    private fun formatMarketCap(value: Double?): String {
        val number = value ?: return "정보 없음"
        if (!number.isFinite() || number <= 0.0) return "정보 없음"
        return when {
            number >= 1_000_000_000_000.0 -> "$%.2fT".format(number / 1_000_000_000_000.0)
            number >= 1_000_000_000.0 -> "$%.1fB".format(number / 1_000_000_000.0)
            else -> "$%.0fM".format(number / 1_000_000.0)
        }
    }

    private fun friendlyError(error: Throwable) = when (error) {
        is ApiException -> error.message
        else -> "데이터를 불러오지 못했습니다. 서버 주소와 실행 상태를 확인해주세요."
    }

    private fun toast(message: String) = Toast.makeText(this, message, Toast.LENGTH_SHORT).show()

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    private fun navigationTint() = ColorStateList(
        arrayOf(intArrayOf(android.R.attr.state_checked), intArrayOf()),
        intArrayOf(ACCENT, MUTED),
    )

    private fun selectedButtonTextTint() = ColorStateList(
        arrayOf(intArrayOf(android.R.attr.state_checked), intArrayOf()),
        intArrayOf(Color.WHITE, MUTED),
    )

    private val isDarkMode: Boolean
        get() = resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK == Configuration.UI_MODE_NIGHT_YES

    private val BG: Int
        get() = if (isDarkMode) Color.rgb(18, 19, 26) else Color.rgb(244, 245, 248)
    private val CARD: Int
        get() = if (isDarkMode) Color.rgb(27, 28, 40) else Color.WHITE
    private val LINE: Int
        get() = if (isDarkMode) Color.rgb(54, 55, 76) else Color.rgb(232, 232, 238)
    private val TEXT: Int
        get() = if (isDarkMode) Color.rgb(244, 245, 255) else Color.rgb(27, 28, 34)
    private val MUTED: Int
        get() = if (isDarkMode) Color.rgb(166, 167, 184) else Color.rgb(106, 108, 120)
    private val SOFT_MUTED: Int
        get() = if (isDarkMode) Color.rgb(124, 125, 142) else Color.rgb(156, 158, 170)
    private val ACCENT: Int
        get() = if (isDarkMode) Color.rgb(124, 124, 240) else Color.rgb(91, 91, 214)
    private val ACCENT_DARK: Int
        get() = if (isDarkMode) Color.rgb(38, 38, 74) else Color.rgb(38, 38, 74)
    private val ACCENT_BG: Int
        get() = if (isDarkMode) Color.rgb(42, 42, 74) else Color.rgb(238, 238, 252)
    private val ACCENT_LINE: Int
        get() = if (isDarkMode) Color.rgb(156, 156, 245) else Color.rgb(201, 201, 245)
    private val GREEN: Int
        get() = if (isDarkMode) Color.rgb(95, 211, 177) else Color.rgb(15, 110, 86)
    private val RED: Int
        get() = if (isDarkMode) Color.rgb(255, 133, 133) else Color.rgb(163, 45, 45)
    private val RED_BG: Int
        get() = if (isDarkMode) Color.rgb(74, 37, 44) else Color.rgb(252, 235, 235)

    private fun <T> async(
        work: () -> T,
        success: (T) -> Unit,
        error: (Throwable) -> Unit = {},
        complete: () -> Unit = {},
    ) {
        Thread {
            try {
                val result = work()
                handler.post { success(result); complete() }
            } catch (throwable: Throwable) {
                handler.post { error(throwable); complete() }
            }
        }.start()
    }

    private data class InitialData(
        val briefing: BriefingData,
        val categories: List<AnalysisCategory>,
        val presets: List<AnalysisPreset>,
        val ranking: List<WatchlistRankingItem>,
    )

    private sealed class DetailTarget {
        data class Stock(val ticker: String, val item: StockBriefing? = null) : DetailTarget()
        data class Sector(val sectorId: Int, val item: SectorBriefing? = null) : DetailTarget()
        data class Overview(val item: MarketOverview? = null) : DetailTarget()
    }

    private sealed class LensTarget {
        data class Stock(val ticker: String) : LensTarget()
        data class Sector(val sectorId: Int) : LensTarget()
    }

    private data class ScreenState(
        val selectedTab: Int,
        val briefingMode: Int,
        val detailTarget: DetailTarget?,
        val lensTarget: LensTarget?,
        val detailTimeMode: Int,
        val selectedDetailSession: String?,
        val selectedHistoryDate: String?,
        val selectedHistorySession: String?,
    )

    companion object {
        private const val TOKEN_KEY = "access_token"
    }
}

private fun LinearLayout.addHorizontalSpace(width: Int) {
    addView(View(context), LinearLayout.LayoutParams(width, 1))
}
