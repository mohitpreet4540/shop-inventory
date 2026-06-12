// ==========================================
// EXPANDED CATEGORIES & NESTED PRODUCTS DOM ENGINE
// ==========================================
let globalCategoriesList = [];
let activeSelectedCategoryId = null;

// DOM Element Registry
const categoryForm = document.getElementById('category-form');
const categoryNameInput = document.getElementById('category-name');
const parentCategorySelect = document.getElementById('parent-category-select');
const tableBody = document.getElementById('categories-table-body');
const submitBtn = document.getElementById('submit-btn');

// New Preview DOM elements
const productPreviewBox = document.getElementById('product-preview-box');
const selectedCategoryTitle = document.getElementById('selected-category-title');
const productCountBadge = document.getElementById('product-count-badge');
const productsPreviewTableBody = document.getElementById('products-preview-table-body');

document.addEventListener('DOMContentLoaded', () => {
    fetchCategories();
    if (categoryForm) {
        categoryForm.addEventListener('submit', handleCategorySubmission);
    }
});

// ==========================================
// GET CATEGORIES DATA MATRIX
// ==========================================
async function fetchCategories() {
    renderLoadingState();
    try {
        const response = await fetch(`${API_BASE_URL}/categories/`);
        if (response.ok) {
            globalCategoriesList = await response.json();
            populateParentDropdown(globalCategoriesList);
            renderTableData(globalCategoriesList);
            
            // Auto-refresh the expanded product list view if a row was selected
            if (activeSelectedCategoryId) {
                const activeCat = globalCategoriesList.find(c => c.id === activeSelectedCategoryId);
                if (activeCat) loadProductsByCategory(activeSelectedCategoryId, activeCat.name);
            }
        }
    } catch (error) {
        console.error("Connection failure:", error);
        tableBody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-red-500">Unreachable backend engine.</td></tr>`;
    }
}

// ==========================================
// RENDERING CATEGORIES LIST WITH CLICK TRIGGERS
// ==========================================
function renderTableData(categories) {
    tableBody.innerHTML = '';

    if (categories.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="4" class="p-6 text-center text-gray-400">No category classifications located.</td></tr>`;
        return;
    }

    categories.forEach(category => {
        let parentName = "Root Category";
        if (category.parent_id) {
            const parentMatch = categories.find(c => c.id === category.parent_id);
            if (parentMatch) parentName = parentMatch.name;
        }

        // Highlight selected category row visually
        const isCurrentSelection = category.id === activeSelectedCategoryId;

        const rowHtml = `
            <tr class="cursor-pointer transition ${isCurrentSelection ? 'bg-blue-100 font-semibold' : 'hover:bg-blue-50/50'}"
                onclick="loadProductsByCategory(${category.id}, '${category.name.replace(/'/g, "\\'")}')">
                <td class="p-4 font-mono text-xs text-gray-400">#${category.id}</td>
                <td class="p-4 text-gray-800 flex items-center justify-between">
                    <span>${category.name}</span>
                    <i class="fa-solid fa-chevron-right text-gray-300 text-xs"></i>
                </td>
                <td class="p-4">
                    <span class="text-xs px-2 py-1 rounded font-medium ${category.parent_id ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-gray-100 text-gray-600'}">
                        ${parentName}
                    </span>
                </td>
                <td class="p-4 text-center">
                    <button class="text-xs font-bold text-blue-600 bg-white border border-blue-200 px-2 py-1 rounded shadow-sm hover:bg-blue-50">
                        <i class="fa-solid fa-eye mr-1"></i> Explore Stock
                    </button>
                </td>
            </tr>
        `;
        tableBody.insertAdjacentHTML('beforeend', rowHtml);
    });
}

// ==========================================
// 🌟 NEW ENGINE: LOADING & FILTERING PRODUCTS 
// ==========================================
async function loadProductsByCategory(categoryId, categoryName) {
    activeSelectedCategoryId = categoryId;
    
    // Highlight selected item in the upper category table instantly
    renderTableData(globalCategoriesList);

    selectedCategoryTitle.textContent = categoryName;
    productPreviewBox.classList.remove('hidden');
    productsPreviewTableBody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-gray-400"><i class="fa-solid fa-spinner fa-spin text-blue-500 mr-2"></i>Scanning active index mappings...</td></tr>`;

    try {
        // Fetch products from your backend routing parameters
        const response = await fetch(`${API_BASE_URL}/products/`);
        if (!response.ok) throw new Error("Product database network drop.");

        const allProducts = await response.json();
        
        // Filter out products belonging exactly to this category context
        const nestedProducts = allProducts.filter(p => p.category_id === categoryId);
        
        productCountBadge.textContent = `${nestedProducts.length} Item(s)`;
        productsPreviewTableBody.innerHTML = '';

        if (nestedProducts.length === 0) {
            productsPreviewTableBody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-gray-400 italic">No inventory line products mapped inside this category yet.</td></tr>`;
            return;
        }

        nestedProducts.forEach(product => {
            const currentQty = parseFloat(product.current_quantity) || 0;
            const isLowStock = currentQty <= 5.00;

            const rowHtml = `
                <tr class="hover:bg-gray-50/80 transition">
                    <td class="p-4">
                        <div class="font-bold text-gray-800 text-sm">${product.name}</div>
                        <div class="text-xs text-gray-400 font-mono">${product.brand || 'Local'} | ${product.barcode || 'Loose Weight'}</div>
                    </td>
                    <td class="p-4 text-right font-mono text-sm text-gray-600">₹${parseFloat(product.cost_price).toFixed(2)}</td>
                    <td class="p-4 text-right font-mono text-sm font-bold text-blue-600">₹${parseFloat(product.selling_price).toFixed(2)}</td>
                    <td class="p-4 text-center">
                        <span class="inline-block px-2 py-0.5 rounded text-xs font-bold ${isLowStock ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}">
                            ${currentQty.toFixed(2)} ${product.unit_type || 'PIECE'}
                        </span>
                    </td>
                    <td class="p-4 text-center space-x-2">
                        <button onclick="inlineModifyPrice(${product.id}, '${product.name.replace(/'/g, "\\'")}', ${product.selling_price})" 
                                class="text-blue-600 hover:text-blue-800 bg-blue-50 border border-blue-200 px-2.5 py-1 rounded text-xs font-bold shadow-xs cursor-pointer">
                            <i class="fa-solid fa-pen mr-1"></i> Edit Price
                        </button>
                    </td>
                </tr>
            `;
            productsPreviewTableBody.insertAdjacentHTML('beforeend', rowHtml);
        });

    } catch (error) {
        productsPreviewTableBody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-red-500 font-bold">Failed to load product sub-matrix lines.</td></tr>`;
    }
}

