// Application JavaScript
// API Base URL
const API_BASE = 'http://localhost:5000/api';

let currentUser = null;
let currentView = "dashboard";

// Helper Functions
function showToast(msg) {
    let t = document.createElement('div');
    t.className = 'toast';
    t.innerText = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 2500);
}

function getAuthHeader() {
    const token = sessionStorage.getItem('token');
    return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
}

async function apiCall(endpoint, method, data = null) {
    const options = {
        method: method,
        headers: getAuthHeader()
    };
    if (data) {
        options.body = JSON.stringify(data);
    }
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    const result = await response.json();
    if (!response.ok) {
        if (response.status === 401) {
            sessionStorage.clear();
            window.location.reload();
        }
        throw new Error(result.error || 'Request failed');
    }
    return result;
}

function exportToCSV(data, filename) {
    if (!data || data.length === 0) {
        showToast("No data to export");
        return;
    }
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];
    for (const row of data) {
        const values = headers.map(header => {
            const val = row[header] || '';
            return `"${String(val).replace(/"/g, '""')}"`;
        });
        csvRows.push(values.join(','));
    }
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.setAttribute('download', `${filename}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showToast("CSV exported successfully");
}

function exportToPDF(htmlContent, filename) {
    const container = document.createElement('div');
    container.className = 'pdf-export-content';
    container.innerHTML = htmlContent;
    document.body.appendChild(container);
    const opt = {
        margin: [0.5, 0.5, 0.5, 0.5],
        filename: `${filename}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, letterRendering: true },
        jsPDF: { unit: 'in', format: 'a4', orientation: 'landscape' }
    };
    html2pdf().set(opt).from(container).save().then(() => {
        document.body.removeChild(container);
    });
    showToast("PDF exported successfully");
}

// Navigation
async function navigateTo(view) {
    currentView = view;
    if (view === 'dashboard') await renderDashboard();
    else if (view === 'company_profits') await renderCompanyProfits();
    else if (view === 'newsale') await renderNewSale();
    else if (view === 'history') await renderSalesHistory();
    else if (view === 'inventory') await renderInventory();
    else if (view === 'transfer') await renderStockTransfer();
    else if (view === 'products') await renderProducts();
    else if (view === 'product_balances') await renderProductBalances();
    else if (view === 'branches') await (currentUser?.role === 'admin' ? renderBranchesManagement() : renderSubmitReport());
    else if (view === 'reports') await (currentUser?.role === 'admin' ? renderAdminReports() : renderSubmitReport());
    else if (view === 'expense') await renderExpenseDeduction();
    else if (view === 'reports_submit') await renderSubmitReport();
    else if (view === 'branch_approvals') await renderStockApprovals();
    else if (view === 'check_report_status') await renderCheckReportStatus();
    else if (view === 'admin_settings') await renderAdminSettings();
    setActiveNav();
}

function setActiveNav() {
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const map = {
        dashboard: 0, company_profits: 1, newsale: 2, history: 3,
        inventory: 4, transfer: 5, products: 6, product_balances: 7,
        branches: 8, reports: 9, expense: 10, reports_submit: 11, branch_approvals: 12,
        check_report_status: 13, admin_settings: 14
    };
    const idx = map[currentView] || 0;
    const navs = document.querySelectorAll('.nav-item');
    if (navs[idx]) navs[idx].classList.add('active');
}

// Render Functions
async function renderDashboard() {
    const stats = await apiCall('/dashboard/stats', 'GET');
    const branchName = currentUser?.role === 'admin' ? "Central Admin" : (currentUser?.branch_name || "Branch");
    const html = `
        <div class="top-bar">
            <h1><i class="fas fa-chart-line"></i> Dashboard</h1>
            <div class="branch-badge">${branchName}</div>
        </div>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">Today's Sales</div>
                <div class="stat-value">Ksh ${stats.today_sales.toLocaleString()}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Total Revenue</div>
                <div class="stat-value">Ksh ${stats.total_revenue.toLocaleString()}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Low Stock Alerts</div>
                <div class="stat-value" style="color:${stats.low_stock > 0 ? '#dc2626' : '#10b981'}">${stats.low_stock}</div>
            </div>
        </div>
    `;
    document.getElementById("dynamicContent").innerHTML = html;
}

async function renderCompanyProfits() {
    if (currentUser?.role !== 'admin') {
        document.getElementById("dynamicContent").innerHTML = `<div class="restricted-msg">Admin access only</div>`;
        return;
    }
    const profits = await apiCall('/company/profits', 'GET');
    const html = `
        <div class="top-bar">
            <h1><i class="fas fa-chart-line"></i> Company Profit & Loss Statement</h1>
            <div class="branch-badge">Admin Financial View</div>
        </div>
        <div class="profit-summary-card">
            <h3><i class="fas fa-chart-pie"></i> Financial Summary (All Time)</h3>
            <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:20px;">
                <div><div class="stat-title" style="color:#cbd5e1;">Total Revenue</div><div class="big-number">Ksh ${profits.totalRevenue.toLocaleString()}</div></div>
                <div><div class="stat-title" style="color:#cbd5e1;">Gross Profit</div><div class="big-number">Ksh ${profits.grossProfit.toLocaleString()}</div></div>
                <div><div class="stat-title" style="color:#cbd5e1;">Sales Commission Paid</div><div class="big-number">Ksh ${profits.totalSalesCommission.toLocaleString()}</div></div>
                <div><div class="stat-title" style="color:#cbd5e1;">Expenses/Deductions</div><div class="big-number">Ksh ${profits.totalExpenses.toLocaleString()}</div></div>
                <div><div class="stat-title" style="color:#cbd5e1;">NET PROFIT</div><div class="big-number" style="color:#fbbf24;">Ksh ${profits.netProfit.toLocaleString()}</div></div>
            </div>
        </div>
    `;
    document.getElementById("dynamicContent").innerHTML = html;
}

