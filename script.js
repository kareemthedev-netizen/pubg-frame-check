// ========================================
// db is defined in firebase-config.js as CONST
// DO NOT redeclare or reassign it
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

function sortDevices(list) {
    let sorted = [...list];
    if (currentSort === "fps_desc") sorted.sort((a, b) => b.maxFPS - a.maxFPS);
    else if (currentSort === "price_asc") sorted.sort((a, b) => (a.priceEGP || 0) - (b.priceEGP || 0));
    else if (currentSort === "price_desc") sorted.sort((a, b) => (b.priceEGP || 0) - (a.priceEGP || 0));
    return sorted;
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
            <tr><td class="setting-name">🏷️ الفئة</td><td>${device.category === 'flagship' ? '👑 flagship' : (device.category === 'midrange' ? '📱 متوسط' : (device.category === 'tablet' ? '📟 تابلت' : '💰 اقتصادي'))}</td></tr>
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
// دوال الصفحة الرئيسية (index.html)
// ========================================

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
    
    filtered = sortDevices(filtered);
    
    const resultsSpan = document.getElementById("resultsCount");
    if (resultsSpan) resultsSpan.textContent = `📱 ${filtered.length} جهاز`;
    
    const grid = document.getElementById("devicesGrid");
    if (!grid) return;
    
    if (filtered.length === 0) {
        grid.innerHTML = `<div style="text-align:center; padding:60px; color:#666;">🔍 لا توجد أجهزة</div>`;
        return;
    }
    
    grid.innerHTML = filtered.map(device => {
        let perf = getPerformanceScore(device.maxFPS);
        let warning = device.screenHz > device.maxFPS;
        return `
            <div class="device-card" data-id="${device.id}">
                <div class="card-image">
                    <img src="${device.image}" onerror="this.src='https://placehold.co/400x200/1a1a2e/e74c3c?text=📱'">
                    <span class="fps-badge">⚡ ${device.maxFPS} FPS</span>
                    <span class="category-badge">${device.category === 'flagship' ? '👑 flagship' : (device.category === 'midrange' ? '📱 متوسط' : (device.category === 'tablet' ? '📟 تابلت' : '💰 اقتصادي'))}</span>
                    <span class="price-badge">💰 ${device.priceEGP?.toLocaleString() || "?"} EGP</span>
                </div>
                <div class="card-content">
                    <div class="card-title"><h3>${device.brand} ${device.model}</h3><span class="hz-badge">${device.screenHz}Hz</span></div>
                    <table class="settings-table">
                        <tr><td class="setting-name">🎮 Smooth</td><td class="fps-value">${formatFPS(device.graphics.smooth)}</td></tr>
                        <tr><td class="setting-name">⚖️ Balanced</td><td class="fps-value">${formatFPS(device.graphics.balanced)}</td></tr>
                        <tr><td class="setting-name">🎬 HD</td><td class="fps-value">${formatFPS(device.graphics.hd)}</td></tr>
                        <tr><td class="setting-name">🌟 HDR</td><td class="fps-value">${formatFPS(device.graphics.hdr)}</td></tr>
                    </table>
                    <div class="perf-bar"><div class="perf-fill" style="width:${perf.score}%; background:${perf.color};"></div></div>
                    <div class="perf-text" style="color:${perf.color}">${perf.text}</div>
                    ${warning ? `<div style="background:rgba(231,76,60,0.15); padding:8px; border-radius:10px; font-size:0.7rem; text-align:center;">⚠️ شاشة ${device.screenHz}Hz لكن ${device.maxFPS} FPS فقط</div>` : ''}
                    <div class="card-actions">
                        <button class="view-details" data-id="${device.id}">📝 تفاصيل</button>
                        <button class="share-device" data-id="${device.id}">📤 مشاركة</button>
                    </div>
                </div>
            </div>
        `;
    }).join("");
    
    document.querySelectorAll(".view-details").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            showDeviceDetails(btn.getAttribute("data-id"));
        });
    });
    document.querySelectorAll(".share-device").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            shareDevice(btn.getAttribute("data-id"));
        });
    });
    document.querySelectorAll(".device-card").forEach(card => {
        card.addEventListener("click", () => {
            showDeviceDetails(card.getAttribute("data-id"));
        });
    });
}

