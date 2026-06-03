// Static scoped schemes configuration (matching VERIFIED_SCHEME_DB on backend)
const SCOPED_FUNDS = [
    {
        key: "bandhan-small-cap-fund-direct-growth",
        name: "Bandhan Small Cap Fund",
        nav: 36.80,
        rating: 4.6,
        performance: { "3Y": 36.45, "5Y": 29.12, "7Y": 21.80, "10Y": 23.40 }
    },
    {
        key: "bandhan-midcap-fund-direct-growth",
        name: "Bandhan Midcap Fund",
        nav: 24.15,
        rating: 4.5,
        performance: { "3Y": 25.60, "5Y": 22.35, "7Y": 17.40, "10Y": 19.10 }
    },
    {
        key: "bandhan-multi-cap-fund-direct-growth",
        name: "Bandhan Multi Cap Fund",
        nav: 18.90,
        rating: 4.4,
        performance: { "3Y": 28.90, "5Y": 24.15, "7Y": 18.90, "10Y": 21.05 }
    },
    {
        key: "edelweiss-mid-and-small-cap-fund-direct-growth",
        name: "Edelweiss Mid and Small Cap Fund",
        nav: 94.30,
        rating: 4.5,
        performance: { "3Y": 30.12, "5Y": 26.50, "7Y": 19.80, "10Y": 22.15 }
    },
    {
        key: "zerodha-multi-asset-passive-fof-direct-growth",
        name: "Zerodha Multi Asset Passive FoF",
        nav: 12.40,
        rating: 4.2,
        performance: { "3Y": null, "5Y": null, "7Y": null, "10Y": null } // Inactive check
    },
    {
        key: "parag-parikh-long-term-value-fund-direct-growth",
        name: "Parag Parikh Long Term Value Fund",
        nav: 84.60,
        rating: 4.8,
        performance: { "3Y": 24.15, "5Y": 25.80, "7Y": 19.90, "10Y": 21.45 }
    },
    {
        key: "nippon-india-small-cap-fund-direct-growth",
        name: "Nippon India Small Cap Fund",
        nav: 164.50,
        rating: 4.8,
        performance: { "3Y": 32.45, "5Y": 28.12, "7Y": 21.90, "10Y": 24.15 }
    },
    {
        key: "nippon-india-multi-asset-allocation-fund-direct-growth",
        name: "Nippon India Multi Asset Allocation Fund",
        nav: 15.60,
        rating: 4.6,
        performance: { "3Y": 19.80, "5Y": 16.40, "7Y": 13.90, "10Y": 15.12 }
    }
];

// Local memory storage for comparing funds return line curves
const TIMELINE_CURVES = {
    "3Y": [10, 15, 20, 25, 30, 32],
    "5Y": [8, 12, 16, 20, 24, 26, 28],
    "7Y": [6, 10, 14, 18, 20, 22, 23, 24],
    "10Y": [5, 9, 12, 15, 18, 20, 21, 22, 23, 24]
};

// Dynamic API base URL configuration (swaps between local development and production)
const API_BASE_URL = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000"
    : "https://rag-mutual-faq-chatbot-production.up.railway.app"; // Replace with your Railway deployment URL

document.addEventListener("DOMContentLoaded", () => {
    initSidebarSchemes();
    initChatHandlers();
    initTransactionTracking();
    initSidebarSearch();
});

// 1. Populate Scoped Schemes inside Sidebar (with search filtering)
function initSidebarSchemes(filterText = "") {
    const listContainer = document.getElementById("target-schemes-list");
    listContainer.innerHTML = "";
    
    const term = filterText.toLowerCase().trim();
    const filtered = term 
        ? SCOPED_FUNDS.filter(fund => fund.name.toLowerCase().includes(term))
        : SCOPED_FUNDS;
        
    // Update schemes count badge
    const countBadge = document.getElementById("schemes-count");
    if (countBadge) countBadge.innerText = filtered.length;
    
    if (filtered.length === 0) {
        listContainer.innerHTML = `
            <p style="text-align: center; color: var(--text-grey); font-size: 12px; padding: 20px 0;">
                No matching mutual funds found.
            </p>
        `;
        return;
    }
    
    filtered.forEach(fund => {
        const item = document.createElement("div");
        item.className = "scheme-card-item";
        item.setAttribute("data-query", `What is the Groww rating, exit load, and NAV of ${fund.name}?`);
        
        item.innerHTML = `
            <div class="scheme-item-title">${fund.name}</div>
            <div class="scheme-meta-row">
                <span>NAV: ₹${fund.nav.toFixed(2)}</span>
                <span class="scheme-meta-badge"><i class="fa-solid fa-star"></i> ${fund.rating.toFixed(1)}</span>
            </div>
        `;
        
        // Trigger quick lookup click
        item.addEventListener("click", () => {
            const query = item.getAttribute("data-query");
            document.getElementById("user-input-field").value = query;
            document.getElementById("user-input-field").focus();
        });
        
        listContainer.appendChild(item);
    });
}