async function renderProductBalances() {
    const products = await apiCall('/products', 'GET');
    const branchStock = await apiCall('/branch-stock', 'GET');
    const isAdmin = currentUser?.role === 'admin';
    
    const balanceMap = new Map();
    branchStock.forEach(entry => {
        balanceMap.set(entry.product_id, entry.quantity);
    });
    
    let html = `
        <div class="top-bar">
            <h1><i class="fas fa-balance-scale"></i> Product Balances & Current Stock</h1>
            <div class="branch-badge">${currentUser?.branch_name || "Central View"}</div>
        </div>
        <div class="section-card">
            <div class="export-buttons">
                <button class="btn-small btn-success" id="exportBalancesCSV"><i class="fas fa-file-csv"></i> Export CSV</button>
                <button class="btn-small btn-primary" id="exportBalancesPDF"><i class="fas fa-file-pdf"></i> Export PDF</button>
            </div>
            <div style="overflow-x: auto;">
                <table class="inventory-table">
                    <thead>
                        <tr><th>Product Code</th><th>Product Name</th><th>Selling Price</th><th>Cost Price</th><th>Current Balance</th><th>Threshold</th><th>Status</th></tr>
                    </thead>
                    <tbody>
    `;
    
    products.forEach(prod => {
        const qty = balanceMap.get(prod.id) || 0;
        const threshold = prod.low_stock_threshold || 5;
        const statusText = qty <= threshold ? '<span class="badge-pending">⚠️ Low Stock</span>' : '<span class="badge-approved">✓ In Stock</span>';
        html += `
            <tr>
                <td>${prod.product_code}</td>
                <td><strong>${prod.name}</strong></td>
                <td>Ksh ${prod.price.toLocaleString()}</td>
                <td>Ksh ${prod.cost.toLocaleString()}</td>
                <td style="font-weight:700;">${qty} ${qty === 1 ? 'unit' : 'units'}</td>
                <td>${threshold}</td>
                <td>${statusText}</td>
            </tr>
        `;
    });
    
    html += `</tbody></table></div></div>`;
    document.getElementById("dynamicContent").innerHTML = html;
    
    document.getElementById("exportBalancesCSV")?.addEventListener("click", () => {
        const exportData = products.map(prod => {
            const qty = balanceMap.get(prod.id) || 0;
            return {
                "Product Code": prod.product_code,
                "Product Name": prod.name,
                "Selling Price (Ksh)": prod.price,
                "Cost Price (Ksh)": prod.cost,
                "Current Balance (Qty)": qty,
                "Low Stock Threshold": prod.low_stock_threshold || 5,
                "Status": qty <= (prod.low_stock_threshold || 5) ? "Low Stock" : "In Stock"
            };
        });
        exportToCSV(exportData, `product_balances_${new Date().toISOString().split('T')[0]}`);
    });
    
    document.getElementById("exportBalancesPDF")?.addEventListener("click", () => {
        let pdfHtml = `<h1>Smart G Networks - Product Balances Report</h1><p>Generated: ${new Date().toLocaleString()}</p><table border="1"><thead><tr><th>Code</th><th>Name</th><th>Price</th><th>Cost</th><th>Balance</th><th>Status</th></tr></thead><tbody>`;
        products.forEach(prod => {
            const qty = balanceMap.get(prod.id) || 0;
            pdfHtml += `<tr><td>${prod.product_code}</td><td>${prod.name}</td><td>Ksh ${prod.price}</td><td>Ksh ${prod.cost}</td><td>${qty}</td><td>${qty <= (prod.low_stock_threshold || 5) ? "Low Stock" : "In Stock"}</td></tr>`;
        });
        pdfHtml += `</tbody></table>`;
        exportToPDF(pdfHtml, `product_balances_${new Date().toISOString().split('T')[0]}`);
    });
}

async function renderStockApprovals() {
    const approvals = await apiCall('/stock-approvals', 'GET');
    
    let html = `
        <div class="top-bar">
            <h1><i class="fas fa-check-circle"></i> Stock Transfer Approvals</h1>
            <div class="branch-badge">${currentUser?.branch_name || "Branch"}</div>
        </div>
        <div class="section-card">
            <h3>Pending Stock Approvals</h3>
            <div style="overflow-x:auto;">
                <table>
                    <thead><tr><th>Product</th><th>Quantity Added</th><th>Date</th><th>Status</th><th>Action</th></tr></thead>
                    <tbody>
    `;
    
    const pending = approvals.filter(a => a.status === 'pending');
    if (pending.length === 0) {
        html += '<tr><td colspan="5" style="text-align:center;">No pending stock transfers.</td></tr>';
    } else {
        pending.forEach(a => {
            html += `
                <tr>
                    <td><strong>${a.product_name}</strong></td>
                    <td>${a.quantity}</td>
                    <td>${new Date(a.created_at).toLocaleDateString()}</td>
                    <td><span class="badge-pending">Pending Approval</span></td>
                    <td>
                        <button class="btn-small btn-success approve-transfer" data-id="${a.id}" data-action="approved"><i class="fas fa-check"></i> Accept</button>
                        <button class="btn-small btn-danger approve-transfer" data-id="${a.id}" data-action="rejected"><i class="fas fa-times"></i> Reject</button>
                    </td>
                </tr>
            `;
        });
    }
    
    html += `</tbody></table></div></div>
        <div class="section-card"><h3>Approved & Rejected Transfers History</h3>
        <div style="overflow-x:auto;"><table><thead><tr><th>Product</th><th>Quantity</th><th>Date</th><th>Status</th></tr></thead><tbody>`;
    
    const history = approvals.filter(a => a.status !== 'pending');
    history.forEach(a => {
        html += `
            <tr>
                <td>${a.product_name}</td>
                <td>${a.quantity}</td>
                <td>${new Date(a.created_at).toLocaleDateString()}</td>
                <td><span class="${a.status === 'approved' ? 'badge-approved' : 'badge-rejected'}">${a.status === 'approved' ? 'Accepted' : 'Rejected'}</span></td>
            </tr>
        `;
    });
    
    html += `</tbody></table></div></div>`;
    document.getElementById("dynamicContent").innerHTML = html;
    
    document.querySelectorAll('.approve-transfer').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = parseInt(btn.dataset.id);
            const action = btn.dataset.action;
            await apiCall(`/stock-approvals/${id}/${action}`, 'POST');
            showToast(`Stock transfer ${action === 'approved' ? 'accepted' : 'rejected'} successfully`);
            renderStockApprovals();
        });
    });
}