function initHomePage() {
    updateHeaderStats();
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
    if (priceFilter) {
        priceFilter.addEventListener("change", (e) => {
            currentPriceFilter = e.target.value;
            renderDevices();
        });
    }
    
    const sortSelect = document.getElementById("sortSelect");
    if (sortSelect) {
        sortSelect.addEventListener("change", (e) => {
            currentSort = e.target.value;
            renderDevices();
        });
    }
    
    const searchBtn = document.getElementById("searchBtn");
    const searchInput = document.getElementById("searchInput");
    const clearBtn = document.getElementById("clearSearch");
    
    if (searchBtn) {
        searchBtn.onclick = () => {
            currentSearch = searchInput?.value || "";
            renderDevices();
        };
    }
    if (searchInput) {
        searchInput.onkeypress = (e) => {
            if (e.key === "Enter") {
                currentSearch = searchInput.value;
                renderDevices();
            }
        };
    }
    if (clearBtn) {
        clearBtn.onclick = () => {
            if (searchInput) searchInput.value = "";
            currentSearch = "";
            renderDevices();
            showToast("✅ تم مسح البحث");
        };
    }
}

// ========================================
// دوال صفحة الماركات (brands.html)
// ========================================

function renderBrands() {
    let brands = [...new Set(devices.filter(d => d.category !== "tablet").map(d => d.brand))];
    brands.sort();
    const grid = document.getElementById("brandsGrid");
    if (grid) {
        grid.innerHTML = brands.map(b => `
            <div class="brand-card" onclick="location.href='brand-devices.html?brand=${encodeURIComponent(b)}'">
                <div class="brand-icon">📱</div>
                <div class="brand-name">${b}</div>
                <div class="brand-count">${devices.filter(d => d.brand === b).length} جهاز</div>
            </div>
        `).join('');
        showToast(`✅ تم تحميل ${brands.length} ماركة`);
    }
}

// ========================================
// دوال صفحة أجهزة الماركة (brand-devices.html)
// ========================================

function renderBrandDevices(brand) {
    let filtered = devices.filter(d => d.brand === brand);
    filtered.sort((a, b) => (b.priceEGP || 0) - (a.priceEGP || 0));
    
    const title = document.getElementById("brandTitle");
    if (title) title.textContent = `📱 ${brand}`;
    
    const grid = document.getElementById("brandDevicesGrid");
    if (!grid) return;
    
    if (filtered.length === 0) {
        grid.innerHTML = "<div style='text-align:center; padding:60px; color:#666;'>لا توجد أجهزة</div>";
        return;
    }
    
    grid.innerHTML = filtered.map(device => {
        let perf = getPerformanceScore(device.maxFPS);
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
                </div>
            </div>
        `;
    }).join('');
    
    showToast(`✅ تم تحميل ${filtered.length} جهاز`);
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
        
        if (path.includes("brands.html")) {
            renderBrands();
        } else if (path.includes("brand-devices.html")) {
            const params = new URLSearchParams(window.location.search);
            const brand = params.get("brand");
            if (brand) renderBrandDevices(brand);
        } else {
            initHomePage();
        }
        
        showToast(`✅ تم تحميل ${devices.length} جهاز`);
    } catch (error) {
        console.error("Error loading devices:", error);
        showToast("❌ فشل تحميل البيانات", true);
    }
}

// ========================================
// تهيئة عامة
// ========================================

function init() {
    const closeBtn = document.querySelector(".close-modal");
    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    
    window.onclick = (e) => {
        const modal = document.getElementById("quickModal");
        if (e.target === modal) closeModal();
    };
    
    const themeBtn = document.getElementById("themeToggle");
    if (themeBtn) themeBtn.addEventListener("click", toggleTheme);
    
    if (localStorage.getItem("pubgTheme") === "light") {
        document.body.classList.add("light-mode");
        const btn = document.getElementById("themeToggle");
        if (btn) {
            btn.textContent = "☀️";
            btn.style.background = "#fff";
            btn.style.color = "#1a1a2e";
        }
    }
}

// ========================================
// بدء التشغيل
// ========================================

document.addEventListener("DOMContentLoaded", async () => {
    if (typeof firebase !== 'undefined' && firebase.firestore) {
        await loadDevicesFromFirebase();
        init();
    } else {
        console.error("Firebase not loaded");
        showToast("❌ خطأ في تحميل قاعدة البيانات", true);
    }
});