// 1.1 Initialize Sidebar Real-time Search Input Listener
function initSidebarSearch() {
    const searchInput = document.getElementById("sidebar-search-input");
    if (!searchInput) return;
    
    searchInput.addEventListener("input", (e) => {
        const val = e.target.value;
        initSidebarSchemes(val);
        updateTransactionsUI(val);
        
        const historyModal = document.getElementById("all-transactions-modal");
        if (historyModal && historyModal.classList.contains("active")) {
            renderFullTransactionsHistory();
        }
    });
}

// 2. Chat UI Action Triggers
function initChatHandlers() {
    const chatForm = document.getElementById("chat-form");
    const inputField = document.getElementById("user-input-field");
    const chatThread = document.getElementById("chat-thread");
    const btnClear = document.getElementById("btn-clear-chat");
    
    // Form Submit
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const query = inputField.value.trim();
        if (!query) return;
        
        submitChatQuery(query);
        inputField.value = "";
    });
    
    // Click suggested buttons
    document.querySelectorAll(".suggested-prompt-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-query");
            submitChatQuery(query);
        });
    });
    
    // Clear chat
    btnClear.addEventListener("click", () => {
        chatThread.innerHTML = `
            <div class="message bot-msg fade-in">
                <div class="avatar-msg"><i class="fa-robot fa-solid"></i></div>
                <div class="msg-bubble-wrapper">
                    <div class="msg-bubble">
                        <p>Conversation history cleared. Ask a factual question to begin!</p>
                    </div>
                </div>
            </div>
        `;
    });
}

// 3. Coordinate Chat API Submission Lifecycle
async function submitChatQuery(query) {
    renderMessage(query, "user");
    
    // Render loading indicator bubble
    const loadingId = renderLoadingIndicator();
    
    try {
        // Post request to FastAPI server RAG chat API
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ query: query })
        });
        
        removeLoadingIndicator(loadingId);
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }
        
        const payload = await response.json();
        renderRAGResponse(payload);
        
    } catch (error) {
        console.error(error);
        removeLoadingIndicator(loadingId);
        renderMessage(`**System Error:** Could not contact the local RAG backend server. Please verify FastAPI is running at \`http://127.0.0.1:8000\` using uvicorn.`, "bot");
    }
}