async function renderNewSale() {
    const products = await apiCall('/products', 'GET');
    let saleItems = [{ productId: products[0]?.id, qty: 1 }];
    
    const renderItems = () => {
        let container = document.getElementById("saleItemsContainer");
        if (!container) return;
        if (products.length === 0) {
            container.innerHTML = '<div class="restricted-msg">No products available. Please contact admin.</div>';
            return;
        }
        container.innerHTML = saleItems.map((item, idx) => `
            <div style="display:flex;gap:12px;margin-bottom:12px;align-items:center;">
                <select data-idx="${idx}" class="saleProductSelect" style="flex:2; padding:10px; border-radius:20px; border:1px solid #e2e8f0;">
                    ${products.map(p => `<option value="${p.id}" ${p.id === item.productId ? 'selected' : ''}>${p.name} - Ksh ${p.price}</option>`)}
                </select>
                <input type="number" data-idx="${idx}" class="saleQtyInput" value="${item.qty}" style="width:100px; padding:10px; border-radius:20px; border:1px solid #e2e8f0;">
                <button class="btn-small removeSaleItem" data-idx="${idx}" style="background:#fee2e2;"><i class="fas fa-trash"></i> Remove</button>
            </div>
        `).join('');
        attachEvents();
    };
    
    const attachEvents = () => {
        document.querySelectorAll('.saleProductSelect').forEach(sel => {
            sel.addEventListener('change', (e) => {
                let idx = sel.dataset.idx;
                saleItems[idx].productId = parseInt(sel.value);
            });
        });
        document.querySelectorAll('.saleQtyInput').forEach(inp => {
            inp.addEventListener('input', (e) => {
                let idx = inp.dataset.idx;
                let val = parseInt(inp.value);
                saleItems[idx].qty = (isNaN(val) || val < 1) ? 1 : val;
                inp.value = saleItems[idx].qty;
            });
        });
        document.querySelectorAll('.removeSaleItem').forEach(btn => {
            btn.addEventListener('click', () => {
                let idx = parseInt(btn.dataset.idx);
                saleItems.splice(idx, 1);
                if (saleItems.length === 0 && products.length > 0) saleItems.push({ productId: products[0]?.id, qty: 1 });
                renderItems();
            });
        });
    };
    
    const html = `
        <div class="top-bar">
            <h1><i class="fas fa-cart-plus"></i> New Sale</h1>
            <div class="branch-badge">${currentUser?.branch_name || "Branch"}</div>
        </div>
        <div class="section-card">
            <div class="info-box"><i class="fas fa-info-circle"></i> Stock will be automatically deducted from your branch inventory when you complete the sale.</div>
            <div id="saleItemsContainer"></div>
            <div style="margin-top: 20px; display: flex; gap: 12px;">
                <button class="btn-small" id="addSaleItemBtn"><i class="fas fa-plus"></i> Add Item</button>
                <button class="btn-primary" id="completeSaleBtn"><i class="fas fa-check"></i> Complete Sale</button>
            </div>
        </div>
    `;
    document.getElementById("dynamicContent").innerHTML = html;
    renderItems();
    
    document.getElementById("addSaleItemBtn")?.addEventListener("click", () => {
        if (products.length > 0) {
            saleItems.push({ productId: products[0].id, qty: 1 });
            renderItems();
        } else {
            showToast("No products available to add");
        }
    });
    
    document.getElementById("completeSaleBtn")?.addEventListener("click", async () => {
        if (saleItems.length === 0) {
            showToast("Add at least one item to sale");
            return;
        }
        const items = saleItems.map(i => ({ product_id: i.productId, quantity: i.qty }));
        try {
            const result = await apiCall('/sales', 'POST', { items });
            showToast("Sale Completed Successfully! Stock has been deducted.");
            saleItems = [{ productId: products[0]?.id || 1, qty: 1 }];
            await navigateTo("history");
        } catch (e) {
            showToast("Error: " + e.message);
        }
    });
}