// ==========================================
// 🌟 NEW ENGINE: INLINE EDITING MANAGEMENT
// ==========================================
window.inlineModifyPrice = async function(productId, productName, currentPrice) {
    const targetPrice = prompt(`✏️ MODIFY SELLING RATE\nEnter new retail selling price for "${productName}":\nCurrent value: ₹${parseFloat(currentPrice).toFixed(2)}`);
    
    if (targetPrice === null) return; // User opted out of selection prompt
    
    const parsedPrice = parseFloat(targetPrice);
    if (isNaN(parsedPrice) || parsedPrice <= 0) {
        alert("Validation Drop: Entered price parameters must be an actual positive cash figure.");
        return;
    }

    try {
        // Send updates back to your FastAPI backend routing matrix parameters
        const response = await fetch(`${API_BASE_URL}/products/${productId}/update-price`, {
            method: 'PUT', // or POST/PATCH depending on how your products router handles edits
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ selling_price: parsedPrice })
        });

        if (response.ok) {
            alert(`🎉 Changes Saved!\n"${productName}" rate successfully updated to ₹${parsedPrice.toFixed(2)}`);
            // Trigger dynamic matrix reload loops to push changes onto the display live
            const activeCat = globalCategoriesList.find(c => c.id === activeSelectedCategoryId);
            if (activeCat) loadProductsByCategory(activeSelectedCategoryId, activeCat.name);
        } else {
            alert("Backend rejected operation payload validation properties.");
        }
    } catch (error) {
        alert("Infrastructure loop missing during active transmission operations.");
    }
};

// ==========================================
// CATEGORIES INGESTION HANDLER MATRICES (POST)
// ==========================================
async function handleCategorySubmission(event) {
    event.preventDefault();
    const nameValue = categoryNameInput.value.trim();
    const parentSelection = parentCategorySelect.value;
    
    const categoryPayload = {
        name: nameValue,
        parent_id: parentSelection === "" ? null : parseInt(parentSelection)
    };

    try {
        setLoadingUISignals(true);
        const response = await fetch(`${API_BASE_URL}/categories/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(categoryPayload)
        });

        if (response.ok) {
            categoryNameInput.value = '';
            parentCategorySelect.value = '';
            await fetchCategories();
        } else {
            const errObj = await response.json();
            alert("Backend rejection: " + (errObj.detail || "Validation Error."));
        }
    } catch (error) {
        alert("Transmission dropped.");
    } finally {
        setLoadingUISignals(false);
    }
}

function populateParentDropdown(categories) {
    parentCategorySelect.innerHTML = '<option value="">-- No Parent (Root Category) --</option>';
    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        parentCategorySelect.appendChild(option);
    });
}

function renderLoadingState() {
    tableBody.innerHTML = `<tr><td colspan="4" class="p-8 text-center text-gray-400"><i class="fa-solid fa-spinner fa-spin mr-2 text-blue-500"></i>Syncing data tables...</td></tr>`;
}

function setLoadingUISignals(isLoading) {
    if (isLoading) {
        submitBtn.disabled = true;
        submitBtn.innerText = "Writing Config Data...";
    } else {
        submitBtn.disabled = false;
        submitBtn.innerText = "Save Category Configuration";
    }
}