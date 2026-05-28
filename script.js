// ========================================
// المتغيرات العامة
// ========================================

let devices = [];
let currentFilter = "all";
let currentSearch = "";
let currentSort = "default";
let currentPriceFilter = "all";
let compareDevices = [];
let recentViewed = JSON.parse(localStorage.getItem("recentViewed")) || [];
let db;

// ========================================
// دوال مساعدة
// ========================================

function showToast(message, isError = false) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.style.backgroundColor = isError ? "#e74c3c" : "#27ae60";
    toast.textContent = message;
    toast.style.display = "block";
    setTimeout(() => {
        toast.style.display = "none";
    }, 3000);
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

function getPriceLabel(priceCategory) {
    if (priceCategory === "budget") return "💰 أقل من 300$";
    if (priceCategory === "mid") return "💵 300$ - 600$";
    return "👑 أكثر من 600$";
}

function isNewDevice(addedDate) {
    const added = new Date(addedDate);
    const now = new Date();
    const diffDays = (now - added) / (1000 * 60 * 60 * 24);
    return diffDays <= 7;
}

function sortDevices(list) {
    let sorted = [...list];
    if (currentSort === "fps_desc") {
        sorted.sort((a, b) => b.maxFPS - a.maxFPS);
    } else if (currentSort === "fps_asc") {
        sorted.sort((a, b) => a.maxFPS - b.maxFPS);
    } else if (currentSort === "name_asc") {
        sorted.sort((a, b) => (a.brand + a.model).localeCompare(b.brand + b.model));
    } else if (currentSort === "newest") {
        sorted.sort((a, b) => new Date(b.addedDate) - new Date(a.addedDate));
    }
    return sorted;
}

function updateHeaderStats() {
    const total = document.getElementById("totalDevices");
    const topFPS = document.getElementById("topFPS");
    const bestDevice = document.getElementById("bestDevice");
    const avgFPS = document.getElementById("avgFPS");
    
    if (total) total.textContent = devices.length;
    if (topFPS) topFPS.textContent = Math.max(...devices.map(d => d.maxFPS));
    if (avgFPS) {
        let avg = Math.round(devices.reduce((s, d) => s + d.maxFPS, 0) / devices.length);
        avgFPS.textContent = avg || 0;
    }
    let best = devices.reduce((max, d) => d.maxFPS > max.maxFPS ? d : max, devices[0]);
    if (bestDevice) bestDevice.textContent = best ? `${best.brand} ${best.model}` : "-";
}

function toggleTheme() {
    document.body.classList.toggle("light-mode");
    let btns = document.querySelectorAll('.pubg-btn');
    if (document.body.classList.contains("light-mode")) {
        btns.forEach(btn => { btn.textContent = "☀️"; btn.style.background = "#fff"; btn.style.color = "#1a1a2e"; });
    } else {
        btns.forEach(btn => { btn.textContent = "🌙"; btn.style.background = "rgba(255,255,255,0.1)"; btn.style.color = "#fff"; });
    }
    localStorage.setItem("pubgTheme", document.body.classList.contains("light-mode") ? "light" : "dark");
}

function shareDevice(id) {
    let device = devices.find(d => d.id === id);
    if (!device) return;
    let text = `📱 ${device.brand} ${device.model}\n⚡ أقصى فريم: ${device.maxFPS} FPS\n📺 الشاشة: ${device.screenHz}Hz\n💰 ${device.priceEGP?.toLocaleString() || "غير محدد"} جنيه`;
    if (navigator.share) {
        navigator.share({ title: `${device.brand} ${device.model}`, text: text });
    } else {
        navigator.clipboard.writeText(text);
        showToast("✅ تم نسخ معلومات الجهاز");
    }
}

function closeModal() {
    let modal = document.getElementById("quickModal");
    if (modal) modal.style.display = "none";
}

function addToRecent(deviceId) {
    recentViewed = recentViewed.filter(id => id !== deviceId);
    recentViewed.unshift(deviceId);
    if (recentViewed.length > 5) recentViewed.pop();
    localStorage.setItem("recentViewed", JSON.stringify(recentViewed));
    renderRecentViewed();
}