// 4. Message Bubble Renderer
function renderMessage(text, sender) {
    const thread = document.getElementById("chat-thread");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender}-msg fade-in`;
    
    const avatarIcon = sender === "user" ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';
    
    // Basic formatting for Markdown bold/code markers inside text
    let formattedText = text
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
        
    // Simple table parser if text contains holdings grids
    if (formattedText.includes('|')) {
        formattedText = parseMarkdownTable(formattedText);
    }
    
    msgDiv.innerHTML = `
        <div class="avatar-msg">${avatarIcon}</div>
        <div class="msg-bubble-wrapper">
            <div class="msg-bubble">
                ${formattedText}
            </div>
            <span class="msg-timestamp">${sender === "user" ? "You" : "WealthAI"} • ${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
        </div>
    `;
    
    thread.appendChild(msgDiv);
    thread.scrollTop = thread.scrollHeight;
}

// 5. Render Loading State
function renderLoadingIndicator() {
    const thread = document.getElementById("chat-thread");
    const loadingId = "loader_" + Date.now();
    
    const msgDiv = document.createElement("div");
    msgDiv.className = "message bot-msg fade-in";
    msgDiv.id = loadingId;
    
    msgDiv.innerHTML = `
        <div class="avatar-msg"><i class="fa-solid fa-robot"></i></div>
        <div class="msg-bubble-wrapper">
            <div class="msg-bubble">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>
    `;
    
    thread.appendChild(msgDiv);
    thread.scrollTop = thread.scrollHeight;
    return loadingId;
}

function removeLoadingIndicator(id) {
    const loader = document.getElementById(id);
    if (loader) loader.remove();
}

// Helper: Custom Markdown Table parser to render grid data beautifully
function parseMarkdownTable(text) {
    const lines = text.split('<br>');
    let isTable = false;
    let tableHtml = "<table>";
    let regularTextBefore = [];
    let regularTextAfter = [];
    
    lines.forEach(line => {
        if (line.includes('|')) {
            isTable = true;
            const cols = line.split('|').map(c => c.trim()).filter(c => c !== '');
            // Skip markdown alignment dividers like :---
            if (line.includes(':---') || line.includes('---:')) return;
            
            tableHtml += "<tr>";
            cols.forEach(col => {
                tableHtml += `<td>${col}</td>`;
            });
            tableHtml += "</tr>";
        } else {
            if (isTable) {
                regularTextAfter.push(line);
            } else {
                regularTextBefore.push(line);
            }
        }
    });
    
    tableHtml += "</table>";
    
    return [
        regularTextBefore.join('<br>'),
        isTable ? tableHtml : '',
        regularTextAfter.join('<br>')
    ].filter(s => s !== '').join('<br>');
}

// 6. RAG Response Payload Parser & Citation Mapper
function renderRAGResponse(payload) {
    const thread = document.getElementById("chat-thread");
    const msgDiv = document.createElement("div");
    msgDiv.className = "message bot-msg fade-in";
    
    // Parse Markdown indicators
    let formattedAnswer = payload.answer
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
        
    // Parse markdown holdings grids if present
    if (formattedAnswer.includes('|')) {
        formattedAnswer = parseMarkdownTable(formattedAnswer);
    }
    
    // Build Citations badging block
    let citationsHtml = "";
    if (payload.citations && payload.citations.length > 0) {
        citationsHtml = '<div class="citation-container">';
        payload.citations.forEach(c => {
            citationsHtml += `
                <a href="${c.url}" target="_blank" class="citation-badge">
                    <i class="fa-solid fa-arrow-up-right-from-square"></i> ${c.fund_name} Source
                </a>
            `;
        });
        citationsHtml += '</div>';
    }

    // Build Suggested Followups block
    let followupsHtml = "";
    if (payload.suggested_followups && payload.suggested_followups.length > 0) {
        followupsHtml = '<div class="suggested-followups-container">';
        payload.suggested_followups.forEach(q => {
            followupsHtml += `
                <button class="suggested-followup-btn" data-query="${q}">
                    <i class="fa-solid fa-circle-question"></i> ${q}
                </button>
            `;
        });
        followupsHtml += '</div>';
    }
    
    msgDiv.innerHTML = `
        <div class="avatar-msg"><i class="fa-solid fa-robot"></i></div>
        <div class="msg-bubble-wrapper">
            <div class="msg-bubble">
                ${formattedAnswer}
                ${citationsHtml}
            </div>
            ${followupsHtml}
            <span class="msg-timestamp">WealthAI • Grounded Context Run</span>
        </div>
    `;
    
    thread.appendChild(msgDiv);
    
    // 7. Dynamic Multi-Fund Chart Comparison Injector
    // Triggers if 2+ funds are detected or comparison intent is parsed
    if (payload.comparison_funds && payload.comparison_funds.length > 0) {
        renderComparisonChart(payload.comparison_funds);
    } else {
        thread.scrollTop = thread.scrollHeight;
    }
}

// 8. Render Interactive Comparison Widget with Hover Timeline Controls
function renderComparisonChart(fundNames) {
    const thread = document.getElementById("chat-thread");
    const chartId = "chart_" + Date.now();
    
    // 1. Resolve matching fund objects from static scoped registry
    const selectedFunds = SCOPED_FUNDS.filter(f => 
        fundNames.some(name => f.name.toLowerCase().includes(name.toLowerCase()))
    ).slice(0, 3); // Strictly limit to top 3 compare cards
    
    if (selectedFunds.length === 0) return;
    
    const chartWidgetDiv = document.createElement("div");
    chartWidgetDiv.className = "chart-container-widget fade-in";
    
    chartWidgetDiv.innerHTML = `
        <div class="chart-widget-header">
            <div class="chart-widget-title">
                <i class="fa-solid fa-chart-line"></i> Scheme Performance Comparison (${selectedFunds.length} Funds Selected)
            </div>
            <div class="chart-timeline-tabs" id="tabs-${chartId}">
                <button class="timeline-tab-btn active" data-period="3Y">3Y</button>
                <button class="timeline-tab-btn" data-period="5Y">5Y</button>
                <button class="timeline-tab-btn" data-period="7Y">7Y</button>
                <button class="timeline-tab-btn" data-period="10Y">10Y</button>
            </div>
        </div>
        <div id="plot-${chartId}"></div>
        <div id="alerts-${chartId}"></div>
    `;
    
    thread.appendChild(chartWidgetDiv);
    thread.scrollTop = thread.scrollHeight;
    
    // 2. Initialize ApexCharts Line Multi-Series Plotting
    const renderApexPlot = (period) => {
        const plotArea = document.getElementById(`plot-${chartId}`);
        plotArea.innerHTML = "";
        
        const alertArea = document.getElementById(`alerts-${chartId}`);
        alertArea.innerHTML = "";
        
        const seriesData = [];
        let errors = [];
        
        // Match performance values over timeline period
        selectedFunds.forEach(fund => {
            const returnPct = fund.performance[period];
            if (returnPct === null || returnPct === undefined) {
                // Fund is not active for this timeline period (e.g. Zerodha Passive FoF)
                errors.push(`${fund.name} was not established/active for the ${period.replace('Y', '-year')} horizon.`);
            } else {
                // Generate chronological curve points
                const baseCurve = TIMELINE_CURVES[period];
                const multiplier = returnPct / baseCurve[baseCurve.length - 1];
                const dataPoints = baseCurve.map(pt => parseFloat((pt * multiplier).toFixed(2)));
                
                seriesData.push({
                    name: fund.name,
                    data: dataPoints
                });
            }
        });
        
        // Render inactive state alerts if any fund was filtered out
        errors.forEach(err => {
            alertArea.innerHTML += `
                <div class="inactive-state-alert">
                    <i class="fa-solid fa-triangle-exclamation"></i> ${err}
                </div>
            `;
        });
        
        if (seriesData.length === 0) {
            plotArea.innerHTML = "<p style='font-size: 12px; color: var(--text-muted); text-align:center; padding: 20px;'>No active funds selected for this timeline.</p>";
            return;
        }
        
        // Dynamic horizontal timeline dates builder
        const timelineYears = parseInt(period.replace('Y', ''));
        const dates = [];
        const currentYear = new Date().getFullYear();
        for (let i = timelineYears; i >= 0; i--) {
            dates.push(`Jan ${currentYear - i}`);
        }
        
        const options = {
            series: seriesData,
            chart: {
                type: 'line',
                height: 240,
                toolbar: { show: false },
                animations: { enabled: true, easing: 'easeinout', speed: 800 }
            },
            stroke: { curve: 'smooth', width: 3 },
            colors: ['#00e5ff', '#0088ff', '#feb019'], // Sleek HSL accents
            grid: {
                borderColor: 'rgba(255,255,255,0.05)',
                xaxis: { lines: { show: true } }
            },
            xaxis: {
                categories: dates.slice(0, seriesData[0].data.length),
                labels: { style: { colors: '#8a8f9d', fontSize: '10px' } }
            },
            yaxis: {
                labels: {
                    style: { colors: '#8a8f9d', fontSize: '10px' },
                    formatter: (val) => `${val}%`
                }
            },
            tooltip: {
                shared: true, // Unified shared tooltip on hover showing all active lines
                intersect: false,
                theme: 'dark',
                y: {
                    formatter: (val) => `${val.toFixed(2)}% Return`
                }
            }
        };
        
        const chart = new ApexCharts(plotArea, options);
        chart.render();
    };
    
    // 3. Trigger initial rendering (3Y default)
    renderApexPlot("3Y");
    
    // 4. Setup timeline toggle buttons click events
    document.getElementById(`tabs-${chartId}`).querySelectorAll(".timeline-tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            // Remove active classes
            document.getElementById(`tabs-${chartId}`).querySelectorAll(".timeline-tab-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            const selectedPeriod = btn.getAttribute("data-period");
            renderApexPlot(selectedPeriod);
        });
    });
}

// State variables for transactions
let userTransactions = [];
let isBrokerConnected = false;
let connectedBrokerName = null;
let selectedBroker = null;
let activeHistoryFilter = 'All';

function initTransactionTracking() {
    const connectModal = document.getElementById("broker-connect-modal");
    const historyModal = document.getElementById("all-transactions-modal");
    
    const btnCloseConnect = document.getElementById("btn-close-connect");
    const btnCancelConnect = document.getElementById("btn-cancel-connect");
    const btnConfirmConnect = document.getElementById("btn-confirm-connect");
    const consentCheckbox = document.getElementById("consent-checkbox");
    const brokerButtons = document.querySelectorAll(".broker-option-btn");
    
    const btnCloseHistory = document.getElementById("btn-close-history");
    const btnDisconnectAction = document.getElementById("btn-disconnect-broker-action");
    const filterTabButtons = document.querySelectorAll(".history-tab-btn");
    
    // Initial State Fetch
    fetchTransactionsState();
    
    // Broker Connect Selection Interactions
    brokerButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            brokerButtons.forEach(b => b.classList.remove("selected"));
            btn.classList.add("selected");
            selectedBroker = btn.getAttribute("data-broker");
            checkConnectionEligibility();
        });
    });
    
    // Consent checkbox state change
    consentCheckbox.addEventListener("change", () => {
        checkConnectionEligibility();
    });
    
    function checkConnectionEligibility() {
        if (selectedBroker && consentCheckbox.checked) {
            btnConfirmConnect.classList.remove("disabled");
            btnConfirmConnect.removeAttribute("disabled");
        } else {
            btnConfirmConnect.classList.add("disabled");
            btnConfirmConnect.setAttribute("disabled", "true");
        }
    }
    
    // Confirm connection click handler
    btnConfirmConnect.addEventListener("click", async () => {
        if (!selectedBroker || !consentCheckbox.checked) return;
        
        btnConfirmConnect.classList.add("disabled");
        btnConfirmConnect.innerText = "Connecting...";
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/transactions/connect`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ broker: selectedBroker })
            });
            
            if (!response.ok) {
                throw new Error("Failed to connect broker.");
            }
            
            const payload = await response.json();
            isBrokerConnected = payload.connected;
            connectedBrokerName = payload.broker;
            userTransactions = payload.transactions;
            
            // Close modal
            connectModal.classList.remove("active");
            
            // Update UI
            updateTransactionsUI();
            
        } catch (error) {
            console.error(error);
            alert("Error linking broker. Please verify the backend service is active.");
        } finally {
            btnConfirmConnect.classList.remove("disabled");
            btnConfirmConnect.innerText = "Authorize & Connect";
        }
    });
    
    // Modal Open/Close wiring
    const showConnectModal = () => {
        // Reset selections
        selectedBroker = null;
        brokerButtons.forEach(b => b.classList.remove("selected"));
        consentCheckbox.checked = false;
        checkConnectionEligibility();
        connectModal.classList.add("active");
    };
    
    btnCloseConnect.addEventListener("click", () => connectModal.classList.remove("active"));
    btnCancelConnect.addEventListener("click", () => connectModal.classList.remove("active"));
    
    // History Modal close
    btnCloseHistory.addEventListener("click", () => historyModal.classList.remove("active"));
    
    // Filter history clicks
    filterTabButtons.forEach(tab => {
        tab.addEventListener("click", () => {
            filterTabButtons.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            activeHistoryFilter = tab.getAttribute("data-filter");
            renderFullTransactionsHistory();
        });
    });
    
    // Disconnect broker click action
    btnDisconnectAction.addEventListener("click", async () => {
        if (!confirm("Are you sure you want to disconnect your broker and revoke transaction tracking permissions?")) {
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/transactions/disconnect`, {
                method: "POST"
            });
            if (response.ok) {
                const payload = await response.json();
                isBrokerConnected = payload.connected;
                connectedBrokerName = payload.broker;
                userTransactions = payload.transactions;
                
                historyModal.classList.remove("active");
                updateTransactionsUI();
            }
        } catch (error) {
            console.error(error);
        }
    });
    
    // Expose dynamic modal open triggers to document
    document.addEventListener("click", (e) => {
        if (e.target.closest(".btn-link-broker")) {
            showConnectModal();
        }
        if (e.target.closest("#btn-see-all-transactions-trigger") || e.target.closest("#btn-filter-transactions-trigger")) {
            activeHistoryFilter = 'All';
            filterTabButtons.forEach(t => {
                if (t.getAttribute("data-filter") === 'All') t.classList.add("active");
                else t.classList.remove("active");
            });
            renderFullTransactionsHistory();
            historyModal.classList.add("active");
        }
        if (e.target.closest(".suggested-followup-btn")) {
            const btn = e.target.closest(".suggested-followup-btn");
            const query = btn.getAttribute("data-query");
            submitChatQuery(query);
        }
    });
}

async function fetchTransactionsState() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/transactions`);
        if (response.ok) {
            const payload = await response.json();
            isBrokerConnected = payload.connected;
            connectedBrokerName = payload.broker;
            userTransactions = payload.transactions;
            updateTransactionsUI();
        }
    } catch (error) {
        console.warn("Backend transactions API not available, loading fallback offline state.");
        updateTransactionsUI();
    }
}

