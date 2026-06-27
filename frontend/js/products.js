// ==========================================
// 1. INITIALIZATION & DOM REFERENCES
// ==========================================
const inventoryTableBody = document.getElementById('inventory-table-body');
const productForm = document.getElementById('product-form');
const inventorySearch = document.getElementById('inventory-search');
const categoryDropdown = document.getElementById('p-category'); 

// Refill Modal Interception Controls DOM
const refillModalBackdrop = document.getElementById('refill-modal-backdrop');
const refillTargetProductDisplay = document.getElementById('refill-target-product-display');
const refillProductIdHolder = document.getElementById('refill-product-id-holder');
const refillQuantityInput = document.getElementById('refill-quantity-input');
const refillCostInput = document.getElementById('refill-cost-input');
const refillSellingInput = document.getElementById('refill-selling-input');
const refillOperationForm = document.getElementById('refill-operation-form');

// Internal global cache array layer for lookup processing
let localInventoryRosterCache = [];

document.addEventListener('DOMContentLoaded', async () => {
    // 💡 Determine base API URL safely with an explicit fallback string context
    const baseUrl = window.API_BASE_URL || 'http://127.0.0.1:8000';
    console.log("Initializing Inventory System Connection Terminal via source path:", baseUrl);

    // Load master table data stream layers up front
    await fetchMasterInventory();
    
    // Wrap dropdown sync parameters in isolated protection branches
    try {
        if (categoryDropdown) {
            await fetchCategoriesForDropdown();
        }
    } catch (catError) {
        console.error("Category parsing safety isolation tripped:", catError);
    }
    
    // Explicitly bind lifecycle events safely
    if (productForm) productForm.addEventListener('submit', handleProductCreation);
    if (refillOperationForm) refillOperationForm.addEventListener('submit', handleRefillFormSubmission);
    
    // Wire Up Hardware Barcode Scanner Global Keyboard Sniffer
    initGlobalBarcodeScannerListener();
});

// ==========================================
// 2. FETCH & DISPLAY ALL INVENTORY ITEMS
// ==========================================
async function fetchMasterInventory() {
    try {
        const baseUrl = window.API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${baseUrl}/products/`);
        const products = await response.json();

        if (response.ok) {
            localInventoryRosterCache = products; // Cache roster locally for scanner parsing
            renderInventoryTable(products);
        }
    } catch (error) {
        console.error("Inventory backend server offline error:", error);
        if (inventoryTableBody) {
            inventoryTableBody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-red-500 font-bold text-xs"><i class="fa-solid fa-triangle-exclamation mr-1"></i> Connection Error: System Terminal Backend Offline.</td></tr>`;
        }
    }
}

function renderInventoryTable(products) {
    if (!inventoryTableBody) return;
    inventoryTableBody.innerHTML = '';

    if (products.length === 0) {
        inventoryTableBody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-gray-400 font-medium text-xs">No products found.</td></tr>`;
        return;
    }

    products.forEach(product => {
        const qty = parseFloat(product.current_quantity || 0);
        const row = document.createElement('tr');
        row.className = "border-b text-xs hover:bg-gray-50/50 transition";
        row.innerHTML = `
            <td class="p-3 font-bold text-gray-500 font-mono text-center">${product.id}</td>
            <td class="p-3">
                <span class="font-bold text-gray-800">${product.name}</span>
                <p class="text-[10px] text-gray-400 font-medium">${product.brand || 'Generic'}</p>
            </td>
            <td class="p-3 font-mono text-gray-600 bg-gray-50/50 rounded font-semibold text-center">${product.barcode || '---'}</td>
            <td class="p-3 font-mono font-medium text-right">
                <span class="text-gray-400 block text-[10px]">Cost: ₹${parseFloat(product.cost_price).toFixed(2)}</span>
                <span class="text-blue-600 font-black">Sell: ₹${parseFloat(product.selling_price).toFixed(2)}</span>
            </td>
            <td class="p-3 font-mono font-bold text-center ${qty <= 5 ? 'text-red-600 bg-red-50 font-black' : 'text-gray-700'}">
                ${qty.toFixed(2)} <span class="text-[10px] text-gray-400 block">${product.unit_type || 'PCS'}</span>
            </td>
            <td class="p-3 text-center">
                <div class="flex gap-1 justify-center items-center">
                    <button class="bg-blue-600 hover:bg-blue-700 text-white px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wider shadow-sm transition" onclick="triggerQuickRestockDialog(${product.id}, '${product.name}')"><i class="fa-solid fa-plus mr-1"></i>Refill</button>
                    <button class="bg-amber-500 hover:bg-amber-600 text-white px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wider shadow-sm transition" onclick="triggerPriceUpdateDialog(${product.id}, ${product.selling_price})"><i class="fa-solid fa-tag mr-1"></i>Rate</button>
                </div>
            </td>
        `;
        inventoryTableBody.appendChild(row);
    });
}

// ==========================================
// 3. ATOMIC PRODUCT CREATION PIPELINE
// ==========================================
async function handleProductCreation(e) {
    e.preventDefault();
    
    const payload = {
        name: document.getElementById('p-name').value.trim(),
        brand: document.getElementById('p-brand').value.trim() || "Local",
        barcode: document.getElementById('p-barcode').value.trim() || null,
        unit_type: document.getElementById('p-unit-type').value,
        cost_price: parseFloat(document.getElementById('p-cost-price').value),
        selling_price: parseFloat(document.getElementById('p-selling-price').value),
        current_quantity: parseFloat(document.getElementById('p-initial-qty').value || 0),
        category_id: parseInt(categoryDropdown.value)
    };

    try {
        const baseUrl = window.API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${baseUrl}/products/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            productForm.reset();
            fetchMasterInventory();
            alert("Product successfully configured and saved!");
        } else {
            const err = await response.json();
            alert("Rejection: " + (err.detail || "Verification Error"));
        }
    } catch (error) {
        alert("Server transmission failed.");
    }
}