async function renderSalesHistory() {
    const sales = await apiCall('/sales', 'GET');
    const html = `
        <div class="top-bar">
            <h1><i class="fas fa-history"></i> Sales History</h1>
            <div class="branch-badge">${currentUser?.branch_name || "Branch"}</div>
        </div>
        <div class="section-card">
            <div style="overflow-x:auto;">
                <table>
                    <thead><tr><th>Date</th><th>Items</th><th>Total (Ksh)</th><th>Commission (Ksh)</th></tr></thead>
                    <tbody>
                        ${sales.map(s => `
                            <tr>
                                <td>${s.sale_date}</td>
                                <td>${s.items ? s.items.reduce((a, b) => a + b.quantity, 0) : 0} pcs</td>
                                <td>Ksh ${s.total_amount.toLocaleString()}</td>
                                <td>Ksh ${s.total_sales_commission.toLocaleString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
    document.getElementById("dynamicContent").innerHTML = html;
}

async function renderInventory() {
    const products = await apiCall('/products', 'GET');
    const branchStock = await apiCall('/branch-stock', 'GET');
    const isAdmin = currentUser?.role === 'admin';
    
    let html = `
        <div class="top-bar">
            <h1><i class="fas fa-boxes"></i> Branch Inventory</h1>
            <div class="branch-badge">${currentUser?.branch_name || "Branch"}</div>
        </div>
        <div class="section-card">
            <div style="overflow-x:auto;">
                <table class="inventory-table">
                    <thead>
                        <tr><th>Product</th><th>Price</th><th>Current Stock</th><th>Status</th></tr>
                    </thead>
                    <tbody>
    `;
    
    const stockMap = new Map();
    branchStock.forEach(s => stockMap.set(s.product_id, s.quantity));
    
    products.forEach(p => {
        const qty = stockMap.get(p.id) || 0;
        const isLowStock = qty <= (p.low_stock_threshold || 5);
        html += `
            <tr>
                <td><strong>${p.name}</strong><br><small>${p.product_code}</small></td>
                <td>Ksh ${p.price}</td>
                <td class="${isLowStock ? 'low-stock' : ''}">${qty}</td>
                <td>${isLowStock ? '<span class="badge-pending">Low Stock</span>' : 'In Stock'}</td>
            </tr>
        `;
    });
    
    html += `</tbody></table></div></div>`;
    document.getElementById("dynamicContent").innerHTML = html;
}

async function renderStockTransfer() {
    if (currentUser?.role !== 'admin') {
        document.getElementById("dynamicContent").innerHTML = `<div class="restricted-msg"><i class="fas fa-lock"></i> Stock Transfer is Admin only.</div>`;
        return;
    }
    const products = await apiCall('/products', 'GET');
    const branches = await apiCall('/branches', 'GET');
    
    const html = `
        <div class="top-bar">
            <h1><i class="fas fa-exchange-alt"></i> Stock Transfer</h1>
        </div>
        <div class="section-card">
            <div style="display:flex; gap:16px; flex-wrap:wrap;">
                <div style="flex:1;">
                    <label>Product</label>
                    <select id="transferProduct" class="edit-input">
                        ${products.map(p => `<option value="${p.id}">${p.name} (Central: ${p.central_stock})</option>`).join('')}
                    </select>
                </div>
                <div style="flex:1;">
                    <label>To Branch</label>
                    <select id="transferBranch" class="edit-input">
                        ${branches.map(b => `<option value="${b.branch_id || b.id}">${b.branch_name || b.name}</option>`).join('')}
                    </select>
                </div>
                <div style="flex:1;">
                    <label>Quantity</label>
                    <input type="number" id="transferQty" class="edit-input" placeholder="Quantity">
                </div>
                <div><button class="btn-primary" id="doTransferBtn" style="margin-top:24px;"><i class="fas fa-arrow-right"></i> Transfer</button></div>
            </div>
        </div>
    `;
    document.getElementById("dynamicContent").innerHTML = html;
    
    document.getElementById("doTransferBtn")?.addEventListener("click", async () => {
        const pid = parseInt(document.getElementById("transferProduct").value);
        const bid = parseInt(document.getElementById("transferBranch").value);
        const qty = parseInt(document.getElementById("transferQty").value);
        if (isNaN(qty) || qty <= 0) {
            showToast("Enter valid quantity");
            return;
        }
        try {
            await apiCall('/stock-transfer', 'POST', { product_id: pid, branch_id: bid, quantity: qty });
            showToast(`Transfer sent! Waiting for branch approval.`);
            renderStockTransfer();
        } catch (e) {
            showToast(e.message);
        }
    });
}

async function renderProducts() {
    const products = await apiCall('/products', 'GET');
    
    if (currentUser?.role === 'admin') {
        const html = `
            <div class="top-bar">
                <h1><i class="fas fa-boxes"></i> Manage Products</h1>
                <button class="btn-primary" id="openProductModalBtn"><i class="fas fa-plus"></i> New Product</button>
            </div>
            <div class="section-card">
                <div class="product-table-wrapper">
                    <table class="product-table">
                        <thead>
                            <tr><th>Code</th><th>Name</th><th>Selling Price</th><th>Cost Price</th><th>Sales Comm</th><th>Manager Comm</th><th>Profit/Unit</th><th>Central Stock</th><th>Actions</th></tr>
                        </thead>
                        <tbody>
                            ${products.map(p => {
                                const price = parseFloat(p.price) || 0;
                                const cost = parseFloat(p.cost) || 0;
                                const salesComm = parseFloat(p.sales_commission) || 0;
                                const managerComm = parseFloat(p.manager_commission) || 0;
                                const profit = price - cost - (salesComm + managerComm);
                                return `
                                    <tr>
                                        <td>${p.product_code}</td>
                                        <td>${p.name}</td>
                                        <td>Ksh ${price}</td>
                                        <td>Ksh ${cost}</td>
                                        <td>Ksh ${salesComm}</td>
                                        <td>Ksh ${managerComm}</td>
                                        <td class="profit-col">Ksh ${profit.toFixed(2)}</td>
                                        <td>${p.central_stock}</td>
                                        <td>
                                            <button class="btn-small btn-warning addStockBtn" data-id="${p.id}" data-name="${p.name}" data-stock="${p.central_stock}"><i class="fas fa-plus"></i> Add Stock</button>
                                            <button class="btn-small btn-danger deleteProductBtn" data-id="${p.id}">Delete</button>
                                        </td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        document.getElementById("dynamicContent").innerHTML = html;
        
        document.querySelectorAll('.deleteProductBtn').forEach(btn => {
            btn.addEventListener('click', async () => {
                if (confirm("Delete product?")) {
                    await apiCall(`/products/${parseInt(btn.dataset.id)}`, 'DELETE');
                    renderProducts();
                }
            });
        });
        
        document.querySelectorAll('.addStockBtn').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = parseInt(btn.dataset.id);
                const name = btn.dataset.name;
                const stock = btn.dataset.stock;
                document.getElementById("addStockProductName").value = name;
                document.getElementById("addStockCurrentStock").value = stock;
                document.getElementById("addStockQuantity").value = "";
                document.getElementById("addStockModal").style.display = "flex";
                window.currentProductId = id;
            });
        });
        
        document.getElementById("openProductModalBtn")?.addEventListener("click", () => {
            document.getElementById("productModal").style.display = "flex";
        });
    } else {
        const html = `
            <div class="top-bar">
                <h1><i class="fas fa-boxes"></i> Products</h1>
                <div class="branch-badge">${currentUser?.branch_name}</div>
            </div>
            <div class="section-card">
                <div class="product-table-wrapper">
                    <table class="product-table">
                        <thead><tr><th>Code</th><th>Name</th><th>Selling Price</th><th>Sales Commission</th></tr></thead>
                        <tbody>
                            ${products.map(p => `
                                <tr>
                                    <td>${p.product_code}</td>
                                    <td>${p.name}</td>
                                    <td>Ksh ${p.price}</td>
                                    <td>Ksh ${p.sales_commission}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        document.getElementById("dynamicContent").innerHTML = html;
    }
}

