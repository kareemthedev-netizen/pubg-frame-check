// ========================================
// db is defined in firebase-config.js (DO NOT redeclare)
// ========================================

let devices = [];
let currentFilter = "all";
let currentSearch = "";
let currentSort = "default";
let currentPriceFilter = "all";

// ========================================
// دوال مساعدة عامة
// ========================================

function showToast(message, isError = false) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.style.backgroundColor = isError ? "#e74c3c" : "#27ae60";
    toast.textContent = message;
    toast.style.display = "block";
    setTimeout(() => { toast.style.display = "none"; }, 3000);
}

function formatFPS(fps) {
    if (fps === "غير مدعوم") return `<span class="fps-low">❌ غير مدعوم</span>`;
    let fpsClass = "fps-low";
    if (fps === 120) fpsClass = "fps-120";
    else if (fps === 90) fpsClass = "fps-90";
    else if (fps === 60) fpsClass = "fps-60";
    return `<span class="${fpsClass}">✅ ${fps} FPS</span>`;
}

function getPerformanceScore(maxFPS) {
    if (maxFPS === 120) return { score: 100, text: "🔥 ممتاز - 120 FPS", color: "#2ecc71" };
    if (maxFPS === 90) return { score: 80, text: "🎯 جيد جداً - 90 FPS", color: "#f39c12" };
    if (maxFPS === 60) return { score: 60, text: "📱 متوسط - 60 FPS", color: "#3498db" };
    return { score: 40, text: "⚠️ ضعيف", color: "#e74c3c" };
}

function toggleTheme() {
    document.body.classList.toggle("light-mode");
    let btn = document.getElementById("themeToggle");
    if (btn) {
        if (document.body.classList.contains("light-mode")) {
            btn.textContent = "☀️";
            btn.style.background = "#fff";
            btn.style.color = "#1a1a2e";
        } else {
            btn.textContent = "🌙";
            btn.style.background = "rgba(255,255,255,0.1)";
            btn.style.color = "#fff";
        }
    }
    localStorage.setItem("pubgTheme", document.body.classList.contains("light-mode") ? "light" : "dark");
}

function closeModal() { 
    const modal = document.getElementById("quickModal");
    if (modal) modal.style.display = "none"; 
}

function shareDevice(id) {
    let device = devices.find(d => d.id === id);
    if (!device) return;
    let text = `📱 ${device.brand} ${device.model}\n⚡ ${device.maxFPS} FPS\n📺 ${device.screenHz}Hz\n💰 ${device.priceEGP?.toLocaleString() || "غير محدد"} جنيه`;
    if (navigator.share) navigator.share({ title: `${device.brand} ${device.model}`, text: text });
    else { navigator.clipboard.writeText(text); showToast("✅ تم نسخ معلومات الجهاز"); }
}

function showDeviceDetails(id) {
    let device = devices.find(d => d.id === id);
    if (!device) return;
    
    // تسجيل المشاهدة (للأكثر مشاهدة)
    if (typeof addView === 'function') addView(id);
    
    let perf = getPerformanceScore(device.maxFPS);
    let body = document.getElementById("modalBody");
    if (!body) return;
    
    body.innerHTML = `
        <div class="modal-device-header">
            <img src="${device.image}" onerror="this.src='https://placehold.co/100x100/1a1a2e/e74c3c?text=📱'">
            <h2>${device.brand} ${device.model}</h2>
            <div class="perf-bar"><div class="perf-fill" style="width:${perf.score}%; background:${perf.color};"></div></div>
            <p style="color:${perf.color}">${perf.text}</p>
            <p>💰 ${device.priceEGP?.toLocaleString() || "غير محدد"} جنيه</p>
        </div>
        <table class="detail-table">
            <tr><td class="setting-name">📺 الشاشة</td><td><strong>${device.screenHz}Hz</strong></td></tr>
            <tr><td class="setting-name">⚡ أقصى فريم</td><td><strong style="color:${perf.color}">${device.maxFPS} FPS</strong></td></tr>
        </table>
        <h3>🎮 الإعدادات</h3>
        <table class="detail-table">
            <tr><td class="setting-name">🎮 Smooth</td><td>${formatFPS(device.graphics.smooth)}</td></tr>
            <tr><td class="setting-name">⚖️ Balanced</td><td>${formatFPS(device.graphics.balanced)}</td></tr>
            <tr><td class="setting-name">🎬 HD</td><td>${formatFPS(device.graphics.hd)}</td></tr>
            <tr><td class="setting-name">🌟 HDR</td><td>${formatFPS(device.graphics.hdr)}</td></tr>
        </table>
        <div style="display:flex; gap:10px; margin-top:20px;">
            <button onclick="closeModal()" style="flex:1; background:#e74c3c; border:none; padding:10px; border-radius:25px; color:#fff;">إغلاق</button>
            <button onclick="shareDevice('${device.id}'); closeModal();" style="flex:1; background:#27ae60; border:none; padding:10px; border-radius:25px; color:#fff;">مشاركة</button>
        </div>
    `;
    const modal = document.getElementById("quickModal");
    if (modal) modal.style.display = "flex";
}

