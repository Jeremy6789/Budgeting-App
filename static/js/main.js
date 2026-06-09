/**
 * MoneyMaster PRO - Core Logic
 */

let myChart = null;
let allTransactions = [];
let currentBudget = 0;

// 1. 初始化頁面
document.addEventListener('DOMContentLoaded', () => {
    // 初始化日期選擇器為今天
    const dateInput = document.getElementById('txDate');
    if (dateInput) {
        dateInput.valueAsDate = new Date();
    }

    // 獲取資料
    fetchData();

    // 綁定表單提交事件
    const form = document.getElementById('transactionForm');
    if (form) {
        form.onsubmit = saveTransaction;
    }
});

// 2. API 資料獲取
async function fetchData() {
    try {
        const res = await fetch('/api/data');
        const data = await res.json();
        
        allTransactions = data.transactions;
        currentBudget = data.budget;

        // 根據當前頁面元素決定渲染內容
        if (document.getElementById('balance')) {
            renderDashboard(data);
        }
        if (document.getElementById('fullTxList')) {
            renderHistory(allTransactions);
        }
    } catch (err) {
        console.error("資料載入失敗:", err);
    }
}

// 3. 彈窗管理 (支援 新增/編輯 模式)
function toggleModal(isEdit = false) {
    const modal = document.getElementById('addModal');
    if (!modal) return;

    if (modal.classList.contains('hidden')) {
        // 如果是開啟彈窗且非編輯模式，重置表單
        if (!isEdit) {
            document.getElementById('transactionForm').reset();
            document.getElementById('txId').value = '';
            document.getElementById('modalTitle').innerText = '新增帳目';
            document.getElementById('txDate').valueAsDate = new Date();
        }
        modal.classList.remove('hidden');
    } else {
        modal.classList.add('hidden');
    }
}

// 4. 編輯功能：將資料填入彈窗
function editTx(id) {
    const tx = allTransactions.find(t => t.id === id);
    if (!tx) return;

    // 填入隱藏 ID 與各項數值
    document.getElementById('txId').value = tx.id;
    document.getElementById('txTitle').value = tx.title;
    document.getElementById('txAmount').value = tx.amount;
    document.getElementById('txDate').value = tx.date;
    document.getElementById('txCategory').value = tx.category;
    document.getElementById('txIsNeed').checked = tx.isNeed;
    
    document.getElementById('modalTitle').innerText = '修改帳目';
    toggleModal(true); // 開啟編輯模式
}

// 5. 儲存/更新帳目
async function saveTransaction(e) {
    e.preventDefault();
    
    const id = document.getElementById('txId').value;
    const categorySelect = document.getElementById('txCategory');
    const selectedOption = categorySelect.options[categorySelect.selectedIndex];
    
    const payload = {
        title: document.getElementById('txTitle').value,
        amount: parseFloat(document.getElementById('txAmount').value),
        category: categorySelect.value,
        icon: selectedOption.getAttribute('data-icon') || 'fa-dollar-sign',
        isNeed: document.getElementById('txIsNeed').checked,
        date: document.getElementById('txDate').value
    };

    // 判斷是 PUT (更新) 還是 POST (新增)
    const url = id ? `/api/transaction/${id}` : '/api/transaction';
    const method = id ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            toggleModal();
            fetchData(); // 重新整理數據
        }
    } catch (err) {
        alert("儲存失敗，請檢查網路連線");
    }
}

// 6. 刪除帳目
async function deleteTx(id) {
    if (confirm('確定要刪除這筆紀錄嗎？')) {
        await fetch(`/api/transaction/${id}`, { method: 'DELETE' });
        fetchData();
    }
}

// 7. 設定總預算
async function setBudget() {
    const newBudget = prompt("請輸入本月總預算：", currentBudget);
    if (newBudget !== null && !isNaN(newBudget)) {
        await fetch('/api/budget', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ budget: parseFloat(newBudget) })
        });
        fetchData();
    }
}