function updateTransactionsUI(filterText = "") {
    const listWrapper = document.getElementById("transactions-list-wrapper");
    if (!listWrapper) return;
    
    listWrapper.innerHTML = "";
    
    if (!isBrokerConnected) {
        // Disconnected state promo
        listWrapper.innerHTML = `
            <div class="link-broker-promo-card">
                <p>Allow WealthSearchAI to track transactions with your permission from your original broking app.</p>
                <button class="btn-link-broker">
                    <i class="fa-solid fa-link"></i> Connect Broking App
                </button>
            </div>
        `;
    } else {
        const term = filterText.toLowerCase().trim();
        const filtered = term 
            ? userTransactions.filter(t => 
                t.fund_name.toLowerCase().includes(term) ||
                t.date.toLowerCase().includes(term)
              )
            : userTransactions;
            
        if (filtered.length === 0) {
            listWrapper.innerHTML = `
                <p style="text-align: center; color: var(--text-grey); font-size: 12px; padding: 20px 0;">
                    No matching transactions found.
                </p>
            `;
            return;
        }
        
        // Connected list state (up to 3 recent items)
        const recentItems = filtered.slice(0, 3);
        let itemsHtml = "";
        
        recentItems.forEach(t => {
            const isPos = t.amount >= 0;
            const sign = isPos ? "+" : "-";
            const amtClass = isPos ? "amount-positive" : "amount-negative";
            const formattedAmt = Math.abs(t.amount).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            
            itemsHtml += `
                <div class="transaction-item-card">
                    <div class="trans-row-top">
                        <span class="trans-title">${t.type}: ${t.fund_name}</span>
                        <span class="trans-amount ${amtClass}">${sign}₹${formattedAmt}</span>
                    </div>
                    <div class="trans-row-bottom">
                        <span>${t.date}</span>
                        <span class="trans-status-badge">
                            <span class="status-dot dot-${t.status.toLowerCase()}"></span>
                            ${t.status}
                        </span>
                    </div>
                </div>
            `;
        });
        
        // Append See All footer row
        itemsHtml += `
            <div class="transactions-aside-footer">
                <button class="btn-see-all-transactions" id="btn-see-all-transactions-trigger">
                    See All <i class="fa-solid fa-chevron-right"></i>
                </button>
                <button class="btn-filter-transactions" id="btn-filter-transactions-trigger" title="Filter / Manage">
                    <i class="fa-solid fa-sliders"></i>
                </button>
            </div>
        `;
        
        listWrapper.innerHTML = itemsHtml;
    }
}

