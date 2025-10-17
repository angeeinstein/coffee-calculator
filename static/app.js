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
        
        if (Object.keys(drinkIngredients).length > 0) {
            drinks.push({
                name: drinkName,
                ingredients: drinkIngredients
            });
        }
    });
    
    return {
        cleaning_cost: cleaningCost,
        products_per_day: productsPerDay,
        ingredients: ingredientCosts,
        drinks: drinks
    };
}

async function calculateCosts() {
    const data = collectData();
    
    if (data.drinks.length === 0) {
        alert('Please add at least one drink with ingredients!');
        return;
    }
    
    try {
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            calculationResults = {
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
            breakdownHTML += `
                <tr>
                    <td>${item.ingredient.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</td>
                    <td>${(item.amount * 1000).toFixed(1)} ${getUnitForIngredient(item.ingredient)}</td>
                    <td>€${item.unit_cost.toFixed(2)}/${getBaseUnitForIngredient(item.ingredient)}</td>
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
        const response = await fetch('/api/configs');
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
        
        const date = new Date(config.updated_at);
        const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        configItem.innerHTML = `
            <div style="flex: 1;" onclick="loadConfiguration(${config.id})">
                <div class="config-name">${escapeHtml(config.name)}</div>
                <div class="config-date">${dateStr}</div>
            </div>
            <button class="config-delete" onclick="event.stopPropagation(); deleteConfiguration(${config.id})">🗑️</button>
        `;
        
        configList.appendChild(configItem);
    });
}

async function loadConfiguration(configId) {
    try {
        const response = await fetch(`/api/configs/${configId}`);
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
            method: 'DELETE'
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
    const modal = document.getElementById('saveModal');
    if (event.target === modal) {
        closeSaveModal();
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