// ==========================================
// 4. PRICE & MODAL REFILL OPERATIONS ENGINE
// ==========================================
function triggerQuickRestockDialog(productId, productName) {
    if (!refillModalBackdrop || !refillTargetProductDisplay || !refillProductIdHolder || !refillQuantityInput) return;
    
    refillProductIdHolder.value = productId;
    refillTargetProductDisplay.innerText = productName;
    refillQuantityInput.value = '';
    
    // Find item configuration from the roster array cache layer to populate base rates
    const targetProduct = localInventoryRosterCache.find(p => p.id === productId);
    if (targetProduct) {
        if (refillCostInput) refillCostInput.value = parseFloat(targetProduct.cost_price || 0);
        if (refillSellingInput) refillSellingInput.value = parseFloat(targetProduct.selling_price || 0);
    }
    
    refillModalBackdrop.classList.remove('hidden');
    setTimeout(() => refillQuantityInput.focus(), 100);
}

function closeRefillModal() {
    if (refillModalBackdrop) refillModalBackdrop.classList.add('hidden');
}

async function handleRefillFormSubmission(e) {
    e.preventDefault();
    
    const productId = parseInt(refillProductIdHolder.value);
    const qty = parseFloat(refillQuantityInput.value);
    const costPrice = parseFloat(refillCostInput.value);
    const sellingPrice = parseFloat(refillSellingInput.value);
    
    if (isNaN(productId) || isNaN(qty) || qty <= 0 || isNaN(costPrice) || isNaN(sellingPrice)) {
        alert("Please declare realistic restock quantity and pricing parameters.");
        return;
    }

    try {
        const baseUrl = window.API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${baseUrl}/products/add-stock/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                product_id: productId, 
                quantity: qty, 
                cost_price: costPrice,
                selling_price: sellingPrice,
                notes: "Manual replenishment entry logged via console management terminal view" 
            })
        });

        if (response.ok) {
            closeRefillModal();
            fetchMasterInventory();
        } else {
            const err = await response.json();
            alert(`Refill rejected: ${err.detail || 'Malformed transaction payload parameter context.'}`);
        }
    } catch (error) {
        console.error("Transmission error tracking stock adjustments:", error);
        alert("Failed to sync inventory update log with store database server.");
    }
}

async function triggerPriceUpdateDialog(productId, currentPrice) {
    const newPriceStr = prompt(`Adjust retail selling rate (Current: ₹${currentPrice}):`);
    if (!newPriceStr) return;
    const newPrice = parseFloat(newPriceStr);
    if (isNaN(newPrice) || newPrice <= 0) return;

    try {
        const baseUrl = window.API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${baseUrl}/products/${productId}/update-price`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ selling_price: newPrice, cost_price: null })
        });

        if (response.ok) {
            fetchMasterInventory();
            alert("Rate successfully logged in system audit path!");
        } else {
            const err = await response.json();
            alert(`Adjustment Denied: ${err.detail}`);
        }
    } catch (error) {
        console.error(error);
    }
}

// ==========================================
// 5. HARDWARE BARCODE INTERCEPTION SUITE
// ==========================================
function initGlobalBarcodeScannerListener() {
    let barcodeBuffer = "";
    let lastKeyTime = Date.now();

    window.addEventListener("keydown", (e) => {
        const targetTag = e.target.tagName.toLowerCase();
        if (targetTag === "input" || targetTag === "select" || targetTag === "textarea") {
            return;
        }

        const currentTime = Date.now();
        if (currentTime - lastKeyTime > 50) {
            barcodeBuffer = "";
        }
        lastKeyTime = currentTime;

        if (e.key === "Enter") {
            if (barcodeBuffer.length >= 3) {
                processBarcodeRefillMatch(barcodeBuffer);
                barcodeBuffer = "";
            }
        } else if (e.key.length === 1) {
            barcodeBuffer += e.key;
        }
    });
}

function processBarcodeRefillMatch(scannedBarcode) {
    const matchedProduct = localInventoryRosterCache.find(p => p.barcode === scannedBarcode);

    if (matchedProduct) {
        triggerQuickRestockDialog(matchedProduct.id, matchedProduct.name);
    } else {
        alert(`Scanned Barcode: "${scannedBarcode}" is not cataloged inside Apna Bazar's records.`);
    }
}

// ==========================================
// 6. SEARCH SYSTEM INTEGRATION WIRE
// ==========================================
if (inventorySearch) {
    inventorySearch.addEventListener('input', async () => {
        const query = inventorySearch.value.trim();
        if (!query) {
            fetchMasterInventory(); 
            return;
        }

        try {
            const baseUrl = window.API_BASE_URL || 'http://127.0.0.1:8000';
            const response = await fetch(`${baseUrl}/search/products/?query=${encodeURIComponent(query)}`);
            const searchResults = await response.json();
            if (response.ok) renderInventoryTable(searchResults);
        } catch (error) {
            console.error(error);
        }
    });
}

async function fetchCategoriesForDropdown() {
    const baseUrl = window.API_BASE_URL || 'http://127.0.0.1:8000';
    const response = await fetch(`${baseUrl}/categories/`);
    const categories = await response.json();
    if (response.ok && categories.length > 0) {
        categoryDropdown.innerHTML = '<option value="">-- Choose Category --</option>';
        categories.forEach(cat => {
            categoryDropdown.insertAdjacentHTML('beforeend', `<option value="${cat.id}">${cat.name}</option>`);
        });
    }
}