function renderFullTransactionsHistory() {
    const listContainer = document.getElementById("transactions-full-list-container");
    if (!listContainer) return;
    
    listContainer.innerHTML = "";
    
    const searchInput = document.getElementById("sidebar-search-input");
    const term = searchInput ? searchInput.value.toLowerCase().trim() : "";
    
    const filtered = userTransactions.filter(t => {
        const matchesTab = activeHistoryFilter === 'All' || t.type.toLowerCase() === activeHistoryFilter.toLowerCase();
        const matchesSearch = !term || 
            t.fund_name.toLowerCase().includes(term) ||
            t.date.toLowerCase().includes(term);
        return matchesTab && matchesSearch;
    });
    
    if (filtered.length === 0) {
        listContainer.innerHTML = `
            <p style="text-align: center; color: var(--text-muted); font-size: 13px; padding: 40px 0;">
                No ${activeHistoryFilter === 'All' ? '' : activeHistoryFilter + ' '}transactions found.
            </p>
        `;
        return;
    }
    
    filtered.forEach(t => {
        const isPos = t.amount >= 0;
        const sign = isPos ? "+" : "-";
        const amtClass = isPos ? "amount-positive" : "amount-negative";
        const formattedAmt = Math.abs(t.amount).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        
        const card = document.createElement("div");
        card.className = "transaction-item-card";
        card.innerHTML = `
            <div class="trans-row-top">
                <span class="trans-title">${t.type}: ${t.fund_name}</span>
                <span class="trans-amount ${amtClass}">${sign}₹${formattedAmt}</span>
            </div>
            <div class="trans-row-bottom">
                <span>${t.date}</span>
                <span class="trans-status-badge">
                    <span class="status-dot dot-${t.status.toLowerCase()}"></span>
                    ${t.status}
                </span>
            </div>
        `;
        listContainer.appendChild(card);
    });
}
