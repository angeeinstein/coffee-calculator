# Counter Reading & Expected Cash Bug Fixes

## Issues Fixed

### 1. Counter Readings Not Persisting After Submission
**Problem:** Counter inputs were being cleared after submission, causing users to lose their cumulative counter values.

**Root Cause:** The `submitCounterReading()` function was clearing ALL form inputs including the counter values.

**Solution:** Modified `submitCounterReading()` to only clear the cash amount and notes fields, leaving counter values intact since they represent cumulative totals.

```javascript
// DON'T clear counter inputs - they are cumulative totals
// Only clear cash and notes
document.getElementById('cash-in-register').value = '';
document.getElementById('counter-notes').value = '';
```

### 2. Counter Inputs Not Restoring Last Values
**Problem:** When switching tabs or reloading the page, counter inputs showed empty fields instead of the last submitted values.

**Root Cause:** The `populateCounterInputs()` function was creating fresh empty inputs without checking for previous readings.

**Solution:** Updated `populateCounterInputs()` to be async and fetch the latest counter reading to pre-populate the inputs:

```javascript
async function populateCounterInputs() {
    // ... fetch last reading ...
    if (data.success && data.readings && data.readings.length > 0) {
        lastReadingData = data.readings[0].counter_data; // Most recent reading
    }
    
    // Set value from last reading
    const lastValue = lastReadingData[drinkName] || 0;
    inputGroup.innerHTML = `
        <input ... value="${lastValue}">
    `;
}
```

### 3. Expected Cash Not Updating (Showing €0.00)
**Problem:** Expected cash register balance showed €0.00 even after submitting counter readings.

**Root Cause:** Vending prices weren't being captured correctly from the UI, so sales records weren't being created with proper revenue values.

**Solution:** Fixed `submitCounterReading()` to get vending prices directly from the input fields instead of relying on `calculationResults`:

```javascript
// Get vending price directly from the drink input field
drinks.forEach(drink => {
    const vendingPriceInput = document.getElementById(`vending-price-${drinkId}`);
    const vendingPrice = parseFloat(vendingPriceInput ? vendingPriceInput.value : 0);
    if (vendingPrice > 0) {
        productPrices[drinkName] = vendingPrice;
    }
});
```

### 4. Missing Warning for Products Without Vending Prices
**Problem:** Users could submit counter readings without setting vending prices, resulting in €0 revenue calculations without knowing why.

**Solution:** Added a confirmation dialog if no vending prices are set:

```javascript
if (Object.keys(productPrices).length === 0) {
    if (!confirm('Warning: No vending prices set for any products. Revenue will be calculated as €0.\n\nYou can set vending prices in the green input fields above each drink.\n\nContinue anyway?')) {
        return;
    }
}
```

### 5. Counter Inputs Not Updating After Loading Configuration
**Problem:** When loading a saved configuration, counter inputs weren't refreshed with the latest values.

**Solution:** Added a call to `populateCounterInputs()` after loading a configuration if the sales tracking section is visible:

```javascript
// Update counter inputs if the sales tracking tab is visible
const salesTrackingSection = document.getElementById('sales-tracking-section');
if (salesTrackingSection && !salesTrackingSection.classList.contains('hidden')) {
    populateCounterInputs();
}
```

### 6. Sales Tracking Not Loading on Page Load
**Problem:** When refreshing the page, sales tracking data wasn't automatically loaded.

**Solution:** Added initialization code in `DOMContentLoaded` event handler to load sales data based on the active tab:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // ... existing code ...
    
    // Initialize sales tracking if user is logged in
    if (salesTrackingSection && !salesTrackingSection.classList.contains('hidden')) {
        if (tabName === 'counter') {
            populateCounterInputs();
            loadRecentReadings();
        } else if (tabName === 'register') {
            loadCashRegisterBalance();
            loadCashEvents();
        }
    }
});
```

### 7. Backend Logging for Missing Prices
**Problem:** No visibility when products had sales but no prices were recorded.

**Solution:** Added warning logging in the backend when quantity is sold but no price is found:

```python
if quantity_sold > 0:
    if product_name in product_prices:
        # ... create sales record ...
    else:
        print(f"Warning: No price found for product '{product_name}' with {quantity_sold} units sold")
```

## Testing Checklist

- [x] Counter readings persist after submission
- [x] Counter inputs show last submitted values on tab switch
- [x] Counter inputs restore on page reload
- [x] Expected cash calculates correctly with vending prices
- [x] Warning shown when no vending prices are set
- [x] Sales records created with correct revenue
- [x] Cash register balance updates after submission
- [x] Configuration loading updates counter inputs
- [x] Page reload initializes sales tracking data

## How Expected Cash Works

The expected cash calculation follows this formula:

```
Expected Cash = Previous Cash + Total Sales Revenue + Deposits - Withdrawals
```

Where:
- **Previous Cash**: The cash_in_register value from the previous counter reading
- **Total Sales Revenue**: Sum of (quantity_sold × vending_price) for all products
- **Deposits**: Money added to the register (e.g., change added)
- **Withdrawals**: Money removed from the register (e.g., bank deposits, petty cash)

**Important:** Sales revenue is ONLY calculated if:
1. There is a previous reading to compare against
2. The vending price is set for each product (green input field)
3. The counter value increased from the previous reading

On the first reading, expected cash will equal the actual cash entered, since there's no previous reading to compare.

## Files Modified

### Frontend (`static/app.js`)
- `submitCounterReading()` - Fixed to not clear counter inputs, get vending prices from UI
- `populateCounterInputs()` - Made async, fetches and restores last reading values
- `loadConfiguration()` - Added counter inputs refresh
- `DOMContentLoaded` event handler - Added sales tracking initialization

### Backend (`app.py`)
- `submit_counter_reading()` - Added warning logging for missing prices
- Logic now separates quantity checking from price checking for better debugging

## Console Debug Commands

To debug counter reading issues in the browser console:

```javascript
// Check current counter data being sent
console.log('Counter data:', counterData);
console.log('Product prices:', productPrices);

// Check last reading
fetch('/api/counter-readings?config_id=' + currentConfigId, {credentials: 'include'})
    .then(r => r.json())
    .then(d => console.log('Last reading:', d.readings[0]));

// Check cash register balance
fetch('/api/cash-register/balance?config_id=' + currentConfigId, {credentials: 'include'})
    .then(r => r.json())
    .then(d => console.log('Balance:', d));
```

## Common Issues & Solutions

### Issue: Expected cash still shows €0.00
**Solution:** 
1. Make sure vending prices are set (green input fields)
2. Submit a counter reading (this becomes your baseline)
3. Update counter values and submit again (sales will now be calculated)
4. Check browser console for any warnings

### Issue: Counter inputs show 0 instead of last values
**Solution:**
1. Refresh the page
2. Make sure you're viewing the correct configuration (check top of page)
3. Switch to a different tab and back to Counter Reading tab

### Issue: Sales not showing in statistics
**Solution:**
1. Ensure you've submitted at least TWO readings (first reading is baseline)
2. Verify vending prices are set for all products
3. Check that counter values increased between readings
