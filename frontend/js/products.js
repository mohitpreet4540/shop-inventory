// ==========================================
// 1. INITIALIZATION & DOM REFERENCES
// ==========================================
const inventoryTableBody = document.getElementById('inventory-table-body');
const productForm = document.getElementById('product-form');
const inventorySearch = document.getElementById('inventory-search');
const categoryDropdown = document.getElementById('p-category'); // Reference to category dropdown

// Boot triggers: Load active inventory and category choices immediately on page launch
document.addEventListener('DOMContentLoaded', () => {
    fetchMasterInventory();
    fetchCategoriesForDropdown();
});

// ==========================================
// 2. FETCH & DISPLAY ALL INVENTORY ITEMS
// ==========================================
async function fetchMasterInventory() {
    try {
        const response = await fetch(`${API_BASE_URL}/products/`);
        const products = await response.json();

        if (response.ok) {
            renderInventoryTable(products);
        } else {
            console.error("Failed to extract master product ledger rows.");
        }
    } catch (error) {
        console.error("Inventory backend server offline error:", error);
    }
}

function renderInventoryTable(products) {
    inventoryTableBody.innerHTML = '';

    if (products.length === 0) {
        inventoryTableBody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-gray-400 font-medium">No inventory products found in database.</td></tr>`;
        return;
    }

    products.forEach(prod => {
        const costPrice = parseFloat(prod.cost_price).toFixed(2);
        const sellingPrice = parseFloat(prod.selling_price).toFixed(2);
        const currentQty = parseFloat(prod.current_quantity);
        
        // Low Stock Highlighter Flag Rule (alert if under 5 units remaining)
        const isLowStock = currentQty <= 5.00;

        const row = `
            <tr class="hover:bg-gray-50 transition border-b border-gray-100">
                <td class="p-4 text-center font-mono text-xs font-bold text-gray-400">${prod.id}</td>
                <td class="p-4">
                    <div class="font-bold text-gray-900">${prod.name}</div>
                    <div class="text-xs text-gray-500">Brand: <span class="font-semibold">${prod.brand}</span></div>
                </td>
                <td class="p-4 text-center font-mono text-xs text-gray-600 font-bold">${prod.barcode || '<span class="text-gray-300">Loose Metrics</span>'}</td>
                <td class="p-4 text-right">
                    <div class="text-xs text-gray-400">Cost: ₹${costPrice}</div>
                    <div class="font-bold text-green-600">Retail: ₹${sellingPrice}</div>
                </td>
                <td class="p-4 text-center">
                    <span class="px-2.5 py-1 rounded-full text-xs font-black ${isLowStock ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}">
                        ${currentQty} ${prod.unit_type}
                    </span>
                </td>
                <td class="p-4 text-center">
                    <button onclick="triggerQuickRestock(${prod.id}, '${prod.name}')" class="bg-blue-500 hover:bg-blue-600 text-white font-bold px-2.5 py-1 text-xs rounded shadow transition cursor-pointer">
                        <i class="fa-solid fa-boxes-stacked"></i> Restock
                    </button>
                </td>
            </tr>
        `;
        inventoryTableBody.insertAdjacentHTML('beforeend', row);
    });
}

// ==========================================
// 3. ONBOARD NEW PRODUCT MANAGEMENT POST
// ==========================================
productForm.addEventListener('submit', async (e) => {
    e.preventDefault(); 

    const categoryIdValue = categoryDropdown.value;
    if (!categoryIdValue) {
        alert("Please select a valid Category option from the dropdown selection list.");
        return;
    }

    const payload = {
        name: document.getElementById('p-name').value.trim(),
        brand: document.getElementById('p-brand').value.trim() || "Local",
        barcode: document.getElementById('p-barcode').value.trim() || null,
        unit_type: document.getElementById('p-unit').value,
        cost_price: parseFloat(document.getElementById('p-cost').value),
        selling_price: parseFloat(document.getElementById('p-selling').value),
        current_quantity: parseFloat(document.getElementById('p-qty').value),
        category_id: parseInt(categoryIdValue) // Reads database integer value safely from select options
    };

    try {
        const response = await fetch(`${API_BASE_URL}/products/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            alert("🎉 Product successfully onboarded and saved to inventory!");
            productForm.reset();
            fetchMasterInventory(); // Reload live list values
        } else {
            alert("Onboarding Denied: Verify item data configurations or completely unique barcode.");
        }
    } catch (error) {
        alert("Server communication failure during stock save profile execution.");
    }
});

// ==========================================
// 4. FIXED: RAPID-ACTION REFILL (CONNECTED TO YOUR /add-stock/)
// ==========================================
// ==========================================
// 4. FIXED: PATH MATCHED TO /products/add-stock/
// ==========================================
window.triggerQuickRestock = async function(productId, productName) {
    // 1. Ask for Quantity
    const refillQty = prompt(`Enter received wholesale delivery quantity for "${productName}":`);
    if (refillQty === null) return; 
    
    const parsedQty = parseFloat(refillQty);
    if (isNaN(parsedQty) || parsedQty <= 0) {
        alert("Invalid quantity!");
        return;
    }

    //  Ask for Optional Price Changes
    const newCost = prompt(`Enter NEW Cost Price (₹) if changed (otherwise leave blank):`);
    const newSelling = prompt(`Enter NEW Selling Price (₹) if changed (otherwise leave blank):`);

    const payload = {
        product_id: productId,
        quantity: parsedQty,
        notes: "Restock with potential price adjustment",
        // Only send numbers if user typed something
        cost_price: (newCost && newCost.trim() !== "") ? parseFloat(newCost) : null,
        selling_price: (newSelling && newSelling.trim() !== "") ? parseFloat(newSelling) : null
    };

    try {
        const response = await fetch(`${API_BASE_URL}/products/add-stock/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const data = await response.json();
            alert(`✅ ${data.message}`);
            fetchMasterInventory(); 
        } else {
            alert("Update failed. Check if rates are valid numbers.");
        }
    } catch (error) {
        alert("Network execution failure during restock.");
    }
};

// ==========================================
// 5. INVENTORY RECORD SEARCH LOGIC FILTER
// ==========================================
inventorySearch.addEventListener('input', async () => {
    const query = inventorySearch.value.trim();
    
    if (!query) {
        fetchMasterInventory(); 
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/search/products/?query=${encodeURIComponent(query)}`);
        const searchResults = await response.json();

        if (response.ok) {
            renderInventoryTable(searchResults);
        }
    } catch (error) {
        console.error("Live inventory filtering failure:", error);
    }
});

// ==========================================
// 6. USER-FRIENDLY CATEGORY SELECT DIALOG LOADER
// ==========================================
async function fetchCategoriesForDropdown() {
    if (!categoryDropdown) return;

    try {
        const response = await fetch(`${API_BASE_URL}/categories/`);
        const categories = await response.json();

        if (response.ok && categories.length > 0) {
            categoryDropdown.innerHTML = '<option value="">-- Select Category --</option>';
            
            categories.forEach(cat => {
                const option = `<option value="${cat.id}">${cat.name}</option>`;
                categoryDropdown.insertAdjacentHTML('beforeend', option);
            });
        }
    } catch (error) {
        console.error("Failed to sync category options down from database engine:", error);
    }
}