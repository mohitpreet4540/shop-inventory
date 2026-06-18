// ==========================================
// 1. STATE MANAGEMENT & DOM INITIALIZATION
// ==========================================
let cart = []; 

const barcodeInput = document.getElementById('barcode-input');
const searchInput = document.getElementById('search-input');
const searchDropdown = document.getElementById('search-results-dropdown'); 
const cartTableBody = document.getElementById('cart-table-body');
const emptyCartView = document.getElementById('empty-cart-view');
const grandTotalDisplay = document.getElementById('summary-grand-total');
const totalItemsDisplay = document.getElementById('summary-total-items');
const checkoutBtn = document.getElementById('checkout-btn');

// Extended split-ledger inputs
const checkoutAmountPaid = document.getElementById('checkout-amount-paid');
const checkoutAmountPending = document.getElementById('checkout-amount-pending');
const customerDetailsInput = document.getElementById('customer-details-input');
const paymentMethodSelect = document.getElementById('payment-method-select');

document.addEventListener('DOMContentLoaded', () => {
    if (barcodeInput) barcodeInput.focus();
    if (checkoutAmountPaid) {
        checkoutAmountPaid.addEventListener('input', runSplitPaymentCalculations);
    }
});

// ==========================================
// 2. HARDWARE INTEGRATION (BARCODE SCANNER)
// ==========================================
if (barcodeInput) {
    barcodeInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            const barcode = barcodeInput.value.trim();
            if (barcode) {
                fetchProductDirectly(barcode);
                barcodeInput.value = ''; 
            }
        }
    });
}

async function fetchProductDirectly(barcodeValue) {
    try {
        const response = await fetch(`${API_BASE_URL}/search/products/?query=${encodeURIComponent(barcodeValue)}`);
        if (!response.ok) return;
        const matchingProducts = await response.json();
        
        if (matchingProducts.length > 0) {
            addItemToCart(matchingProducts[0]);
        } else {
            alert(`No items mapped to barcode string: ${barcodeValue}`);
        }
    } catch (error) {
        console.error("Scanner stream communication interruption:", error);
    }
}