async function renderBranchesManagement() {
    if (currentUser?.role !== 'admin') {
        document.getElementById("dynamicContent").innerHTML = `<div class="restricted-msg">Admin access only</div>`;
        return;
    }
    const branches = await apiCall('/branches', 'GET');
    const html = `
        <div class="top-bar">
            <h1><i class="fas fa-store-alt"></i> Manage Branches</h1>
            <button class="btn-primary" id="adminCreateBranchBtn"><i class="fas fa-plus"></i> New Branch</button>
            <button class="btn-primary" id="adminResetBranchPwdBtn" style="background:#f59e0b;"><i class="fas fa-key"></i> Reset Branch Password</button>
        </div>
        <div class="section-card">
            <table>
                <thead><tr><th>ID</th><th>Branch Name</th><th>Manager</th><th>Email</th><th>Actions</th></tr></thead>
                <tbody>
                    ${branches.map(b => `
                        <tr>
                            <td>${b.id || b.branch_id}</td>
                            <td>${b.branch_name || b.name}</td>
                            <td>${b.name || b.manager}</td>
                            <td>${b.email}</td>
                            <td><button class="btn-small btn-danger deleteBranchBtn" data-id="${b.id || b.branch_id}">Delete</button></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    document.getElementById("dynamicContent").innerHTML = html;
    
    document.querySelectorAll('.deleteBranchBtn').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (confirm("Delete branch?")) {
                await apiCall(`/branches/${parseInt(btn.dataset.id)}`, 'DELETE');
                renderBranchesManagement();
            }
        });
    });
    
    document.getElementById("adminCreateBranchBtn")?.addEventListener("click", () => {
        document.getElementById("showRegisterBtn").click();
    });
    
    document.getElementById("adminResetBranchPwdBtn")?.addEventListener("click", async () => {
        const branchesList = await apiCall('/branches', 'GET');
        const select = document.getElementById("resetBranchSelect");
        select.innerHTML = branchesList.map(b => `<option value="${b.id || b.branch_id}">${b.branch_name || b.name} (${b.email})</option>`).join('');
        document.getElementById("resetBranchPwdModal").style.display = "flex";
    });
}

async function renderSubmitReport() {
    const production = await apiCall('/today-production', 'GET');
    const expenses = await apiCall('/expenses', 'GET');
    const reports = await apiCall('/reports', 'GET');
    const totalDeductions = expenses.reduce((sum, e) => sum + e.amount, 0);
    
    const html = `
        <div class="top-bar">
            <h1><i class="fas fa-file-alt"></i> Submit Daily Report</h1>
            <div class="branch-badge">${currentUser?.branch_name || "Branch"}</div>
        </div>
        <div class="section-card">
            <div class="info-box">
                <h3>Today's Performance (Auto-Fetched from Sales)</h3>
                <p><strong>Daily Production (Revenue):</strong> Ksh ${production.daily_production.toLocaleString()}</p>
                <p><strong>Sales Commission Earned:</strong> Ksh ${production.sales_commission.toLocaleString()}</p>
                <p><strong>Total Deductions:</strong> Ksh ${totalDeductions.toLocaleString()}</p>
                <hr>
                <p><strong>Amount Remaining:</strong> <span style="font-weight:700;background:#e6f7ec;padding:2px 10px;border-radius:20px;">Ksh ${(production.daily_production - production.sales_commission - totalDeductions).toLocaleString()}</span></p>
            </div>
            <div class="input-group"><label>Report Title</label><input id="reportTitle" class="edit-input" placeholder="Daily Report"></div>
            <div class="input-group"><label>Notes</label><textarea id="reportSummary" rows="2" class="edit-input"></textarea></div>
            <div class="input-group"><label>Additional Deduction Reason</label><textarea id="deductionReason" rows="2" class="edit-input"></textarea></div>
            <div class="input-group"><label>Additional Amount (Ksh)</label><input type="number" id="additionalDeduction" class="edit-input" value="0"></div>
            <button class="btn-primary" id="submitReportBtn">Submit Report for Approval</button>
        </div>
    `;
    document.getElementById("dynamicContent").innerHTML = html;
    
    document.getElementById("submitReportBtn")?.addEventListener("click", async () => {
        const title = document.getElementById("reportTitle").value;
        if (!title) return showToast("Enter title");
        const additional = parseFloat(document.getElementById("additionalDeduction").value) || 0;
        const reason = document.getElementById("deductionReason").value;
        await apiCall('/reports', 'POST', {
            title,
            summary: document.getElementById("reportSummary").value,
            daily_production: production.daily_production,
            sales_commission: production.sales_commission,
            total_deductions: totalDeductions + additional,
            deduction_reason: reason
        });
        showToast("Report submitted! Pending admin approval.");
        renderSubmitReport();
    });
}