function renderRecentViewed() {
    const container = document.getElementById("recentViewed");
    const listContainer = document.getElementById("recentList");
    if (!container || !listContainer) return;
    
    if (recentViewed.length === 0) {
        container.style.display = "none";
        return;
    }
    
    container.style.display = "block";
    const recentDevices = recentViewed.map(id => devices.find(d => d.id === id)).filter(d => d);
    
    listContainer.innerHTML = recentDevices.map(device => `
        <div class="recent-item" onclick="showDeviceDetails('${device.id}')">
            <img src="${device.image}" onerror="this.src='https://placehold.co/80x80/1a1a2e/e74c3c?text=📱'">
            <span>${device.brand} ${device.model}</span>
            <small>${device.maxFPS} FPS</small>
        </div>
    `).join("");
}

function getRecommendations(deviceId) {
    const currentDevice = devices.find(d => d.id === deviceId);
    if (!currentDevice) return [];
    return devices.filter(d => d.id !== deviceId && d.maxFPS === currentDevice.maxFPS && d.category === currentDevice.category).slice(0, 4);
}

function renderRecommendations(deviceId) {
    const container = document.getElementById("recommendations");
    const listContainer = document.getElementById("recommendList");
    if (!container || !listContainer) return;
    
    const recommendations = getRecommendations(deviceId);
    if (recommendations.length === 0) {
        container.style.display = "none";
        return;
    }
    
    container.style.display = "block";
    listContainer.innerHTML = recommendations.map(device => `
        <div class="recommend-item" onclick="showDeviceDetails('${device.id}')">
            <img src="${device.image}" onerror="this.src='https://placehold.co/80x80/1a1a2e/e74c3c?text=📱'">
            <span>${device.brand} ${device.model}</span>
            <small>${device.maxFPS} FPS</small>
        </div>
    `).join("");
}

function showDeviceDetails(id) {
    let device = devices.find(d => d.id === id);
    if (!device) return;
    
    addToRecent(id);
    renderRecommendations(id);
    
    let perf = getPerformanceScore(device.maxFPS);
    let modal = document.getElementById("quickModal");
    let body = document.getElementById("modalBody");
    
    body.innerHTML = `
        <div class="modal-device-header">
            <img src="${device.image}" onerror="this.src='https://placehold.co/100x100/1a1a2e/e74c3c?text=📱'">
            <h2>${device.brand} ${device.model}</h2>
            <div class="perf-bar"><div class="perf-fill" style="width:${perf.score}%; background:${perf.color};"></div></div>
            <p style="color:${perf.color}">${perf.text}</p>
            <p>💰 ${device.priceEGP?.toLocaleString() || "غير محدد"} جنيه</p>
        </div>
        <table class="detail-table">
            <tr><td>📺 الشاشة</td><td><strong>${device.screenHz}Hz</strong></td></tr>
            <tr><td>⚡ أقصى فريم</td><td><strong style="color:${perf.color}">${device.maxFPS} FPS</strong></td></tr>
            <tr><td>🏷️ الفئة</td><td>${device.category === 'flagship' ? '👑 flagship' : (device.category === 'midrange' ? '📱 متوسط' : '💰 اقتصادي')}</td></tr>
        </table>
        <h3 style="margin:15px 0 10px;">🎮 الإعدادات</h3>
        <table class="detail-table">
            <tr><td>🎮 Smooth</td><td>${formatFPS(device.graphics.smooth)}</td></tr>
            <tr><td>⚖️ Balanced</td><td>${formatFPS(device.graphics.balanced)}</td></tr>
            <tr><td>🎬 HD</td><td>${formatFPS(device.graphics.hd)}</td></tr>
            <tr><td>🌟 HDR</td><td>${formatFPS(device.graphics.hdr)}</td></tr>
        </table>
        <div style="display:flex; gap:10px; margin-top:20px;">
            <button onclick="closeModal()" style="flex:1; background:#e74c3c; border:none; padding:10px; border-radius:25px; color:#fff; cursor:pointer;">إغلاق</button>
            <button onclick="shareDevice('${device.id}'); closeModal();" style="flex:1; background:#27ae60; border:none; padding:10px; border-radius:25px; color:#fff; cursor:pointer;">مشاركة</button>
        </div>
    `;
    modal.style.display = "flex";
}