// ========================================
// تحميل الأجهزة من Firebase
// ========================================

async function loadDevicesFromFirebase() {
    try {
        const snapshot = await db.collection("devices").get();
        devices = [];
        snapshot.forEach(doc => devices.push({ id: doc.id, ...doc.data() }));
        
        const path = window.location.pathname;
        
        if (path.includes("popular.html")) {
            renderPopularDevices();
        } else if (path.includes("latest.html")) {
            renderLatestDevices();
        } else if (path.includes("best-value.html")) {
            renderBestValueDevices();
        } else if (path.includes("guide.html")) {
            initGuidePage();
        } else if (path.includes("faq.html")) {
            initFaqPage();
        } else {
            // index.html
            if (document.getElementById("totalDevices")) updateHeaderStats();
            renderDevices();
            initHomePage();
        }
        
        showToast(`✅ تم تحميل ${devices.length} جهاز`);
    } catch (error) {
        console.error(error);
        showToast("❌ فشل تحميل البيانات", true);
    }
}

// ========================================
// عرض الأجهزة (الصفحة الرئيسية)
// ========================================

function renderDevices() {
    let filtered = [...devices];
    
    if (currentFilter === "120") filtered = filtered.filter(d => d.maxFPS === 120);
    else if (currentFilter === "90") filtered = filtered.filter(d => d.maxFPS === 90);
    else if (currentFilter === "60") filtered = filtered.filter(d => d.maxFPS === 60);
    else if (currentFilter === "flagship") filtered = filtered.filter(d => d.category === "flagship");
    else if (currentFilter === "midrange") filtered = filtered.filter(d => d.category === "midrange");
    else if (currentFilter === "tablet") filtered = filtered.filter(d => d.category === "tablet");
    
    if (currentPriceFilter !== "all") {
        if (currentPriceFilter === "budget") filtered = filtered.filter(d => d.priceEGP < 10000);
        else if (currentPriceFilter === "mid") filtered = filtered.filter(d => d.priceEGP >= 10000 && d.priceEGP <= 30000);
        else if (currentPriceFilter === "premium") filtered = filtered.filter(d => d.priceEGP > 30000);
    }
    
    if (currentSearch.trim()) {
        let term = currentSearch.toLowerCase();
        filtered = filtered.filter(d => d.brand.toLowerCase().includes(term) || d.model.toLowerCase().includes(term));
    }
    
    if (currentSort === "fps_desc") filtered.sort((a, b) => b.maxFPS - a.maxFPS);
    else if (currentSort === "price_asc") filtered.sort((a, b) => (a.priceEGP || 0) - (b.priceEGP || 0));
    else if (currentSort === "price_desc") filtered.sort((a, b) => (b.priceEGP || 0) - (a.priceEGP || 0));
    
    const resultsSpan = document.getElementById("resultsCount");
    if (resultsSpan) resultsSpan.textContent = `📱 ${filtered.length} جهاز`;
    
    const grid = document.getElementById("devicesGrid");
    if (!grid) return;
    
    if (filtered.length === 0) {
        grid.innerHTML = `<div style="text-align:center; padding:60px;">🔍 لا توجد أجهزة</div>`;
        return;
    }
    
    grid.innerHTML = filtered.map(device => {
        let perf = getPerformanceScore(device.maxFPS);
        let warning = device.screenHz > device.maxFPS;
        return `
            <div class="device-card" onclick="showDeviceDetails('${device.id}')">
                <div class="card-image">
                    <img src="${device.image}" onerror="this.src='https://placehold.co/400x200/1a1a2e/e74c3c?text=📱'">
                    <span class="fps-badge">⚡ ${device.maxFPS} FPS</span>
                    <span class="price-badge">💰 ${device.priceEGP?.toLocaleString() || "?"} EGP</span>
                </div>
                <div class="card-content">
                    <div class="card-title"><h3>${device.brand} ${device.model}</h3><span class="hz-badge">${device.screenHz}Hz</span></div>
                    <div class="perf-bar"><div class="perf-fill" style="width:${perf.score}%; background:${perf.color};"></div></div>
                    <div class="perf-text" style="color:${perf.color}">${perf.text}</div>
                    ${warning ? `<div class="warning-badge">⚠️ شاشة ${device.screenHz}Hz لكن ${device.maxFPS} FPS فقط</div>` : ''}
                </div>
            </div>
        `;
    }).join("");
}