async function renderAdminReports() {
    if (currentUser?.role !== 'admin') return;
    const reports = await apiCall('/reports', 'GET');
    
    const html = `
        <div class="top-bar">
            <h1><i class="fas fa-check-double"></i> Branch Reports Approval</h1>
        </div>
        <div class="section-card">
            <div style="overflow-x:auto;">
                <table>
                    <thead><tr><th>Branch</th><th>Title</th><th>Production</th><th>Sales Comm</th><th>Deductions</th><th>Remaining</th><th>Status</th><th>Action</th></tr></thead>
                    <tbody>
                        ${reports.map(r => {
                            const remaining = (r.daily_production || 0) - (r.sales_commission || 0) - (r.total_deductions || 0);
                            const isPending = r.status === 'pending';
                            return `
                                <tr>
                                    <td>${r.branch_name}</td>
                                    <td>${r.title}<br><small>${r.summary || ''}</small></td>
                                    <td>Ksh ${(r.daily_production || 0).toLocaleString()}</td>
                                    <td>Ksh ${(r.sales_commission || 0).toLocaleString()}</td>
                                    <td>Ksh ${(r.total_deductions || 0).toLocaleString()}<br><small>${r.deduction_reason || ''}</small></td>
                                    <td class="profit-col">Ksh ${remaining.toLocaleString()}</td>
                                    <td><span class="${r.status === 'approved' ? 'badge-approved' : (r.status === 'rejected' ? 'badge-rejected' : 'badge-pending')}">${r.status}</span></td>
                                    <td>${isPending ? `<button class="btn-small btn-success approve-btn" data-id="${r.id}" data-action="approved">Approve</button> <button class="btn-small btn-danger approve-btn" data-id="${r.id}" data-action="rejected">Reject</button>` : '-'}</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
    document.getElementById("dynamicContent").innerHTML = html;
    
    document.querySelectorAll('.approve-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = parseInt(btn.dataset.id);
            const action = btn.dataset.action;
            const comment = prompt(`Enter comment for ${action === 'approved' ? 'approval' : 'rejection'}:`);
            if (comment !== null) {
                await apiCall(`/reports/${id}/${action}`, 'POST', { admin_comment: comment });
                showToast(`Report ${action}`);
                renderAdminReports();
            }
        });
    });
}

async function renderExpenseDeduction() {
    const expenses = await apiCall('/expenses', 'GET');
    const html = `
        <div class="top-bar">
            <h1><i class="fas fa-receipt"></i> Record Expense/Shortage</h1>
        </div>
        <div class="section-card">
            <div class="input-group"><label>Amount (Ksh)</label><input type="number" id="expenseAmount" class="edit-input"></div>
            <div class="input-group"><label>Reason</label><textarea id="expenseReason" rows="2" class="edit-input"></textarea></div>
            <div class="input-group"><label>Type</label><select id="expenseType" class="edit-input"><option value="expense">Expense</option><option value="shortage">Shortage</option></select></div>
            <button class="btn-primary" id="saveExpenseBtn">Record Deduction</button>
        </div>
    `;
    document.getElementById("dynamicContent").innerHTML = html;
    
    document.getElementById("saveExpenseBtn")?.addEventListener("click", async () => {
        const amt = parseFloat(document.getElementById("expenseAmount").value);
        if (!amt) return showToast("Enter amount");
        await apiCall('/expenses', 'POST', {
            amount: amt,
            reason: document.getElementById("expenseReason").value,
            type: document.getElementById("expenseType").value
        });
        showToast("Deduction recorded");
        renderExpenseDeduction();
    });
}

