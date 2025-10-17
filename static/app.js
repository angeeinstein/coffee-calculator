let drinkCounter = 0;
let calculationResults = null;
let currentConfigId = null;
let currentConfigName = null;

// Available ingredients
const ingredients = [
    'coffee_beans',
    'milk',
    'chocolate_powder',
    'sugar',
    'water',
    'vanilla_syrup'
];

// Initialize with one drink and load configurations
document.addEventListener('DOMContentLoaded', function() {
    addDrink();
    loadConfigurations();
    loadTeaBags();
});

function addDrink() {
    drinkCounter++;
    const drinksContainer = document.getElementById('drinks-container');
    
    const drinkCard = document.createElement('div');
    drinkCard.className = 'drink-card';
    drinkCard.id = `drink-${drinkCounter}`;
    
    drinkCard.innerHTML = `
        <div class="drink-header">
            <input type="text" placeholder="Drink Name (e.g., Cappuccino)" id="drink-name-${drinkCounter}" />
            <button class="btn btn-danger" onclick="removeDrink(${drinkCounter})">Remove</button>
        </div>
        <div id="ingredients-${drinkCounter}">
            <div class="ingredient-row">
                <div class="input-group">
                    <label>Ingredient</label>
                    <select class="ingredient-select" onchange="updateUnitLabel(this)">
                        <option value="">Select ingredient</option>
                        ${ingredients.map(ing => `<option value="${ing}">${ing.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>`).join('')}
                    </select>
                </div>
                <div class="input-group">
                    <label class="amount-label">Amount</label>
                    <input type="number" class="ingredient-amount" step="0.1" min="0" placeholder="0.0" />
                </div>
                <button class="btn btn-danger" onclick="removeIngredientRow(this)" style="margin-top: 25px;">✕</button>
            </div>
        </div>
        <button class="btn" onclick="addIngredientRow(${drinkCounter})">+ Add Ingredient</button>
        
        <div class="custom-items-section" style="margin-top: 20px; padding-top: 20px; border-top: 2px solid #e0e0e0;">
            <h4 style="margin-bottom: 10px; color: #667eea;">🍪 Custom Items (Cookies, etc.)</h4>
            <div id="custom-items-${drinkCounter}">
                <!-- Custom items will be added here -->
            </div>
            <button class="btn" onclick="addCustomItem(${drinkCounter})" style="margin-top: 10px; font-size: 0.9em; background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);">
                ➕ Add Custom Item
            </button>
        </div>
    `;
    
    drinksContainer.appendChild(drinkCard);
}

function removeDrink(drinkId) {
    const drinkCard = document.getElementById(`drink-${drinkId}`);
    if (drinkCard) {
        drinkCard.remove();
    }
}

function addIngredientRow(drinkId) {
    const ingredientsContainer = document.getElementById(`ingredients-${drinkId}`);
    
    const row = document.createElement('div');
    row.className = 'ingredient-row';
    row.innerHTML = `
        <div class="input-group">
            <label>Ingredient</label>
            <select class="ingredient-select" onchange="updateUnitLabel(this)">
                <option value="">Select ingredient</option>
                ${ingredients.map(ing => `<option value="${ing}">${ing.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>`).join('')}
            </select>
        </div>
        <div class="input-group">
            <label class="amount-label">Amount</label>
            <input type="number" class="ingredient-amount" step="0.1" min="0" placeholder="0.0" />
        </div>
        <button class="btn btn-danger" onclick="removeIngredientRow(this)" style="margin-top: 25px;">✕</button>
    `;
    
    ingredientsContainer.appendChild(row);
}

function updateUnitLabel(selectElement) {
    const row = selectElement.closest('.ingredient-row');
    const label = row.querySelector('.amount-label');
    const ingredient = selectElement.value;
    
    // Liquids use ml, solids use g
    const liquidIngredients = ['milk', 'water', 'vanilla_syrup'];
    const unit = liquidIngredients.includes(ingredient) ? 'ml' : 'g';
    
    label.textContent = `Amount (${unit})`;
}

function removeIngredientRow(button) {
    const row = button.closest('.ingredient-row');
    const container = row.parentElement;
    
    // Keep at least one row
    if (container.children.length > 1) {
        row.remove();
    } else {
        alert('Each drink must have at least one ingredient!');
    }
}

function collectData() {
    // Collect fixed costs
    const cleaningCost = parseFloat(document.getElementById('cleaning_cost').value) || 0;
    const productsPerDay = parseFloat(document.getElementById('products_per_day').value) || 1;
    
    // Collect ingredient costs (per kg or L)
    const ingredientCosts = {};
    ingredients.forEach(ing => {
        const value = parseFloat(document.getElementById(ing).value) || 0;
        ingredientCosts[ing] = value;
    });
    
    // Collect drinks
    const drinks = [];
    const drinkCards = document.querySelectorAll('.drink-card');
    
    drinkCards.forEach(card => {
        const drinkId = card.id.split('-')[1];
        const drinkName = document.getElementById(`drink-name-${drinkId}`).value.trim();
        
        if (!drinkName) {
            return; // Skip drinks without names
        }
        
        const drinkIngredients = {};
        const ingredientRows = card.querySelectorAll('.ingredient-row');
        
        ingredientRows.forEach(row => {
            const select = row.querySelector('.ingredient-select');
            const amountInput = row.querySelector('.ingredient-amount');
            
            const ingredientName = select.value;
            let amount = parseFloat(amountInput.value) || 0;
            
            if (ingredientName && amount > 0) {
                // Convert g to kg or ml to L (divide by 1000)
                // This allows backend to calculate: (cost_per_kg * kg_used) or (cost_per_L * L_used)
                drinkIngredients[ingredientName] = amount / 1000;
            }
        });
        
        // Collect custom items for this drink
        const customItems = [];
        const customItemsContainer = document.getElementById(`custom-items-${drinkId}`);
        if (customItemsContainer) {
            customItemsContainer.querySelectorAll('.custom-item-row').forEach(row => {
                const name = row.querySelector('.custom-item-name').value.trim();
                const cost = parseFloat(row.querySelector('.custom-item-cost').value) || 0;
                
                if (name && cost > 0) {
                    customItems.push({ name, cost });
                }
            });
        }
        
        if (Object.keys(drinkIngredients).length > 0 || customItems.length > 0) {
            drinks.push({
                name: drinkName,
                ingredients: drinkIngredients,
                tea_bags: {}, // Will be added if needed
                custom_items: customItems
            });
        }
    });
    
    return {
        cleaning_cost: cleaningCost,
        products_per_day: productsPerDay,
        ingredients: ingredientCosts,
        tea_bags: teaBags,
        drinks: drinks
    };
}

async function calculateCosts() {
    const data = collectData();
    
    if (data.drinks.length === 0) {
        alert('Please add at least one drink with ingredients!');
        return;
    }
    
    // Debug output
    console.log('=== Calculation Data ===');
    console.log('Fixed Costs:', {
        cleaning_cost: data.cleaning_cost,
        products_per_day: data.products_per_day
    });
    console.log('Ingredient Prices (€/kg or €/L):', data.ingredients);
    console.log('Drinks:', data.drinks);
    
    try {
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        console.log('=== Calculation Results ===');
        console.log('Results from backend:', result.results);
        
        if (result.success) {
            calculationResults = {
                cleaning_cost: data.cleaning_cost,
                products_per_day: data.products_per_day,
                ingredients: data.ingredients,
                drinks: data.drinks,
                results: result.results
            };
            displayResults(result.results);
            document.getElementById('download-pdf-btn').classList.remove('hidden');
        } else {
            alert('Error calculating costs: ' + result.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function displayResults(results) {
    const resultsSection = document.getElementById('results');
    const resultsContainer = document.getElementById('results-container');
    
    resultsContainer.innerHTML = '';
    
    results.forEach(result => {
        const resultCard = document.createElement('div');
        resultCard.className = 'result-card';
        
        let breakdownHTML = `
            <table class="breakdown-table">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Amount</th>
                        <th>Unit Cost</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        result.breakdown.forEach(item => {
            let amountDisplay = '';
            let unitCostDisplay = '';
            
            if (item.type === 'per_unit') {
                // Tea bags or per-unit items
                amountDisplay = `${item.amount} units`;
                unitCostDisplay = `€${item.unit_cost.toFixed(2)}/unit`;
            } else if (item.type === 'custom') {
                // Custom items
                amountDisplay = `1 item`;
                unitCostDisplay = `€${item.unit_cost.toFixed(2)}`;
            } else {
                // Bulk ingredients (default)
                amountDisplay = `${(item.amount * 1000).toFixed(1)} ${getUnitForIngredient(item.ingredient)}`;
                unitCostDisplay = `€${item.unit_cost.toFixed(2)}/${getBaseUnitForIngredient(item.ingredient)}`;
            }
            
            breakdownHTML += `
                <tr>
                    <td>${item.ingredient.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</td>
                    <td>${amountDisplay}</td>
                    <td>${unitCostDisplay}</td>
                    <td><strong>€${item.total_cost.toFixed(2)}</strong></td>
                </tr>
            `;
        });
        
        // Add cleaning cost row if present
        if (result.cleaning_cost_per_product && result.cleaning_cost_per_product > 0) {
            breakdownHTML += `
                <tr style="background-color: #e8f5e9;">
                    <td><strong>Daily Cleaning Cost</strong></td>
                    <td>Per product</td>
                    <td>€${result.total_cleaning_cost?.toFixed(2) || '0.00'}/day</td>
                    <td><strong>€${result.cleaning_cost_per_product.toFixed(2)}</strong></td>
                </tr>
            `;
        }
        
        breakdownHTML += `
                </tbody>
            </table>
        `;
        
        // Show ingredient subtotal if cleaning cost is present
        let subtotalHTML = '';
        if (result.cleaning_cost_per_product && result.cleaning_cost_per_product > 0) {
            const ingredientCost = result.total_cost - result.cleaning_cost_per_product;
            subtotalHTML = `
                <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>Ingredient Cost:</span>
                        <span><strong>€${ingredientCost.toFixed(2)}</strong></span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>Cleaning Cost (per product):</span>
                        <span><strong>€${result.cleaning_cost_per_product.toFixed(2)}</strong></span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 1.1em; padding-top: 8px; border-top: 2px solid #ddd;">
                        <span><strong>Total Cost:</strong></span>
                        <span style="color: #2ecc71;"><strong>€${result.total_cost.toFixed(2)}</strong></span>
                    </div>
                </div>
            `;
        }
        
        resultCard.innerHTML = `
            <h3>${result.name}</h3>
            <div class="result-total">Total Cost: €${result.total_cost.toFixed(2)}</div>
            ${breakdownHTML}
            ${subtotalHTML}
        `;
        
        resultsContainer.appendChild(resultCard);
    });
    
    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

async function downloadPDF() {
    if (!calculationResults) {
        alert('Please calculate costs first!');
        return;
    }
    
    try {
        const response = await fetch('/api/generate-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(calculationResults)
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `coffee_cost_report_${new Date().toISOString().slice(0, 10)}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            alert('Error generating PDF');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Configuration Management Functions

async function loadConfigurations() {
    try {
        const response = await fetch('/api/configs', {
            credentials: 'include'
        });
        const result = await response.json();
        
        if (result.success) {
            displayConfigurations(result.configs);
        }
    } catch (error) {
        console.error('Error loading configurations:', error);
    }
}

function displayConfigurations(configs) {
    const configList = document.getElementById('config-list');
    
    if (configs.length === 0) {
        configList.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">No saved configurations yet</p>';
        return;
    }
    
    configList.innerHTML = '';
    
    configs.forEach(config => {
        const configItem = document.createElement('div');
        configItem.className = 'config-item';
        if (currentConfigId === config.id) {
            configItem.classList.add('active');
        }
        
        // Mark shared configs
        if (config.access_type === 'shared') {
            configItem.classList.add('shared');
        }
        
        const date = new Date(config.updated_at);
        const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        const ownerLabel = config.owner_name ? `<span class="config-owner">by ${escapeHtml(config.owner_name)}</span>` : '';
        const shareIcon = config.access_type === 'shared' ? '🔗 ' : '';
        
        configItem.innerHTML = `
            <div style="flex: 1;" onclick="loadConfiguration(${config.id})">
                <div class="config-name">${shareIcon}${escapeHtml(config.name)} ${ownerLabel}</div>
                <div class="config-date">${dateStr}</div>
            </div>
            <div class="config-actions">
                ${config.access_type === 'owner' ? `<button class="config-share" onclick="event.stopPropagation(); showShareModal(${config.id}, '${escapeHtml(config.name).replace(/'/g, "\\'")}')">📤</button>` : ''}
                ${config.can_edit || config.access_type === 'owner' ? `<button class="config-delete" onclick="event.stopPropagation(); deleteConfiguration(${config.id})">🗑️</button>` : ''}
            </div>
        `;
        
        configList.appendChild(configItem);
    });
}

async function loadConfiguration(configId) {
    try {
        const response = await fetch(`/api/configs/${configId}`, {
            credentials: 'include'
        });
        const result = await response.json();
        
        if (result.success) {
            const config = result.config;
            
            // Set current config
            currentConfigId = config.id;
            currentConfigName = config.name;
            
            // Update UI to show current config
            document.getElementById('current-config').style.display = 'block';
            document.getElementById('current-config-name').textContent = config.name;
            
            // Load fixed costs
            document.getElementById('cleaning_cost').value = config.cleaning_cost || 0;
            document.getElementById('products_per_day').value = config.products_per_day || 1;
            
            // Load ingredients
            ingredients.forEach(ing => {
                const input = document.getElementById(ing);
                if (input) {
                    input.value = config.ingredients[ing] || 0;
                }
            });
            
            // Clear existing drinks
            document.getElementById('drinks-container').innerHTML = '';
            drinkCounter = 0;
            
            // Load drinks
            config.drinks.forEach(drink => {
                addDrink();
                const drinkId = drinkCounter;
                
                // Set drink name
                document.getElementById(`drink-name-${drinkId}`).value = drink.name;
                
                // Clear default ingredient row
                const ingredientsContainer = document.getElementById(`ingredients-${drinkId}`);
                ingredientsContainer.innerHTML = '';
                
                // Add ingredient rows
                Object.entries(drink.ingredients).forEach(([ingredientName, amount]) => {
                    const unit = getUnitForIngredient(ingredientName);
                    const displayAmount = amount * 1000; // Convert back to g/ml for display
                    
                    const row = document.createElement('div');
                    row.className = 'ingredient-row';
                    row.innerHTML = `
                        <div class="input-group">
                            <label>Ingredient</label>
                            <select class="ingredient-select" onchange="updateUnitLabel(this)">
                                <option value="">Select ingredient</option>
                                ${ingredients.map(ing => `<option value="${ing}" ${ing === ingredientName ? 'selected' : ''}>${ing.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>`).join('')}
                            </select>
                        </div>
                        <div class="input-group">
                            <label class="amount-label">Amount (${unit})</label>
                            <input type="number" class="ingredient-amount" step="0.1" min="0" placeholder="0.0" value="${displayAmount.toFixed(1)}" />
                        </div>
                        <button class="btn btn-danger" onclick="removeIngredientRow(this)" style="margin-top: 25px;">✕</button>
                    `;
                    ingredientsContainer.appendChild(row);
                });
                
                // Load custom items if any
                if (drink.custom_items && drink.custom_items.length > 0) {
                    const customItemsContainer = document.getElementById(`custom-items-${drinkId}`);
                    if (customItemsContainer) {
                        drink.custom_items.forEach(item => {
                            const div = document.createElement('div');
                            div.className = 'custom-item-row';
                            div.style.cssText = 'display: flex; gap: 10px; margin-bottom: 10px;';
                            div.innerHTML = `
                                <input type="text" 
                                       placeholder="Item name (e.g., Cookie)" 
                                       class="custom-item-name"
                                       value="${escapeHtml(item.name)}"
                                       style="flex: 2; padding: 8px; border-radius: 6px; border: 1px solid #ddd;">
                                <input type="number" 
                                       placeholder="Cost (€)" 
                                       class="custom-item-cost"
                                       value="${item.cost}"
                                       step="0.01"
                                       style="flex: 1; padding: 8px; border-radius: 6px; border: 1px solid #ddd;">
                                <button onclick="this.parentElement.remove()" 
                                        style="background: #e74c3c; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer;">
                                    ✕
                                </button>
                            `;
                            customItemsContainer.appendChild(div);
                        });
                    }
                }
            });
            
            // Reload configurations to update active state
            loadConfigurations();
            
            // Clear results
            calculationResults = null;
            document.getElementById('results').classList.add('hidden');
            document.getElementById('download-pdf-btn').classList.add('hidden');
            
        } else {
            alert('Error loading configuration: ' + result.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function showSaveModal() {
    const data = collectData();
    
    if (data.drinks.length === 0) {
        alert('Please add at least one drink before saving!');
        return;
    }
    
    document.getElementById('saveModal').style.display = 'block';
    document.getElementById('config-name-input').value = currentConfigName || '';
    document.getElementById('config-name-input').focus();
}

function closeSaveModal() {
    document.getElementById('saveModal').style.display = 'none';
    document.getElementById('config-name-input').value = '';
}

async function saveConfiguration() {
    const name = document.getElementById('config-name-input').value.trim();
    
    if (!name) {
        alert('Please enter a configuration name!');
        return;
    }
    
    const data = collectData();
    
    if (data.drinks.length === 0) {
        alert('Please add at least one drink!');
        return;
    }
    
    try {
        const payload = {
            name: name,
            cleaning_cost: data.cleaning_cost,
            products_per_day: data.products_per_day,
            ingredients: data.ingredients,
            drinks: data.drinks
        };
        
        // If updating existing config
        if (currentConfigId && currentConfigName === name) {
            payload.id = currentConfigId;
        }
        
        const response = await fetch('/api/configs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentConfigId = result.id;
            currentConfigName = name;
            
            document.getElementById('current-config').style.display = 'block';
            document.getElementById('current-config-name').textContent = name;
            
            closeSaveModal();
            loadConfigurations();
            
            alert('Configuration saved successfully!');
        } else {
            alert('Error saving configuration: ' + result.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function deleteConfiguration(configId) {
    if (!confirm('Are you sure you want to delete this configuration?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/configs/${configId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (result.success) {
            // If deleted config was the current one, clear it
            if (currentConfigId === configId) {
                currentConfigId = null;
                currentConfigName = null;
                document.getElementById('current-config').style.display = 'none';
            }
            
            loadConfigurations();
            alert('Configuration deleted successfully!');
        } else {
            alert('Error deleting configuration: ' + result.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function newConfiguration() {
    if (confirm('This will clear the current configuration. Continue?')) {
        currentConfigId = null;
        currentConfigName = null;
        document.getElementById('current-config').style.display = 'none';
        
        // Clear fixed costs
        document.getElementById('cleaning_cost').value = '';
        document.getElementById('products_per_day').value = '';
        
        // Clear ingredients
        ingredients.forEach(ing => {
            const input = document.getElementById(ing);
            if (input) {
                input.value = '';
            }
        });
        
        // Clear drinks
        document.getElementById('drinks-container').innerHTML = '';
        drinkCounter = 0;
        addDrink();
        
        // Clear results
        calculationResults = null;
        document.getElementById('results').classList.add('hidden');
        document.getElementById('download-pdf-btn').classList.add('hidden');
        
        loadConfigurations();
    }
}

function getUnitForIngredient(ingredient) {
    const liquidIngredients = ['milk', 'water', 'vanilla_syrup'];
    return liquidIngredients.includes(ingredient) ? 'ml' : 'g';
}

function getBaseUnitForIngredient(ingredient) {
    const liquidIngredients = ['milk', 'water', 'vanilla_syrup'];
    return liquidIngredients.includes(ingredient) ? 'L' : 'kg';
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Close modal when clicking outside
window.onclick = function(event) {
    const saveModal = document.getElementById('saveModal');
    const shareModal = document.getElementById('shareModal');
    if (event.target === saveModal) {
        closeSaveModal();
    }
    if (event.target === shareModal) {
        closeShareModal();
    }
}

// Allow Enter key to save in modal
document.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        const modal = document.getElementById('saveModal');
        if (modal.style.display === 'block') {
            saveConfiguration();
        }
    }
});

// ============================================
// LOGOUT FUNCTIONALITY
// ============================================
async function logout() {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Logout error:', error);
        alert('Error logging out. Please try again.');
    }
}

// ============================================
// TEA BAG MANAGEMENT
// ============================================
let teaBags = {}; // Store tea bag data

async function loadTeaBags() {
    try {
        const response = await fetch('/api/tea-bags', {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            teaBags = {};
            const container = document.getElementById('tea-bag-inputs');
            container.innerHTML = '';
            
            data.tea_bags.forEach(bag => {
                teaBags[bag.name] = bag.cost_per_unit;
                addTeaBagInput(bag.name, bag.cost_per_unit, bag.id);
            });
        }
    } catch (error) {
        console.error('Error loading tea bags:', error);
    }
}

function addTeaBagInput(name = '', cost = '', id = null) {
    const container = document.getElementById('tea-bag-inputs');
    const teaBagId = id || 'new';
    
    const div = document.createElement('div');
    div.className = 'tea-bag-item';
    div.dataset.teabagId = teaBagId;
    div.style.cssText = 'display: flex; gap: 10px; align-items: center; background: #f8f9fa; padding: 10px; border-radius: 8px;';
    
    div.innerHTML = `
        <input type="text" 
               placeholder="Tea Bag Name (e.g., Earl Grey)" 
               value="${name}"
               onchange="saveTeaBag(this)"
               style="flex: 2; padding: 8px; border-radius: 6px; border: 1px solid #ddd;">
        <input type="number" 
               placeholder="0.00" 
               value="${cost}"
               step="0.01"
               onchange="saveTeaBag(this)"
               style="flex: 1; padding: 8px; border-radius: 6px; border: 1px solid #ddd;">
        <button onclick="deleteTeaBag('${teaBagId}')" 
                style="background: #e74c3c; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 1.2em;">
            🗑️
        </button>
    `;
    
    container.appendChild(div);
}

async function saveTeaBag(input) {
    const container = input.closest('[data-teabag-id]');
    const inputs = container.querySelectorAll('input');
    const name = inputs[0].value.trim();
    const cost = parseFloat(inputs[1].value) || 0;
    const id = container.dataset.teabagId !== 'new' ? container.dataset.teabagId : null;
    
    if (!name || cost <= 0) return;
    
    try {
        const response = await fetch('/api/tea-bags', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ id: id === 'new' ? null : parseInt(id), name, cost_per_unit: cost })
        });
        
        const data = await response.json();
        if (data.success) {
            teaBags[name] = cost;
            loadTeaBags(); // Reload to get proper IDs
        }
    } catch (error) {
        console.error('Error saving tea bag:', error);
    }
}

async function deleteTeaBag(id) {
    if (!confirm('Delete this tea bag?')) return;
    
    if (id === 'new') {
        loadTeaBags();
        return;
    }
    
    try {
        const response = await fetch(`/api/tea-bags/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            loadTeaBags();
        }
    } catch (error) {
        console.error('Error deleting tea bag:', error);
    }
}

function addTeaBag() {
    addTeaBagInput();
}

// ============================================
// CUSTOM ITEMS PER DRINK
// ============================================
function addCustomItem(drinkId) {
    const container = document.getElementById(`custom-items-${drinkId}`);
    if (!container) return;
    
    const itemId = `custom-${drinkId}-${Date.now()}`;
    
    const div = document.createElement('div');
    div.className = 'custom-item-row';
    div.dataset.itemId = itemId;
    div.style.cssText = 'display: flex; gap: 10px; margin-bottom: 10px;';
    
    div.innerHTML = `
        <input type="text" 
               placeholder="Item name (e.g., Cookie)" 
               class="custom-item-name"
               style="flex: 2; padding: 8px; border-radius: 6px; border: 1px solid #ddd;">
        <input type="number" 
               placeholder="Cost (€)" 
               class="custom-item-cost"
               step="0.01"
               style="flex: 1; padding: 8px; border-radius: 6px; border: 1px solid #ddd;">
        <button onclick="this.parentElement.remove()" 
                style="background: #e74c3c; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer;">
            ✕
        </button>
    `;
    
    container.appendChild(div);
}

// ============================================
// SHARING FUNCTIONALITY
// ============================================
let currentShareConfigId = null;

function showShareModal(configId, configName) {
    currentShareConfigId = configId;
    const modal = document.getElementById('shareModal');
    document.getElementById('share-config-name').textContent = configName;
    
    loadSharedUsers(configId);
    modal.style.display = 'flex';
}

function closeShareModal() {
    document.getElementById('shareModal').style.display = 'none';
    document.getElementById('shareEmail').value = '';
    document.getElementById('shareCanEdit').checked = false;
    currentShareConfigId = null;
}

async function loadSharedUsers(configId) {
    try {
        const response = await fetch(`/api/configs/${configId}/shared-users`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('sharedUsersList');
            if (data.shared_users.length === 0) {
                container.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">Not shared with anyone yet</p>';
            } else {
                container.innerHTML = '<h4 style="margin-bottom: 10px; color: #333;">Shared with:</h4>';
                data.shared_users.forEach(user => {
                    const userDiv = document.createElement('div');
                    userDiv.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 8px; background: white; border-radius: 6px; margin-bottom: 5px;';
                    userDiv.innerHTML = `
                        <span style="color: #333;"><strong>${escapeHtml(user.name)}</strong> (${escapeHtml(user.email)}) - ${user.can_edit ? '✏️ Can Edit' : '👁️ View Only'}</span>
                        <button onclick="unshareWith(${configId}, ${user.user_id})" 
                                style="background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.85em;">
                            Remove
                        </button>
                    `;
                    container.appendChild(userDiv);
                });
            }
        }
    } catch (error) {
        console.error('Error loading shared users:', error);
    }
}

async function shareConfiguration() {
    const email = document.getElementById('shareEmail').value.trim();
    const canEdit = document.getElementById('shareCanEdit').checked;
    
    if (!email) {
        alert('Please enter an email address');
        return;
    }
    
    try {
        const response = await fetch(`/api/configs/${currentShareConfigId}/share`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ email, can_edit: canEdit })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Configuration shared successfully!');
            document.getElementById('shareEmail').value = '';
            loadSharedUsers(currentShareConfigId);
        } else {
            alert(data.error || 'Failed to share configuration');
        }
    } catch (error) {
        console.error('Error sharing configuration:', error);
        alert('Network error. Please try again.');
    }
}

async function unshareWith(configId, userId) {
    if (!confirm('Remove sharing access for this user?')) return;
    
    try {
        const response = await fetch(`/api/configs/${configId}/unshare/${userId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            loadSharedUsers(configId);
        }
    } catch (error) {
        console.error('Error removing share:', error);
    }
}