function updateHeaderStats() {
    const total = document.getElementById("totalDevices");
    const topFPS = document.getElementById("topFPS");
    const bestDevice = document.getElementById("bestDevice");
    const avgFPS = document.getElementById("avgFPS");
    
    if (total) total.textContent = devices.length;
    if (topFPS) topFPS.textContent = Math.max(...devices.map(d => d.maxFPS), 0);
    if (avgFPS) {
        let avg = Math.round(devices.reduce((s, d) => s + d.maxFPS, 0) / (devices.length || 1));
        avgFPS.textContent = avg || 0;
    }
    let best = devices.reduce((max, d) => d.maxFPS > max.maxFPS ? d : max, devices[0]);
    if (bestDevice) bestDevice.textContent = best ? `${best.brand} ${best.model}` : "-";
}

function initHomePage() {
    if (document.getElementById("totalDevices")) updateHeaderStats();
    renderDevices();
    
    document.querySelectorAll(".chip").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".chip").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentFilter = btn.getAttribute("data-filter");
            renderDevices();
        });
    });
    
    const priceFilter = document.getElementById("priceFilter");
    if (priceFilter) priceFilter.addEventListener("change", (e) => { currentPriceFilter = e.target.value; renderDevices(); });
    const sortSelect = document.getElementById("sortSelect");
    if (sortSelect) sortSelect.addEventListener("change", (e) => { currentSort = e.target.value; renderDevices(); });
    const searchBtn = document.getElementById("searchBtn");
    const searchInput = document.getElementById("searchInput");
    const clearBtn = document.getElementById("clearSearch");
    
    if (searchBtn) searchBtn.onclick = () => { currentSearch = searchInput?.value || ""; renderDevices(); };
    if (searchInput) searchInput.onkeypress = (e) => { if (e.key === "Enter") { currentSearch = searchInput.value; renderDevices(); } };
    if (clearBtn) clearBtn.onclick = () => { if (searchInput) searchInput.value = ""; currentSearch = ""; renderDevices(); showToast("✅ تم مسح البحث"); };
}

// ========================================
// الصفحات الجديدة
// ========================================

// 1. الأكثر مشاهدة (Popular)
function renderPopularDevices() {
    let sorted = [...devices];
    sorted.sort((a, b) => (b.views || 0) - (a.views || 0));
    const grid = document.getElementById("popularGrid");
    if (!grid) return;
    if (sorted.length === 0) { grid.innerHTML = "<div style='text-align:center; padding:60px;'>لا توجد أجهزة</div>"; return; }
    grid.innerHTML = sorted.map(device => {
        let perf = getPerformanceScore(device.maxFPS);
        return `<div class="device-card" onclick="showDeviceDetails('${device.id}')">
            <div class="card-image"><img src="${device.image}" onerror="this.src='https://placehold.co/400x200/1a1a2e/e74c3c?text=📱'"><span class="fps-badge">⚡ ${device.maxFPS} FPS</span><span class="price-badge">💰 ${device.priceEGP?.toLocaleString() || "?"} EGP</span></div>
            <div class="card-content"><div class="card-title"><h3>${device.brand} ${device.model}</h3><span class="hz-badge">${device.screenHz}Hz</span></div>
            <div class="perf-bar"><div class="perf-fill" style="width:${perf.score}%; background:${perf.color};"></div></div><div class="perf-text" style="color:${perf.color}">${perf.text}</div></div>
        </div>`;
    }).join('');
}