function exportResults() {
    let filtered = [...devices];
    if (currentFilter === "120") filtered = filtered.filter(d => d.maxFPS === 120);
    else if (currentFilter === "90") filtered = filtered.filter(d => d.maxFPS === 90);
    else if (currentFilter === "60") filtered = filtered.filter(d => d.maxFPS === 60);
    else if (currentFilter === "flagship") filtered = filtered.filter(d => d.category === "flagship");
    else if (currentFilter === "midrange") filtered = filtered.filter(d => d.category === "midrange");
    
    if (currentPriceFilter !== "all") {
        filtered = filtered.filter(d => d.priceCategory === currentPriceFilter);
    }
    
    if (currentSearch.trim()) {
        let term = currentSearch.toLowerCase();
        filtered = filtered.filter(d => d.brand.toLowerCase().includes(term) || d.model.toLowerCase().includes(term));
    }
    
    let text = "🏆 PUBG Frame Check\n";
    text += `📅 ${new Date().toLocaleDateString('ar-EG')}\n📊 عدد الأجهزة: ${filtered.length}\n\n`;
    filtered.forEach((d, i) => {
        text += `${i+1}. ${d.brand} ${d.model} | ${d.maxFPS} FPS | ${d.screenHz}Hz | ${d.priceEGP?.toLocaleString() || "?"} EGP\n`;
    });
    let blob = new Blob([text], { type: "text/plain" });
    let link = document.createElement("a");
    link.download = "pubg_devices.txt";
    link.href = URL.createObjectURL(blob);
    link.click();
    showToast("✅ تم التصدير");
}

// ========================================
// تحميل الأجهزة من Firebase
// ========================================

async function loadDevicesFromFirebase() {
    try {
        const snapshot = await db.collection("devices").get();
        
        if (snapshot.empty) {
            console.log("No devices found, adding sample data...");
            await addSampleDevices();
            return;
        }
        
        devices = [];
        snapshot.forEach(doc => {
            devices.push({ id: doc.id, ...doc.data() });
        });
        
        updateHeaderStats();
        renderDevices();
        renderRecentViewed();
        showToast(`✅ تم تحميل ${devices.length} جهاز`);
        
    } catch (error) {
        console.error("Error loading devices:", error);
        showToast("❌ فشل تحميل البيانات", true);
    }
}

async function addSampleDevices() {
    const sampleDevices = [
        {
            brand: "OnePlus",
            model: "11 5G",
            screenHz: 120,
            maxFPS: 120,
            category: "flagship",
            priceCategory: "premium",
            priceEGP: 29999,
            image: "https://fdn2.gsmarena.com/vv/bigpic/oneplus-11-5g.jpg",
            addedDate: new Date().toISOString(),
            graphics: { smooth: 120, balanced: 90, hd: 60, hdr: 40, ultraHDR: "غير مدعوم", extremeHDR: "غير مدعوم" }
        },
        {
            brand: "Poco",
            model: "F4 GT",
            screenHz: 120,
            maxFPS: 90,
            category: "midrange",
            priceCategory: "mid",
            priceEGP: 15999,
            image: "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-poco-f4-gt.jpg",
            addedDate: new Date().toISOString(),
            graphics: { smooth: 90, balanced: 60, hd: 60, hdr: "غير مدعوم", ultraHDR: "غير مدعوم", extremeHDR: "غير مدعوم" }
        },
        {
            brand: "Samsung",
            model: "Galaxy S23 Ultra",
            screenHz: 120,
            maxFPS: 90,
            category: "flagship",
            priceCategory: "premium",
            priceEGP: 59999,
            image: "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-s23-ultra-5g.jpg",
            addedDate: new Date().toISOString(),
            graphics: { smooth: 90, balanced: 60, hd: 60, hdr: 40, ultraHDR: 40, extremeHDR: "غير مدعوم" }
        },
        {
            brand: "Xiaomi",
            model: "13T Pro",
            screenHz: 144,
            maxFPS: 90,
            category: "flagship",
            priceCategory: "mid",
            priceEGP: 26900,
            image: "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-13t-pro.jpg",
            addedDate: new Date().toISOString(),
            graphics: { smooth: 90, balanced: 60, hd: 60, hdr: 40, ultraHDR: "غير مدعوم", extremeHDR: "غير مدعوم" }
        },
        {
            brand: "iPhone",
            model: "14 Pro Max",
            screenHz: 120,
            maxFPS: 90,
            category: "flagship",
            priceCategory: "premium",
            priceEGP: 72999,
            image: "https://fdn2.gsmarena.com/vv/bigpic/apple-iphone-14-pro-max.jpg",
            addedDate: new Date().toISOString(),
            graphics: { smooth: 90, balanced: 60, hd: 60, hdr: 40, ultraHDR: 40, extremeHDR: "غير مدعوم" }
        }
    ];
    
    for (const device of sampleDevices) {
        await db.collection("devices").add(device);
    }
    
    await loadDevicesFromFirebase();
    showToast("✅ تم إضافة عينة من الأجهزة");
}

// ========================================
// عرض الأجهزة
// ========================================

