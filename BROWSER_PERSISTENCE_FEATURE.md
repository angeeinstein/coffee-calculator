# Browser Persistence Feature

## Summary

Implemented localStorage-based persistence so form data survives browser refreshes while maintaining clean separation between configurations.

## How It Works

### Auto-Save
- **Every input change** is automatically saved to localStorage after a 500ms debounce
- Saves: ingredient prices, drink names, vending prices, ingredients, tea bags, custom items, fixed costs
- **No manual save required** - happens automatically in the background

### Auto-Restore
- On page load, the app checks for saved data in localStorage
- If found, **automatically restores** the entire form state
- If not found, creates a default empty drink card

### Config-Specific Behavior
- **Loading a saved configuration**: Clears localStorage first, then loads config data from database
- **Creating a new configuration**: Clears localStorage, creates fresh form
- **Saving a configuration**: Updates localStorage with current state

## User Experience

### Before:
1. Fill out form with drinks and prices
2. Accidentally refresh page
3. **All data lost** ❌
4. Start over from scratch

### After:
1. Fill out form with drinks and prices
2. Data auto-saves continuously
3. Refresh page or close browser
4. **All data restored automatically** ✅
5. Continue where you left off

### When Loading Different Config:
1. Working on "Morning Menu" config
2. Click to load "Afternoon Menu" config
3. localStorage cleared
4. "Afternoon Menu" loads fresh from database
5. Start editing "Afternoon Menu"
6. Data auto-saves for "Afternoon Menu"

## Implementation Details

### Data Structure Saved to localStorage:

```javascript
{
  configId: 123,                    // Current config ID (if any)
  configName: "Morning Menu",       // Current config name
  cleaningCost: "15.00",           // Fixed costs
  productsPerDay: "100",
  ingredients: {                    // Ingredient prices
    coffee_beans: "25.00",
    milk: "1.50",
    // ...
  },
  drinks: [                         // Array of all drinks
    {
      name: "Cappuccino",
      vendingPrice: "3.50",
      ingredients: [
        { name: "coffee_beans", amount: "7.0" },
        { name: "milk", amount: "150.0" }
      ],
      teaBags: [],
      customItems: []
    },
    // ... more drinks
  ]
}
```

### Key Functions:

#### `saveFormState()`
- Collects all form data
- Serializes to JSON
- Stores in `localStorage.coffeeCalculatorFormState`
- Called automatically on input changes (debounced)

#### `restoreFormState()`
- Retrieves data from localStorage
- Parses JSON
- Populates all form fields
- Recreates drink cards with all details
- Returns true if restore successful, false if no data

#### `clearFormState()`
- Removes data from localStorage
- Called when loading a config or creating new config

#### `setupAutoSave()`
- Attaches event listeners to all inputs
- Uses MutationObserver for dynamic elements
- Debounces saves to avoid performance issues

### Debouncing Strategy:
- **500ms delay** after last input change before saving
- Prevents excessive writes to localStorage
- Ensures smooth typing/editing experience
- Still saves quickly enough to feel instant

### Edge Cases Handled:

1. **Multiple tabs**: Each tab has its own localStorage (per domain)
2. **Parse errors**: Try-catch prevents crashes if data corrupted
3. **Missing elements**: Checks for element existence before accessing
4. **Dynamic content**: MutationObserver captures changes in drinks container
5. **Empty states**: Gracefully handles empty drinks arrays

## Browser Compatibility

- **Works in**: Chrome, Firefox, Edge, Safari (all modern browsers)
- **Requires**: localStorage support (available since IE8+)
- **Storage limit**: ~5-10MB (more than enough for form data)

## Testing Checklist

- [x] Form data persists after page refresh
- [x] Form data persists after browser close/reopen
- [x] Data clears when loading a different configuration
- [x] Data clears when creating a new configuration
- [x] Data saves automatically while typing (with debounce)
- [x] All field types persist (text, number, select, dynamic)
- [x] Vending prices persist correctly
- [x] Tea bags persist correctly
- [x] Custom items persist correctly
- [x] Multiple drinks persist correctly
- [x] Config ID/name persists correctly
- [x] No performance issues with auto-save

## Files Modified

### `static/app.js`

**New Functions Added:**
- `saveFormState()` - Collects and saves form data to localStorage
- `restoreFormState()` - Retrieves and populates form from localStorage
- `clearFormState()` - Removes data from localStorage
- `setupAutoSave()` - Sets up auto-save event listeners

**Modified Functions:**
- `DOMContentLoaded` event handler - Now attempts to restore state on load
- `loadConfiguration()` - Clears localStorage before loading config
- `saveConfiguration()` - Saves to localStorage after successful save
- `newConfiguration()` - Clears localStorage when creating new config

**Lines Changed:** ~300 lines added/modified

## Performance Impact

- **Minimal**: Debounced saves prevent excessive writes
- **Fast**: localStorage is synchronous and very quick
- **No network**: All operations are local to the browser
- **No server impact**: No additional API calls

## Privacy & Security

- **Local only**: Data stored only in user's browser
- **No transmission**: Never sent to server except when explicitly saving config
- **Per-domain**: Other websites cannot access this data
- **User-controlled**: User can clear via browser settings

## Future Enhancements

Potential improvements:

1. **Version checking**: Detect if localStorage structure changed, migrate data
2. **Compression**: Compress data before storing (for very large configs)
3. **Multiple slots**: Allow saving multiple "drafts" in localStorage
4. **Conflict detection**: Warn if localStorage data conflicts with loaded config
5. **Export/Import**: Allow exporting localStorage data as JSON file
6. **Sync indicator**: Show visual feedback when auto-save happens

## Troubleshooting

### Problem: Data not persisting
**Solution:**
- Check browser's localStorage is enabled
- Check browser is not in private/incognito mode
- Try clearing localStorage and starting fresh
- Check browser console for errors

### Problem: Data persists when switching configs
**Solution:**
- This shouldn't happen - file a bug report
- Manually clear localStorage: `localStorage.removeItem('coffeeCalculatorFormState')`

### Problem: Old data loading incorrectly
**Solution:**
- Clear localStorage: `localStorage.clear()`
- Refresh page
- Data structure may have changed in update

## Developer Notes

### Debugging:
```javascript
// View current saved state
JSON.parse(localStorage.getItem('coffeeCalculatorFormState'))

// Manually save current form
saveFormState()

// Clear saved state
clearFormState()

// Check if data exists
localStorage.getItem('coffeeCalculatorFormState') !== null
```

### Testing localStorage:
```javascript
// Test save
const testData = { test: 'data' };
localStorage.setItem('test', JSON.stringify(testData));

// Test retrieve
const retrieved = JSON.parse(localStorage.getItem('test'));
console.log(retrieved);

// Test clear
localStorage.removeItem('test');
```