// ==================== NEW FEATURES ====================
// Feature 1: Branch can check report approval status
async function renderCheckReportStatus() {
    if (currentUser?.role === 'admin') {
        document.getElementById("dynamicContent").innerHTML = `<div class="restricted-msg">This feature is for branches. Admins can view reports in the Reports section.</div>`;
        return;
    }
    
    const reports = await apiCall('/reports', 'GET');
    
    let html = `
        <div class="top-bar">
            <h1><i class="fas fa-file-check"></i> My Report Status</h1>
            <div class="branch-badge">${currentUser?.branch_name || "Branch"}</div>
        </div>
        <div class="section-card">
    `;
    
    if (reports.length === 0) {
        html += '<p style="text-align:center;color:#64748b;">No reports submitted yet.</p>';
    } else {
        html += '<div style="overflow-x:auto;"><table><thead><tr><th>Title</th><th>Submitted Date</th><th>Production</th><th>Commission</th><th>Status</th><th>Admin Comment</th></tr></thead><tbody>';
        
        reports.forEach(r => {
            const submittedDate = new Date(r.created_at).toLocaleDateString();
            const statusBadge = r.status === 'approved' ? '<span class="badge-approved">✓ Approved</span>' : 
                               (r.status === 'rejected' ? '<span class="badge-rejected">✗ Rejected</span>' : '<span class="badge-pending">⏳ Pending</span>');
            html += `
                <tr>
                    <td><strong>${r.title}</strong></td>
                    <td>${submittedDate}</td>
                    <td>Ksh ${(r.daily_production || 0).toLocaleString()}</td>
                    <td>Ksh ${(r.sales_commission || 0).toLocaleString()}</td>
                    <td>${statusBadge}</td>
                    <td>${r.admin_comment ? `<small>${r.admin_comment}</small>` : 'N/A'}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
    }
    
    html += '</div>';
    document.getElementById("dynamicContent").innerHTML = html;
}

// Feature 2: Admin can change password
async function renderAdminSettings() {
    if (currentUser?.role !== 'admin') {
        document.getElementById("dynamicContent").innerHTML = `<div class="restricted-msg">Admin access only</div>`;
        return;
    }
    
    const html = `
        <div class="top-bar">
            <h1><i class="fas fa-cog"></i> Admin Settings</h1>
            <div class="branch-badge">Administrator</div>
        </div>
        <div class="section-card">
            <h3><i class="fas fa-key"></i> Security</h3>
            <button class="btn-primary" id="openChangePasswordBtn">Change Password</button>
        </div>
        <div class="section-card">
            <h3><i class="fas fa-trash"></i> Data Management</h3>
            <button class="btn-danger" id="openResetSalesBtn">Reset Sales History</button>
        </div>
    `;
    
    document.getElementById("dynamicContent").innerHTML = html;
    
    document.getElementById("openChangePasswordBtn")?.addEventListener("click", () => {
        document.getElementById("changeAdminPasswordModal").style.display = "flex";
    });
    
    document.getElementById("openResetSalesBtn")?.addEventListener("click", async () => {
        // Load branches for reset sales modal
        try {
            const branches = await apiCall('/branches', 'GET');
            const branchSelect = document.getElementById("resetSalesBranch");
            branchSelect.innerHTML = '<option value="">-- Select Branch --</option>' + 
                branches.map(b => `<option value="${b.branch_id}">${b.branch_name}</option>`).join('');
        } catch (e) {
            console.error("Could not load branches", e);
        }
        document.getElementById("resetSalesModal").style.display = "flex";
    });
}

// Login and Initialization
async function initLoginSelect() {
    try {
        const branches = await fetch(`${API_BASE}/public/branches`).then(res => res.json());
        const select = document.getElementById("loginBranchSelect");
        select.innerHTML = '<option value="">-- Select Role --</option><option value="admin">System Administrator</option>' +
            branches.map(b => `<option value="branch_${b.branch_id}">${b.branch_name || b.name} (Branch Manager)</option>`).join('');
    } catch (e) {
        console.error('Could not load branches', e);
        const select = document.getElementById("loginBranchSelect");
        select.innerHTML = '<option value="">-- Select Role --</option><option value="admin">System Administrator</option>';
    }
}

document.getElementById("doLoginBtn").addEventListener("click", async () => {
    const email = document.getElementById("loginEmail").value;
    const roleVal = document.getElementById("loginBranchSelect").value;
    const password = document.getElementById("loginPassword").value;
    
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, role: roleVal })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error);
        
        sessionStorage.setItem('token', result.token);
        currentUser = result.user;
        
        document.getElementById("loginScreen").style.display = "none";
        document.getElementById("appWrapper").style.display = "flex";
        document.getElementById("userDisplayName").innerText = currentUser.role === 'admin' ? "Administrator" : `Mgr: ${currentUser.name}`;
        document.getElementById("adminBadge").style.display = currentUser.role === 'admin' ? 'inline-block' : 'none';
        document.getElementById("adminSettingsNav").style.display = currentUser.role === 'admin' ? 'flex' : 'none';
        document.getElementById("userBranchLabel").innerHTML = currentUser.role === 'admin' ? 'Full Access (Profit Data Visible)' : 'Branch View (Limited Data)';
        
        await navigateTo("dashboard");
    } catch (e) {
        document.getElementById("loginError").innerText = e.message;
        document.getElementById("loginError").style.display = "block";
    }
});

document.getElementById("showRegisterBtn").addEventListener("click", () => {
    document.getElementById("loginScreen").style.display = "none";
    document.getElementById("registerScreen").style.display = "flex";
});

document.getElementById("backToLoginBtn").addEventListener("click", () => {
    document.getElementById("registerScreen").style.display = "none";
    document.getElementById("loginScreen").style.display = "flex";
});

document.getElementById("doRegisterBtn").addEventListener("click", async () => {
    const token = sessionStorage.getItem('token');
    if (!token) {
        showToast("Please login as Admin first");
        document.getElementById("backToLoginBtn").click();
        return;
    }
    
    const name = document.getElementById("regBranchName").value;
    const manager = document.getElementById("regManagerName").value;
    const email = document.getElementById("regEmail").value;
    const pwd = document.getElementById("regPassword").value;
    const confirm = document.getElementById("regConfirmPassword").value;
    
    if (!name || !manager || !email || !pwd) return showToast("All fields required");
    if (pwd !== confirm) return showToast("Passwords mismatch");
    
    try {
        await apiCall('/branches', 'POST', { name, manager, email, password: pwd });
        showToast("Branch created successfully!");
        document.getElementById("registerScreen").style.display = "none";
        document.getElementById("loginScreen").style.display = "flex";
        initLoginSelect();
    } catch (e) {
        showToast(e.message);
    }
});

document.getElementById("logoutBtn").addEventListener("click", () => {
    sessionStorage.clear();
    currentUser = null;
    document.getElementById("appWrapper").style.display = "none";
    document.getElementById("loginScreen").style.display = "flex";
    document.getElementById("loginEmail").value = "";
    document.getElementById("loginPassword").value = "";
    showToast("Logged out successfully");
});

document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener("click", () => {
        if (btn.dataset.nav) navigateTo(btn.dataset.nav);
    });
});

document.getElementById("forgotPasswordBtn").addEventListener("click", () => document.getElementById("resetPasswordModal").style.display = "flex");
document.getElementById("closeResetModalBtn").addEventListener("click", () => document.getElementById("resetPasswordModal").style.display = "none");

document.getElementById("performResetBtn").addEventListener("click", async () => {
    const email = document.getElementById("resetEmail").value;
    const npwd = document.getElementById("resetNewPassword").value;
    const confirm = document.getElementById("resetConfirmPassword").value;
    if (npwd !== confirm) return showToast("Passwords don't match");
    await fetch(`${API_BASE}/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, new_password: npwd })
    });
    showToast("Password reset successful");
    document.getElementById("resetPasswordModal").style.display = "none";
});

document.getElementById("performBranchResetBtn")?.addEventListener("click", async () => {
    const branchId = parseInt(document.getElementById("resetBranchSelect").value);
    const newPwd = document.getElementById("resetBranchNewPwd").value;
    const confirm = document.getElementById("resetBranchConfirmPwd").value;
    if (!branchId) return showToast("Select a branch");
    if (!newPwd || newPwd.length < 3) return showToast("Password must be at least 3 characters");
    if (newPwd !== confirm) return showToast("Passwords don't match");
    await apiCall(`/branches/${branchId}/reset-password`, 'POST', { new_password: newPwd });
    showToast("Branch password reset successfully");
    document.getElementById("resetBranchPwdModal").style.display = "none";
});

document.getElementById("closeBranchResetModalBtn")?.addEventListener("click", () => {
    document.getElementById("resetBranchPwdModal").style.display = "none";
});

// New modal event listeners for the new features
document.getElementById("closeChangePasswordModalBtn")?.addEventListener("click", () => {
    document.getElementById("changeAdminPasswordModal").style.display = "none";
    document.getElementById("currentAdminPassword").value = "";
    document.getElementById("newAdminPassword").value = "";
    document.getElementById("confirmAdminPassword").value = "";
});

