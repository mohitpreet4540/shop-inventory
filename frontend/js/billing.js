// ==========================================
// 1. STATE MANAGEMENT & DOM INITIALIZATION
// ==========================================
let cart = []; // The temporary "memory" bank for the current bill

const barcodeInput = document.getElementById('barcode-input');
const searchInput = document.getElementById('search-input');
const searchDropdown = document.getElementById('search-results-dropdown'); // 🌟 The floating box
const cartTableBody = document.getElementById('cart-table-body');
const emptyCartView = document.getElementById('empty-cart-view');
const grandTotalDisplay = document.getElementById('summary-grand-total');
const totalItemsDisplay = document.getElementById('summary-total-items');
const checkoutBtn = document.getElementById('checkout-btn');

// Payment Mode UI Cards
const payCashLabel = document.getElementById('pay-cash-label');
const payOnlineLabel = document.getElementById('pay-online-label');
const radioCash = document.getElementById('radio-cash');
const radioOnline = document.getElementById('radio-online');

// ==========================================
// 2. HARDWARE INTEGRATION (BARCODE SCANNER)
// ==========================================
barcodeInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        const barcode = barcodeInput.value.trim();
        if (barcode) {
            fetchProductDirectly(barcode);
            barcodeInput.value = ''; // Instantly clear for next barcode scan
        }
    }
});

// Directly adds scanned item to cart without showing a dropdown
async function fetchProductDirectly(barcodeValue) {
    try {
        const response = await fetch(`${API_BASE_URL}/search/products/?query=${encodeURIComponent(barcodeValue)}`);
        const data = await response.json();

        if (response.ok && data.length > 0) {
            addToCart(data[0]); 
        } else {
            alert(`Scanned item not found: "${barcodeValue}"`);
        }
    } catch (error) {
        console.error("Scanner communication failure:", error);
    }
}

