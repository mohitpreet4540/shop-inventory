// ==========================================
// INITIALIZATION & STATE MANAGEMENT
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    // Run core execution layout routines on startup
    syncCategoryRegistryLayers();

    // Attach listener to manual refresh sync trigger button
    const refreshTrigger = document.getElementById('refresh-tree-trigger');
    if (refreshTrigger) {
        refreshTrigger.addEventListener('click', syncCategoryRegistryLayers);
    }

    // Intercept and process creation forms
    const creationForm = document.getElementById('category-creation-form');
    if (creationForm) {
        creationForm.addEventListener('submit', commitCategoryFormSubmission);
    }
});

// ==========================================
// DYNAMIC HIERARCHY MATRIX SYNC ENGINE
// ==========================================
async function syncCategoryRegistryLayers() {
    const treeRoot = document.getElementById('category-hierarchy-tree-root');
    const loaderSpinner = document.getElementById('tree-loader-spinner');
    const emptyNotice = document.getElementById('tree-empty-notice');
    const totalCounter = document.getElementById('total-category-counter');

    if (!treeRoot) return;

    loaderSpinner.classList.remove('hidden');
    treeRoot.innerHTML = '';
    emptyNotice.classList.add('hidden');
    
    try {
        // Absolute fallback URL matching dashboard configuration
        const baseUrl = window.API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${baseUrl}/categories`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Data synchronization failure down network pipeline');
        }
        
        const rootCategories = await response.json();
        
        if (totalCounter) {
            let totalCount = rootCategories.length;
            rootCategories.forEach(cat => {
                if (cat.subcategories) totalCount += cat.subcategories.length;
            });
            totalCounter.innerText = totalCount;
        }

        if (rootCategories.length === 0) {
            loaderSpinner.classList.add('hidden');
            emptyNotice.classList.remove('hidden');
            populateParentSelectionDropdown([]);
            return;
        }

        populateParentSelectionDropdown(rootCategories);
        loaderSpinner.classList.add('hidden');
        
        rootCategories.forEach(rootCategory => {
            const rootCard = document.createElement('div');
            rootCard.className = "bg-gray-50 border border-gray-200 rounded-xl overflow-hidden shadow-sm mb-3";
            
            let subcategoryRowsHTML = '';
            const validSubcategories = rootCategory.subcategories || [];

            if (validSubcategories.length > 0) {
                validSubcategories.forEach(sub => {
                    subcategoryRowsHTML += `
                        <div class="flex items-center justify-between py-2.5 px-4 bg-white border-t border-gray-100 text-sm pl-8">
                            <div class="flex items-center space-x-2 text-gray-700">
                                <i class="fa-solid fa-turn-up rotate-90 text-gray-300 text-xs mb-1"></i>
                                <span class="font-medium">${sub.name}</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <span class="text-xs bg-indigo-50 text-indigo-600 font-semibold px-2 py-0.5 rounded-full border border-indigo-100">Subgroup</span>
                                <button class="text-xs text-emerald-500 p-1 transition" onclick="triggerInactivationAlert('${sub.name}')" title="Active">
                                    <i class="fa-solid fa-toggle-on text-sm"></i>
                                </button>
                            </div>
                        </div>
                    `;
                });
            } else {
                subcategoryRowsHTML = `
                    <div class="py-3 px-4 bg-white border-t border-gray-100 text-xs text-gray-400 italic pl-8">
                        No secondary sub-group classifications assigned under this department root.
                    </div>
                `;
            }

            rootCard.innerHTML = `
                <div class="flex items-center justify-between py-3.5 px-4 bg-gray-100 text-sm font-bold text-gray-800">
                    <div class="flex items-center space-x-2">
                        <i class="fa-solid fa-folder text-amber-500"></i>
                        <span>${rootCategory.name}</span>
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full font-semibold">Primary Root</span>
                        <button class="text-xs text-emerald-500 p-1 transition" onclick="triggerInactivationAlert('${rootCategory.name}')" title="Active">
                            <i class="fa-solid fa-toggle-on text-sm"></i>
                        </button>
                    </div>
                </div>
                <div class="bg-white">
                    ${subcategoryRowsHTML}
                </div>
            `;
            
            treeRoot.appendChild(rootCard);
        });

    } catch (err) {
        loaderSpinner.classList.add('hidden');
        console.error("Categories engine pipeline crash:", err);
        triggerSystemToast(err.message, 'error');
    }
}

// ==========================================
// INPUT ENTRY COMMIT OPERATION ROUTINES
// ==========================================
async function commitCategoryFormSubmission(e) {
    e.preventDefault();
    
    const nameInput = document.getElementById('category-name-input');
    const parentSelect = document.getElementById('parent-category-select');
    
    if (!nameInput) return;
    
    const rawName = nameInput.value.trim();
    const chosenParent = parentSelect ? parentSelect.value : "";

    if (!rawName) return;

    const payload = {
        name: rawName,
        parent_id: chosenParent ? parseInt(chosenParent, 10) : null
    };

    try {
        const baseUrl = window.API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${baseUrl}/categories/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to create new category record entry');
        }

        triggerSystemToast(`Category entry successfully committed and registered!`);
        nameInput.value = '';
        if (parentSelect) parentSelect.value = '';
        
        await syncCategoryRegistryLayers();

    } catch (error) {
        console.error("Category configuration storage fault:", error);
        triggerSystemToast(error.message, 'error');
    }
}

// ==========================================
// HELPER UI COMPONENT UTILITIES
// ==========================================
function populateParentSelectionDropdown(rootNodes) {
    const parentSelect = document.getElementById('parent-category-select');
    if (!parentSelect) return;

    parentSelect.innerHTML = '<option value="">None — Treat as Primary Department Root</option>';
    
    rootNodes.forEach(node => {
        const option = document.createElement('option');
        option.value = node.id;
        option.innerText = node.name;
        parentSelect.appendChild(option);
    });
}

function triggerSystemToast(message, type = 'success') {
    const toast = document.getElementById('toast-notification');
    const iconBox = document.getElementById('toast-icon-box');
    const icon = document.getElementById('toast-icon');
    const msgBox = document.getElementById('toast-message');

    if (!toast || !msgBox) return;

    msgBox.innerText = message;
    
    if (type === 'error') {
        if (iconBox) iconBox.className = "inline-flex items-center justify-center flex-shrink-0 w-8 h-8 text-red-500 bg-red-100 rounded-lg";
        if (icon) icon.className = "fa-solid fa-triangle-exclamation";
    } else {
        if (iconBox) iconBox.className = "inline-flex items-center justify-center flex-shrink-0 w-8 h-8 text-emerald-500 bg-emerald-100 rounded-lg";
        if (icon) icon.className = "fa-solid fa-circle-check";
    }

    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 4000);
}

function triggerInactivationAlert(categoryName) {
    alert(
        `🛡️ ERP Safety Notice:\n\n` +
        `The classification entry "${categoryName}" cannot be hard-deleted because historical sales transactions, ` +
        `invoice ledger line records, or active stock items rely on its relational mapping references.\n\n` +
        `To alter this configuration, please use the Bulk Move panel on the Inventory screen to reassign any linked products first.`
    );
}