// ==========================================
// 3. LIVE SEARCH FILTER LAYER
// ==========================================
if (searchInput) {
    searchInput.addEventListener('input', async () => {
        const query = searchInput.value.trim();
        if (!query) {
            hideSearchDropdown();
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/search/products/?query=${encodeURIComponent(query)}`);
            const products = await response.json();

            if (response.ok && products.length > 0) {
                renderSearchDropdown(products);
            } else {
                hideSearchDropdown();
            }
        } catch (error) {
            console.error("Dropdown filter failure:", error);
        }
    });
}

function renderSearchDropdown(products) {
    searchDropdown.innerHTML = '';
    searchDropdown.classList.remove('hidden');

    products.forEach(product => {
        const qty = parseFloat(product.current_quantity || 0);
        const itemElement = document.createElement('div');
        itemElement.className = "p-2 hover:bg-gray-100 cursor-pointer text-xs border-b flex justify-between items-center";
        itemElement.innerHTML = `
            <div>
                <span class="font-bold text-gray-800">${product.name}</span>
                <span class="text-gray-400 text-[10px] ml-1">[${product.brand || 'Generic'}]</span>
            </div>
            <div class="text-right">
                <span class="text-blue font-bold mr-2">₹${parseFloat(product.selling_price).toFixed(2)}</span>
                <span class="${qty <= 0 ? 'text-red-500 font-bold' : 'text-gray-500'}">Qty: ${qty.toFixed(0)}</span>
            </div>
        `;
        itemElement.addEventListener('click', () => {
            addItemToCart(product);
            searchInput.value = '';
            hideSearchDropdown();
        });
        searchDropdown.appendChild(itemElement);
    });
}

function hideSearchDropdown() {
    searchDropdown.innerHTML = '';
    searchDropdown.classList.add('hidden');
}

// ==========================================
// 4. CART INTERACTION CORE
// ==========================================
function addItemToCart(product) {
    const existingItem = cart.find(item => item.id === product.id);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id: product.id,
            name: product.name,
            brand: product.brand,
            barcode: product.barcode,
            unit_type: product.unit_type || 'PCS',
            selling_price: parseFloat(product.selling_price),
            quantity: 1
        });
    }
    renderCart();
}

function updateQuantity(productId, newQty) {
    const qty = parseFloat(newQty);
    const itemIndex = cart.findIndex(item => item.id === productId);
    
    if (itemIndex === -1) return;

    if (qty <= 0 || isNaN(qty)) {
        cart.splice(itemIndex, 1);
    } else {
        cart[itemIndex].quantity = qty;
    }
    renderCart();
}

function renderCart() {
    cartTableBody.innerHTML = '';
    
    if (cart.length === 0) {
        emptyCartView.classList.remove('hidden');
        grandTotalDisplay.innerText = "₹0.00";
        totalItemsDisplay.innerText = "0";
        if (checkoutAmountPaid) checkoutAmountPaid.value = "0";
        if (checkoutAmountPending) checkoutAmountPending.innerText = "₹0.00";
        return;
    }

    emptyCartView.classList.add('hidden');
    let runningGrandTotal = 0;
    let runningTotalItems = 0;

    cart.forEach(item => {
        const rowTotal = item.selling_price * item.quantity;
        runningGrandTotal += rowTotal;
        runningTotalItems += item.quantity;

        const row = document.createElement('tr');
        row.className = "border-b text-xs hover:bg-gray-50";
        row.innerHTML = `
            <td class="p-3">
                <span class="font-bold text-gray-800">${item.name}</span>
                <p class="text-[10px] text-gray-400 font-medium">${item.brand || 'Generic'}</p>
            </td>
            <td class="p-3 font-mono">₹${item.selling_price.toFixed(2)}</td>
            <td class="p-3">
                <div class="flex items-center gap-1">
                    <input type="number" class="w-16 border rounded p-1 text-center font-bold" value="${item.quantity}" min="0.1" step="any" onchange="updateQuantity(${item.id}, this.value)">
                    <span class="text-[10px] text-gray-400 font-medium">${item.unit_type}</span>
                </div>
            </td>
            <td class="p-3 font-mono font-bold text-gray-800">₹${rowTotal.toFixed(2)}</td>
            <td class="p-3 text-center">
                <button class="text-red-500 hover:text-red-700 transition" onclick="updateQuantity(${item.id}, 0)">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        `;
        cartTableBody.appendChild(row);
    });

    grandTotalDisplay.innerText = `₹${runningGrandTotal.toFixed(2)}`;
    totalItemsDisplay.innerText = runningTotalItems.toFixed(0);
    
    runSplitPaymentCalculations();
}

function runSplitPaymentCalculations() {
    const totalAmount = parseFloat(grandTotalDisplay.innerText.replace('₹', '')) || 0;
    let amountPaid = parseFloat(checkoutAmountPaid.value);
    
    if (isNaN(amountPaid) || amountPaid < 0) amountPaid = 0;
    if (amountPaid > totalAmount) {
        amountPaid = totalAmount;
        checkoutAmountPaid.value = totalAmount.toFixed(2);
    }

    const residualDebt = totalAmount - amountPaid;
    if (checkoutAmountPending) {
        checkoutAmountPending.innerText = `₹${residualDebt.toFixed(2)}`;
    }
}

// ==========================================
// 5. ASYNC ORDER SUBMISSION DISPATCH PIPELINE
// ==========================================
if (checkoutBtn) {
    checkoutBtn.addEventListener('click', async () => {
        if (cart.length === 0) {
            alert("POS cart register is currently empty.");
            return;
        }

        const totalAmount = parseFloat(grandTotalDisplay.innerText.replace('₹', ''));
        const amountPaid = parseFloat(checkoutAmountPaid.value) || 0;
        const amountPending = parseFloat(checkoutAmountPending.innerText.replace('₹', ''));
        const customerInfo = customerDetailsInput.value.trim() || "Anonymous Retail Walk-in";
        const paymentMethod = paymentMethodSelect.value;

        // Security Risk Boundaries protection check
        if (amountPending > 0 && customerInfo === "Anonymous Retail Walk-in") {
            alert("🔒 High Risk: Khata ledger allocations cannot be authorized anonymously. Please provide a verified customer name/account.");
            return;
        }

        checkoutBtn.disabled = true;

        const comprehensiveOrderPayload = {
            total_amount: totalAmount,
            amount_paid: amountPaid,
            amount_pending: amountPending,
            payment_method: paymentMethod,
            customer_info: customerInfo,
            items: cart.map(item => ({
                product_id: item.id,
                barcode: item.barcode || null,
                quantity: item.quantity
            }))
        };

        try {
            const response = await fetch(`${API_BASE_URL}/orders/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(comprehensiveOrderPayload)
            });

            const data = await response.json();

            if (response.ok) {
                alert(`🎉 Order Finalized! Invoice ID: #${data.id}`);
                cart = []; 
                customerDetailsInput.value = '';
                checkoutAmountPaid.value = '0';
                renderCart();
                if (barcodeInput) barcodeInput.focus(); 
            } else {
                alert("Checkout Rejected: " + (data.detail || "Validation fail"));
            }
        } catch (error) {
            console.error("Order payload submission drop:", error);
            alert("Network connection dropped.");
        } finally {
            checkoutBtn.disabled = false;
        }
    });
}