document.getElementById("performChangePasswordBtn")?.addEventListener("click", async () => {
    const currentPwd = document.getElementById("currentAdminPassword").value;
    const newPwd = document.getElementById("newAdminPassword").value;
    const confirmPwd = document.getElementById("confirmAdminPassword").value;
    const msgDiv = document.getElementById("changePasswordMessage");
    
    msgDiv.innerText = "";
    msgDiv.style.display = "none";
    
    if (!currentPwd || !newPwd) {
        msgDiv.innerText = "All fields are required";
        msgDiv.style.display = "block";
        return;
    }
    
    if (newPwd.length < 3) {
        msgDiv.innerText = "New password must be at least 3 characters";
        msgDiv.style.display = "block";
        return;
    }
    
    if (newPwd !== confirmPwd) {
        msgDiv.innerText = "New passwords don't match";
        msgDiv.style.display = "block";
        return;
    }
    
    try {
        await apiCall('/admin/change-password', 'POST', {
            current_password: currentPwd,
            new_password: newPwd
        });
        showToast("Password changed successfully!");
        document.getElementById("changeAdminPasswordModal").style.display = "none";
        document.getElementById("currentAdminPassword").value = "";
        document.getElementById("newAdminPassword").value = "";
        document.getElementById("confirmAdminPassword").value = "";
    } catch (e) {
        msgDiv.innerText = e.message;
        msgDiv.style.display = "block";
    }
});

document.getElementById("closeResetSalesModalBtn")?.addEventListener("click", () => {
    document.getElementById("resetSalesModal").style.display = "none";
    document.getElementById("resetSalesType").value = "all";
    document.getElementById("confirmResetText").value = "";
    document.getElementById("dateInputGroup").style.display = "none";
    document.getElementById("branchInputGroup").style.display = "none";
});

document.getElementById("resetSalesType")?.addEventListener("change", (e) => {
    const type = e.target.value;
    document.getElementById("dateInputGroup").style.display = type === 'date' ? 'block' : 'none';
    document.getElementById("branchInputGroup").style.display = type === 'branch' ? 'block' : 'none';
});

document.getElementById("performResetSalesBtn")?.addEventListener("click", async () => {
    const resetType = document.getElementById("resetSalesType").value;
    const confirmText = document.getElementById("confirmResetText").value;
    const msgDiv = document.getElementById("resetSalesMessage");
    
    msgDiv.innerText = "";
    msgDiv.style.display = "none";
    
    if (confirmText !== "CONFIRM") {
        msgDiv.innerText = "Please type 'CONFIRM' to proceed";
        msgDiv.style.display = "block";
        return;
    }
    
    try {
        const payload = { reset_type: resetType };
        
        if (resetType === 'date') {
            const date = document.getElementById("resetSalesDate").value;
            if (!date) {
                msgDiv.innerText = "Please select a date";
                msgDiv.style.display = "block";
                return;
            }
            payload.sale_date = date;
        } else if (resetType === 'branch') {
            const branchId = document.getElementById("resetSalesBranch").value;
            if (!branchId) {
                msgDiv.innerText = "Please select a branch";
                msgDiv.style.display = "block";
                return;
            }
            payload.branch_id = parseInt(branchId);
        }
        
        await apiCall('/admin/reset-sales', 'POST', payload);
        showToast("Sales history reset successfully!");
        document.getElementById("resetSalesModal").style.display = "none";
        document.getElementById("resetSalesType").value = "all";
        document.getElementById("confirmResetText").value = "";
        document.getElementById("dateInputGroup").style.display = "none";
        document.getElementById("branchInputGroup").style.display = "none";
    } catch (e) {
        msgDiv.innerText = e.message;
        msgDiv.style.display = "block";
    }
});

document.getElementById("saveProductBtn")?.addEventListener("click", async () => {
    const code = document.getElementById("prodCode").value;
    const name = document.getElementById("prodName").value;
    const price = parseFloat(document.getElementById("prodPrice").value);
    const cost = parseFloat(document.getElementById("prodCost").value);
    const sComm = parseFloat(document.getElementById("prodSalesComm").value) || 0;
    const mComm = parseFloat(document.getElementById("prodManagerComm").value) || 0;
    const stock = parseInt(document.getElementById("prodStock").value);
    const thresh = parseInt(document.getElementById("prodThreshold").value) || 5;
    
    if (!code || !name || isNaN(price)) return showToast("Fill required fields");
    await apiCall('/products', 'POST', {
        product_code: code, name, price, cost,
        sales_commission: sComm, manager_commission: mComm,
        central_stock: stock, low_stock_threshold: thresh
    });
    showToast("Product created");
    document.getElementById("productModal").style.display = "none";
    renderProducts();
});

document.getElementById("closeProductModalBtn")?.addEventListener("click", () => {
    document.getElementById("productModal").style.display = "none";
});

document.getElementById("confirmAddStockBtn")?.addEventListener("click", async () => {
    const qty = parseInt(document.getElementById("addStockQuantity").value);
    if (!qty || qty <= 0) return showToast("Enter valid quantity");
    if (!window.currentProductId) return showToast("Product ID not set");
    try {
        await apiCall(`/products/${window.currentProductId}/add-stock`, 'POST', { quantity: qty });
        showToast(`Added ${qty} units to stock`);
        document.getElementById("addStockModal").style.display = "none";
        document.getElementById("addStockQuantity").value = "";
        await renderProducts();
    } catch (e) {
        showToast("Error adding stock: " + e.message);
    }
});

document.getElementById("closeAddStockModalBtn")?.addEventListener("click", () => {
    document.getElementById("addStockModal").style.display = "none";
});

// Check for existing session
const token = sessionStorage.getItem('token');
if (token) {
    // Try to restore session (simplified - just show UI and let user refresh)
    document.getElementById("loginScreen").style.display = "none";
    document.getElementById("appWrapper").style.display = "flex";
    currentUser = JSON.parse(sessionStorage.getItem('user') || '{}');
    if (currentUser.name) {
        document.getElementById("userDisplayName").innerText = currentUser.role === 'admin' ? "Administrator" : `Mgr: ${currentUser.name}`;
        document.getElementById("adminBadge").style.display = currentUser.role === 'admin' ? 'inline-block' : 'none';
        document.getElementById("adminSettingsNav").style.display = currentUser.role === 'admin' ? 'flex' : 'none';
        navigateTo("dashboard");
    }
}

initLoginSelect();