// 2. أحدث الأجهزة (Latest)
function renderLatestDevices() {
    let sorted = [...devices];
    sorted.sort((a, b) => new Date(b.addedDate) - new Date(a.addedDate));
    const grid = document.getElementById("latestGrid");
    if (!grid) return;
    if (sorted.length === 0) { grid.innerHTML = "<div style='text-align:center; padding:60px;'>لا توجد أجهزة</div>"; return; }
    grid.innerHTML = sorted.map(device => {
        let perf = getPerformanceScore(device.maxFPS);
        return `<div class="device-card" onclick="showDeviceDetails('${device.id}')">
            <div class="card-image"><img src="${device.image}" onerror="this.src='https://placehold.co/400x200/1a1a2e/e74c3c?text=📱'"><span class="fps-badge">⚡ ${device.maxFPS} FPS</span><span class="price-badge">💰 ${device.priceEGP?.toLocaleString() || "?"} EGP</span></div>
            <div class="card-content"><div class="card-title"><h3>${device.brand} ${device.model}</h3><span class="hz-badge">${device.screenHz}Hz</span></div>
            <div class="perf-bar"><div class="perf-fill" style="width:${perf.score}%; background:${perf.color};"></div></div><div class="perf-text" style="color:${perf.color}">${perf.text}</div></div>
        </div>`;
    }).join('');
}

// 3. الأكثر توفيراً (Best Value)
function renderBestValueDevices() {
    let sorted = [...devices];
    sorted.sort((a, b) => (b.maxFPS / (b.priceEGP || 1)) - (a.maxFPS / (a.priceEGP || 1)));
    const grid = document.getElementById("bestValueGrid");
    if (!grid) return;
    if (sorted.length === 0) { grid.innerHTML = "<div style='text-align:center; padding:60px;'>لا توجد أجهزة</div>"; return; }
    grid.innerHTML = sorted.map(device => {
        let perf = getPerformanceScore(device.maxFPS);
        return `<div class="device-card" onclick="showDeviceDetails('${device.id}')">
            <div class="card-image"><img src="${device.image}" onerror="this.src='https://placehold.co/400x200/1a1a2e/e74c3c?text=📱'"><span class="fps-badge">⚡ ${device.maxFPS} FPS</span><span class="price-badge">💰 ${device.priceEGP?.toLocaleString() || "?"} EGP</span></div>
            <div class="card-content"><div class="card-title"><h3>${device.brand} ${device.model}</h3><span class="hz-badge">${device.screenHz}Hz</span></div>
            <div class="perf-bar"><div class="perf-fill" style="width:${perf.score}%; background:${perf.color};"></div></div><div class="perf-text" style="color:${perf.color}">${perf.text}</div></div>
        </div>`;
    }).join('');
}

// 4. دليل الشراء (Guide)
function initGuidePage() {
    // لا يحتاج أي كود إضافي، كل المحتوى ثابت في HTML
}

// 5. الأسئلة الشائعة (FAQ)
function initFaqPage() {
    document.querySelectorAll('.faq-question').forEach(q => {
        q.addEventListener('click', () => {
            const parent = q.parentElement;
            parent.classList.toggle('active');
        });
    });
}

// تسجيل المشاهدات (للأكثر مشاهدة)
async function addView(deviceId) {
    try {
        const deviceRef = db.collection("devices").doc(deviceId);
        await deviceRef.update({
            views: firebase.firestore.FieldValue.increment(1)
        });
    } catch (error) {
        console.error("Error adding view:", error);
    }
}

// ========================================
// التهيئة العامة
// ========================================

function init() {
    const closeBtn = document.querySelector(".close-modal");
    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    
    window.onclick = (e) => { if (e.target === document.getElementById("quickModal")) closeModal(); };
    
    const themeBtn = document.getElementById("themeToggle");
    if (themeBtn) themeBtn.addEventListener("click", toggleTheme);
    
    if (localStorage.getItem("pubgTheme") === "light") {
        document.body.classList.add("light-mode");
        const btn = document.getElementById("themeToggle");
        if (btn) { btn.textContent = "☀️"; btn.style.background = "#fff"; btn.style.color = "#1a1a2e"; }
    }
}

// بدء التشغيل
document.addEventListener("DOMContentLoaded", async () => {
    if (typeof firebase !== 'undefined' && firebase.firestore) {
        await loadDevicesFromFirebase();
        init();
    } else {
        console.error("Firebase not loaded");
        showToast("❌ خطأ في تحميل قاعدة البيانات", true);
    }
});