// 8. 儀表板渲染邏輯
function renderDashboard(data) {
    const totalSpent = allTransactions.reduce((sum, tx) => sum + tx.amount, 0);
    const budget = data.budget;
    const remaining = budget - totalSpent;

    // 1. 核心數值
    document.getElementById('balance').innerText = `$${remaining.toLocaleString()}`;
    
    // 2. 總進度條
    const percent = Math.min((totalSpent / budget) * 100, 100);
    document.getElementById('progressBar').style.width = `${percent}%`;
    document.getElementById('percentText').innerText = `${Math.round(percent)}%`;

    // 3. 特色功能：計算 Needs vs Wants
    const needsAmount = allTransactions.filter(tx => tx.isNeed).reduce((sum, tx) => sum + tx.amount, 0);
    const wantsAmount = totalSpent - needsAmount;
    
    const needsPercent = totalSpent > 0 ? (needsAmount / totalSpent) * 100 : 100;
    const wantsPercent = totalSpent > 0 ? (wantsAmount / totalSpent) * 100 : 0;

    document.getElementById('needsBar').style.width = `${needsPercent}%`;
    document.getElementById('wantsBar').style.width = `${wantsPercent}%`;
    document.getElementById('needsText').innerText = `$${needsAmount.toLocaleString()}`;
    document.getElementById('wantsText').innerText = `$${wantsAmount.toLocaleString()}`;
    
    // 消費健康度 (需要越多，分數越高)
    const score = Math.round(needsPercent);
    document.getElementById('healthScore').innerText = `健康度: ${score}%`;

    // 4. 預計月底結餘 (預算 - 目前支出 - 預期之後的支出)
    const now = new Date();
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    const currentDay = now.getDate();
    const dailyRate = totalSpent / currentDay; // 平均每天花多少
    const estTotalSpent = dailyRate * lastDay; // 預估月底會花多少
    const estSaving = budget - estTotalSpent;

    const estSavingEl = document.getElementById('estSaving');
    estSavingEl.innerText = `$${Math.round(estSaving).toLocaleString()}`;
    estSavingEl.className = estSaving < 0 ? "text-lg font-bold text-red-400" : "text-lg font-bold text-indigo-400";

    renderChart();
}

// 9. 圖表渲染 (Chart.js)
function renderChart() {
    const chartCanvas = document.getElementById('mainChart');
    if (!chartCanvas) return;

    const categoryTotals = {};
    allTransactions.forEach(tx => {
        categoryTotals[tx.category] = (categoryTotals[tx.category] || 0) + tx.amount;
    });

    const ctx = chartCanvas.getContext('2d');
    if (myChart) myChart.destroy();

    myChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(categoryTotals),
            datasets: [{
                data: Object.values(categoryTotals),
                // 改為藍、綠、青色系的簡約配色
                backgroundColor: [
                    '#6366f1', // Indigo
                    '#0d9488', // Teal
                    '#3b82f6', // Blue
                    '#2dd4bf', // Teal light
                    '#818cf8', // Indigo light
                    '#94a3b8'  // Slate (用於其他)
                ],
                borderWidth: 5,
                borderColor: '#ffffff',
                hoverOffset: 10
            }]
        },
        options: {
            cutout: '80%', // 更細的圓環看起來更高級
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 25,
                        font: { size: 11, weight: '600' },
                        color: '#94a3b8'
                    }
                }
            }
        }
    });
}

// 10. 歷史紀錄渲染 (History Page)
function renderHistory(txs) {
    const list = document.getElementById('fullTxList');
    if (!list) return;
    
    list.innerHTML = txs.map(tx => {
        const tagHtml = tx.isNeed 
            ? `<span class="text-[9px] bg-teal-50 text-teal-600 px-2 py-0.5 rounded font-black ml-2 uppercase">必要</span>`
            : `<span class="text-[9px] bg-indigo-50 text-indigo-500 px-2 py-0.5 rounded font-black ml-2 uppercase">想要</span>`;

        return `
        <li class="group flex items-center p-5 bg-white rounded-[2rem] border border-slate-100 mb-3 transition-all hover:shadow-md">
            <div class="w-12 h-12 rounded-2xl bg-slate-50 flex items-center justify-center text-slate-400 mr-4 group-hover:bg-indigo-50 group-hover:text-indigo-500 transition-colors">
                <i class="fa-solid ${tx.icon || 'fa-dollar-sign'} text-lg"></i>
            </div>
            <div class="flex-1 text-left">
                <div class="flex items-center">
                    <p class="font-bold text-slate-700">${tx.title}</p>
                    ${tagHtml}
                </div>
                <p class="text-[10px] text-slate-400 font-bold mt-1">${tx.date} • ${tx.category}</p>
            </div>
            <div class="text-right">
                <p class="font-black text-slate-800">$${tx.amount.toLocaleString()}</p>
                <div class="flex space-x-3 mt-1 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onclick="editTx(${tx.id})" class="text-[10px] font-black text-indigo-400 uppercase tracking-widest">編輯</button>
                    <button onclick="deleteTx(${tx.id})" class="text-[10px] font-black text-slate-300 uppercase tracking-widest hover:text-red-400">刪除</button>
                </div>
            </div>
        </li>
        `;
    }).join('');
}

// 11. 搜尋/篩選功能
function filterTransactions() {
    const term = document.getElementById('searchInput').value.toLowerCase();
    const filtered = allTransactions.filter(tx => 
        tx.title.toLowerCase().includes(term) || 
        tx.category.toLowerCase().includes(term)
    );
    renderHistory(filtered);
}