// ==========================================
// 3. MODERN INTERACTIVE AUTOCOMPLETE SEARCH
// ==========================================
// This fires instantly on EVERY single key you type!
searchInput.addEventListener('input', async function () {
    const textQuery = searchInput.value.trim();
    
    // If the search bar is wiped empty, hide the dropdown instantly
    if (!textQuery) {
        hideDropdown();
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/search/products/?query=${encodeURIComponent(textQuery)}`);
        const products = await response.json();

        if (response.ok && products.length > 0) {
            searchDropdown.classList.remove('hidden');
            searchDropdown.innerHTML = ''; // Clear older matches

            // Loop and build visual cards inside the floating dropdown
            products.forEach(product => {
                const itemRow = `
                    <div class="p-3 border-b border-gray-100 hover:bg-blue-50 cursor-pointer flex justify-between items-center transition"
                         onclick="selectDropdownItem(${JSON.stringify(product).replace(/"/g, '&quot;')})">
                        <div>
                            <span class="font-bold text-gray-800">${product.name}</span>
                            <span class="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded ml-2">${product.brand}</span>
                        </div>
                        <div class="text-right">
                            <div class="text-sm font-bold text-blue-600">₹${parseFloat(product.selling_price).toFixed(2)}</div>
                            <div class="text-xs ${product.current_quantity <= 5 ? 'text-red-500 font-bold' : 'text-gray-400'}">
                                Stock: ${product.current_quantity} ${product.unit_type}
                            </div>
                        </div>
                    </div>
                `;
                searchDropdown.insertAdjacentHTML('beforeend', itemRow);
            });
        } else {
            // Show a friendly "No results" banner inside the dropdown
            searchDropdown.classList.remove('hidden');
            searchDropdown.innerHTML = `<div class="p-4 text-sm text-gray-400 text-center font-medium">No products match "${textQuery}"</div>`;
        }
    } catch (error) {
        console.error("Autocomplete backend failure:", error);
    }
});

// Executes when the shopkeeper clicks an item inside the dropdown list
window.selectDropdownItem = function(product) {
    addToCart(product);       
    searchInput.value = '';   
    hideDropdown();
};

function hideDropdown() {
    searchDropdown.classList.add('hidden');
    searchDropdown.innerHTML = '';
    barcodeInput.focus(); // Keep focus on the primary barcode element
}

// Automatically dismiss the dropdown if you click outside the boxes
document.addEventListener('click', function (e) {
    if (e.target !== searchInput && e.target !== searchDropdown) {
        searchDropdown.classList.add('hidden');
    }
});


// ==========================================
// 4. ACTIVE BILL CART MANAGEMENT MATRIX
// ==========================================
function addToCart(product) {
    const existingItem = cart.find(item => item.id === product.id);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id: product.id,
            name: product.name,
            brand: product.brand,
            unit_type: product.unit_type,
            selling_price: parseFloat(product.selling_price),
            quantity: 1,
            barcode: product.barcode
        });
    }
    renderCart();
}

window.updateQuantity = function(id, newQty) {
    const item = cart.find(i => i.id === id);
    if (item) {
        item.quantity = parseFloat(newQty) || 0;
        if (item.quantity <= 0) {
            removeFromCart(id);
        } else {
            renderCart();
        }
    }
};

window.removeFromCart = function(id) {
    cart = cart.filter(item => item.id !== id);
    renderCart();
};

document.getElementById('clear-cart-btn').addEventListener('click', () => {
    cart = [];
    renderCart();
});

// ==========================================
// 5. RENDERING THE DYNAMIC LAYOUT TABLE
// ==========================================
function renderCart() {
    cartTableBody.innerHTML = '';
    let grandTotal = 0;
    let totalItems = 0;

    if (cart.length === 0) {
        emptyCartView.classList.remove('hidden');
        checkoutBtn.disabled = true;
    } else {
        emptyCartView.classList.add('hidden');
        checkoutBtn.disabled = false;

        cart.forEach(item => {
            const subtotal = item.quantity * item.selling_price;
            grandTotal += subtotal;
            totalItems += 1;

            const row = `
                <tr class="hover:bg-gray-50 transition">
                    <td class="p-4">
                        <div class="font-bold text-gray-800">${item.name}</div>
                        <div class="text-xs text-gray-500">${item.brand} | ${item.barcode || 'Metric Loose Item'}</div>
                    </td>
                    <td class="p-4 text-center"><span class="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-bold">${item.unit_type}</span></td>
                    <td class="p-4 text-right">₹${item.selling_price.toFixed(2)}</td>
                    <td class="p-4">
                        <input type="number" step="0.01" value="${item.quantity}" 
                            class="w-24 border rounded px-2 py-1 text-center font-bold bg-gray-50"
                            onchange="updateQuantity(${item.id}, this.value)">
                    </td>
                    <td class="p-4 text-right font-bold text-blue-600">₹${subtotal.toFixed(2)}</td>
                    <td class="p-4 text-center">
                        <button onclick="removeFromCart(${item.id})" class="text-red-400 hover:text-red-600 cursor-pointer">
                            <i class="fa-solid fa-circle-xmark text-lg"></i>
                        </button>
                    </td>
                </tr>
            `;
            cartTableBody.insertAdjacentHTML('beforeend', row);
        });
    }

    grandTotalDisplay.innerText = grandTotal.toFixed(2);
    totalItemsDisplay.innerText = totalItems;
}

// ==========================================
// 6. PAYMENT MODE UI SWITCH CONTROLLERS
// ==========================================
payCashLabel.addEventListener('click', () => {
    radioCash.checked = true;
    payCashLabel.className = "border-2 border-blue-500 bg-blue-50 rounded-lg p-3 flex flex-col items-center justify-center cursor-pointer shadow-sm transition";
    payCashLabel.querySelector('i').className = "fa-solid fa-money-bill-wave text-xl text-blue-600 mb-1";
    payCashLabel.querySelector('span').className = "text-sm font-bold text-blue-700";
    
    payOnlineLabel.className = "border border-gray-200 rounded-lg p-3 flex flex-col items-center justify-center cursor-pointer transition hover:bg-gray-50";
    payOnlineLabel.querySelector('i').className = "fa-solid fa-qrcode text-xl text-gray-500 mb-1";
    payOnlineLabel.querySelector('span').className = "text-sm font-bold text-gray-600";
});

payOnlineLabel.addEventListener('click', () => {
    radioOnline.checked = true;
    payOnlineLabel.className = "border-2 border-blue-500 bg-blue-50 rounded-lg p-3 flex flex-col items-center justify-center cursor-pointer shadow-sm transition";
    payOnlineLabel.querySelector('i').className = "fa-solid fa-qrcode text-xl text-blue-600 mb-1";
    payOnlineLabel.querySelector('span').className = "text-sm font-bold text-blue-700";
    
    payCashLabel.className = "border border-gray-200 rounded-lg p-3 flex flex-col items-center justify-center cursor-pointer transition hover:bg-gray-50";
    payCashLabel.querySelector('i').className = "fa-solid fa-money-bill-wave text-xl text-gray-500 mb-1";
    payCashLabel.querySelector('span').className = "text-sm font-bold text-gray-600";
});

// ==========================================
// 7. FIXED: DUAL-TRACK LEDGER CHECKOUT TRANSACTION
// ==========================================
checkoutBtn.addEventListener('click', async () => {
    if (cart.length === 0) return alert("Cart validation error.");

    const totalBillAmount = parseFloat(grandTotalDisplay.innerText);
    const primarySelectedMode = document.querySelector('input[name="payment_method"]:checked').value;
    
    let allocatedPaid = totalBillAmount;
    let allocatedPending = 0.00;
    let customerIdentityRecord = "Walk-in Customer";
    let activePaymentType = primarySelectedMode;

    // 🌟 ENHANCED CASH SECURITY CHECK
    if (primarySelectedMode === 'CASH') {
        const securityVerification = confirm(`💰 PHYSICAL CASH TRANSACTION CHECK\n\nTotal Bill Amount: ₹${totalBillAmount.toFixed(2)}\n\nHave you counted and physically received this cash inside the drawer till?`);
        if (!securityVerification) return; 
    }

    // 🌟 CHOOSE INVOICE STATE PATHWAY: ASK FOR BOOK ENTRIES
    const requestLedgerSplit = confirm("Is this an outstanding Credit line account profile order ('Udhaar' / Partial payment deal)?\n\n[OK = Yes, Cancel = Regular Full Payment]");

    if (requestLedgerSplit) {
        const nameInput = prompt("⚠️ CREDIT LOG MANDATE:\nEnter Customer Name & Phone Number:\n(e.g., Rajesh Kumar - 9876543210)");
        
        if (!nameInput || nameInput.trim() === "") {
            alert("Checkout Blocked! Core accounting requires an identity token string to log outstanding debt.");
            return;
        }
        customerIdentityRecord = nameInput.trim();

        const cashDownPayment = prompt(`Invoice Total Value is ₹${totalBillAmount.toFixed(2)}.\n\nHow much cash/online money did this customer pay right now?\n(Enter 0 for 100% Full Udhaar Khata)`);
        
        if (cashDownPayment === null) return; 

        const parsedDownPayment = parseFloat(cashDownPayment);
        if (isNaN(parsedDownPayment) || parsedDownPayment < 0 || parsedDownPayment > totalBillAmount) {
            alert("Data Integrity Error: Invalid input value. Amount paid must match financial balance limits.");
            return;
        }

        allocatedPaid = parsedDownPayment;
        allocatedPending = totalBillAmount - allocatedPaid;
        activePaymentType = allocatedPaid > 0 ? "PARTIAL" : "CREDIT";
    } else {
        const casualTracking = prompt("Enter Customer Identity Notes [OPTIONAL]:\n(Leave blank for default Walk-in profile registration)");
        if (casualTracking && casualTracking.trim() !== "") {
            customerIdentityRecord = casualTracking.trim();
        }
    }

    const comprehensiveOrderPayload = {
        payment_method: activePaymentType,
        total_amount: totalBillAmount,
        amount_paid: allocatedPaid,
        amount_pending: allocatedPending,
        customer_info: customerIdentityRecord,
        items: cart.map(item => ({
            product_id: item.id,
            quantity: item.quantity
        }))
    };

    try {
        checkoutBtn.disabled = true; // Block double-click double processing loops
        
        const response = await fetch(`${API_BASE_URL}/orders/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(comprehensiveOrderPayload)
        });

        // 🌟 FIX: Parse the JSON string stream into an object BEFORE evaluating status
        const data = await response.json();

        if (response.ok) {
            let successMessage = `🎉 Transaction Finalized Safely!\n\nInvoice ID: #${data.id}\nTotal Bill: ₹${parseFloat(data.total_amount).toFixed(2)}\nPayment Status: ${data.payment_status}`;
            
            if (data.amount_pending > 0) {
                successMessage += `\n\n📝 KHATA BALANCE RECORDED:\nAccount Holder: ${data.customer_info}\nPending Udhaar Ledger Debt: ₹${parseFloat(data.amount_pending).toFixed(2)}`;
            }
            
            alert(successMessage);
            cart = []; 
            renderCart();
            barcodeInput.focus(); 
        } else {
            // Intercept gracefully if a backend validation error (400/404/422) occurs
            alert("Checkout Rejected by Backend Pipeline: " + (data.detail || "Validation check breakdown"));
        }
    } catch (error) {
        console.error("Frontend Communication Error Trace:", error);
        alert("Frontend App Error: Connection interrupted or unhandled asset mapping.");
    } finally {
        checkoutBtn.disabled = false;
    }
});

// Force automatic focus on page boot
barcodeInput.focus();