function renderDevices() {
    let filtered = [...devices];
    
    if (currentFilter === "120") filtered = filtered.filter(d => d.maxFPS === 120);
    else if (currentFilter === "90") filtered = filtered.filter(d => d.maxFPS === 90);
    else if (currentFilter === "60") filtered = filtered.filter(d => d.maxFPS === 60);
    else if (currentFilter === "flagship") filtered = filtered.filter(d => d.category === "flagship");
    else if (currentFilter === "midrange") filtered = filtered.filter(d => d.category === "midrange");
    
    if (currentPriceFilter !== "all") {
        filtered = filtered.filter(d => d.priceCategory === currentPriceFilter);
    }
    
    if (currentSearch.trim()) {
        let term = currentSearch.toLowerCase();
        filtered = filtered.filter(d => d.brand.toLowerCase().includes(term) || d.model.toLowerCase().includes(term));
    }
    
    filtered = sortDevices(filtered);
    
    let resultsSpan = document.getElementById("resultsCount");
    if (resultsSpan) resultsSpan.textContent = `📱 ${filtered.length} جهاز`;
    
    let grid = document.getElementById("devicesGrid");
    if (!grid) return;
    
    if (filtered.length === 0) {
        grid.innerHTML = `<div style="text-align:center; padding:60px; color:#666;">🔍 لا توجد أجهزة</div>`;
        return;
    }
    
    grid.innerHTML = filtered.map(device => {
        let perf = getPerformanceScore(device.maxFPS);
        let warning = device.screenHz > device.maxFPS;
        let isNew = isNewDevice(device.addedDate);
        return `
            <div class="device-card" data-id="${device.id}">
                ${isNew ? '<span class="new-badge">🔥 NEW</span>' : ''}
                <div class="card-image">
                    <img src="${device.image}" onerror="this.src='https://placehold.co/400x200/1a1a2e/e74c3c?text=📱+${device.brand}+${device.model}'">
                    <span class="fps-badge">⚡ ${device.maxFPS} FPS</span>
                    <span class="category-badge">${device.category === 'flagship' ? '👑 flagship' : (device.category === 'midrange' ? '📱 متوسط' : '💰 اقتصادي')}</span>
                    <span class="price-badge">💰 ${device.priceEGP?.toLocaleString() || "?"} EGP</span>
                </div>
                <div class="card-content">
                    <div class="card-title">
                        <h3>${device.brand} ${device.model}</h3>
                        <span class="hz-badge">${device.screenHz}Hz</span>
                    </div>
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

// ========================================
// الإعلانات
// ========================================

function initAds() {
    const closeAdTop = document.getElementById("closeAdTop");
    if (closeAdTop) {
        closeAdTop.onclick = () => {
            document.getElementById("adTop").style.display = "none";
        };
    }
}

// ========================================
// التهيئة
// ========================================

function initPage() {
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
    
    let searchBtn = document.getElementById("searchBtn");
    let searchInput = document.getElementById("searchInput");
    let clearBtn = document.getElementById("clearSearch");
    let sortSelect = document.getElementById("sortSelect");
    let exportBtn = document.getElementById("exportBtn");
    let closeModalBtn = document.querySelector(".close-modal");
    
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
    if (sortSelect) {
        sortSelect.onchange = (e) => {
            currentSort = e.target.value;
            renderDevices();
        };
    }
    if (exportBtn) exportBtn.onclick = exportResults;
    if (closeModalBtn) closeModalBtn.onclick = closeModal;
    
    window.onclick = (e) => {
        if (e.target === document.getElementById("quickModal")) closeModal();
    };
}

// ========================================
// بدء التشغيل
// ========================================

document.addEventListener("DOMContentLoaded", async () => {
    if (typeof firebase !== 'undefined' && firebase.firestore) {
        db = firebase.firestore();
        await loadDevicesFromFirebase();
    } else {
        console.error("Firebase not loaded");
        showToast("❌ خطأ في تحميل قاعدة البيانات", true);
        devices = [];
    }
    
    initPage();
    initAds();
    
    let themeBtn = document.getElementById("themeToggle");
    if (themeBtn) themeBtn.addEventListener("click", toggleTheme);
    
    if (localStorage.getItem("pubgTheme") === "light") {
        document.body.classList.add("light-mode");
        document.querySelectorAll(".pubg-btn").forEach(btn => {
            btn.textContent = "☀️";
            btn.style.background = "#fff";
            btn.style.color = "#1a1a2e";
        });
    }
});