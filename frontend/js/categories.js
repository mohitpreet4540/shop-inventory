let globalCategoriesList = [];

const categoryForm = document.getElementById('category-form');
const categoryNameInput = document.getElementById('category-name');
const parentCategorySelect = document.getElementById('parent-category-select');
const tableBody = document.getElementById('categories-table-body');
const submitBtn = document.getElementById('submit-btn');

// Preview Nodes DOM Element Connections
const productPreviewBox = document.getElementById('product-preview-box');
const selectedCategoryTitle = document.getElementById('selected-category-title');
const productCountBadge = document.getElementById('product-count-badge');
const subcategoriesContainer = document.getElementById('subcategories-container');
const productsPreviewTableBody = document.getElementById('products-preview-table-body');

document.addEventListener('DOMContentLoaded', () => {
    fetchCategories();
    if (categoryForm) categoryForm.addEventListener('submit', handleCategorySubmission);
});

async function fetchCategories() {
    try {
        const response = await fetch(`${API_BASE_URL}/categories/`);
        if (response.ok) {
            globalCategoriesList = await response.json();
            populateParentDropdown(globalCategoriesList);
            renderCategoriesTable(globalCategoriesList);
        }
    } catch (error) {
        console.error("Failed to fetch system categories payload:", error);
    }
}

function renderCategoriesTable(categories) {
    if (!tableBody) return;
    tableBody.innerHTML = '';

    if (categories.length === 0) {
        tableBody.innerHTML = `<tr><td colspan=\"3\" class=\"p-4 text-center text-gray-400 text-xs\">No configuration classes recorded.</td></tr>`;
        return;
    }

    categories.forEach(cat => {
        // Find human readable parent node name if it links backwards
        const parentNode = categories.find(c => c.id === cat.parent_id);
        const parentName = parentNode ? parentNode.name : '<span class="text-gray-300 font-normal">Root Layer</span>';

        const row = document.createElement('tr');
        row.className = "border-b text-xs hover:bg-blue-50/50 cursor-pointer transition duration-150";
        row.innerHTML = `
            <td class="p-3 font-bold text-gray-500 font-mono text-center">${cat.id}</td>
            <td class="p-3 font-black text-gray-800">${cat.name}</td>
            <td class="p-3 font-semibold text-gray-600">${parentName}</td>
        `;
        
        // Add click integration callback
        row.addEventListener('click', () => handleCategoryDrilldownClick(cat.id, cat.name));
        tableBody.appendChild(row);
    });
}

// Interactive Drill-down Logic Processing Pipeline Engine
async function handleCategoryDrilldownClick(categoryId, categoryName) {
    if (!productPreviewBox || !selectedCategoryTitle || !subcategoriesContainer || !productsPreviewTableBody) return;

    // Unhide layout view system
    selectedCategoryTitle.innerText = categoryName;
    productPreviewBox.classList.remove('hidden');

    // 1. Process and populate subcategories tracking loops
    subcategoriesContainer.innerHTML = '';
    const childNodes = globalCategoriesList.filter(c => c.parent_id === categoryId);
    
    if (childNodes.length === 0) {
        subcategoriesContainer.innerHTML = `<span class="text-gray-400 italic font-medium text-[11px]">No child subcategories nested under this group.</span>`;
    } else {
        childNodes.forEach(child => {
            const spanTag = `<span class="px-2.5 py-1 bg-white border border-gray-200 rounded-md shadow-sm font-bold text-gray-700"><i class="fa-solid fa-folder text-yellow-500 mr-1"></i>${child.name}</span>`;
            subcategoriesContainer.insertAdjacentHTML('beforeend', spanTag);
        });
    }

    // 2. Fetch inventory records to filter bound catalog list data
    try {
        productsPreviewTableBody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-gray-400"><i class="fa-solid fa-spinner fa-spin mr-2 text-blue-500"></i>Synchronizing items stream...</td></tr>`;
        
        const response = await fetch(`${API_BASE_URL}/products/`);
        if (response.ok) {
            const allProducts = await response.json();
            
            // Collect target array boundaries: include parent and child subcategory items
            const structuralIdsTarget = [categoryId, ...childNodes.map(c => c.id)];
            const matchSetProducts = allProducts.filter(p => structuralIdsTarget.includes(p.category_id));

            productCountBadge.innerText = `${matchSetProducts.length} Items Found`;
            productsPreviewTableBody.innerHTML = '';

            if (matchSetProducts.length === 0) {
                productsPreviewTableBody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-gray-400 font-medium">No active products added to this category mapping group yet.</td></tr>`;
                return;
            }

            matchSetProducts.forEach(prod => {
                const tr = `
                    <tr class="hover:bg-gray-50/50 transition">
                        <td class="p-3 font-bold text-gray-800">${prod.name}</td>
                        <td class="p-3 text-gray-500">${prod.brand || 'Generic'}</td>
                        <td class="p-3 text-right font-mono font-bold text-blue-600">₹${parseFloat(prod.selling_price).toFixed(2)}</td>
                        <td class="p-3 text-center font-mono font-bold ${prod.current_quantity <= 10 ? 'text-red-600 bg-red-50' : 'text-gray-700'}">${prod.current_quantity} ${prod.unit_type || 'PCS'}</td>
                    </tr>
                `;
                productsPreviewTableBody.insertAdjacentHTML('beforeend', tr);
            });
        } else {
            productsPreviewTableBody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-red-500">Could not unpack storage schema stream.</td></tr>`;
        }
    } catch (err) {
        productsPreviewTableBody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-red-500">Data pipeline dropped unexpectedly.</td></tr>`;
    }
}

async function handleCategorySubmission(e) {
    e.preventDefault();
    const nameVal = categoryNameInput.value.trim();
    if (!nameVal) return;

    const payload = {
        name: nameVal,
        parent_id: parentCategorySelect.value ? parseInt(parentCategorySelect.value) : null
    };

    try {
        const response = await fetch(`${API_BASE_URL}/categories/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            categoryNameInput.value = '';
            parentCategorySelect.value = '';
            if (productPreviewBox) productPreviewBox.classList.add('hidden'); // Reset active drill-down view
            await fetchCategories();
        } else {
            const err = await response.json();
            alert(`Rejected: ${err.detail}`);
        }
    } catch (error) {
        alert("Transmission dropped.");
    }
}

function populateParentDropdown(categories) {
    if (!parentCategorySelect) return;
    parentCategorySelect.innerHTML = '<option value=\"\">-- No Parent (Root Category) --</option>';
    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        parentCategorySelect.appendChild(option);
    });
}