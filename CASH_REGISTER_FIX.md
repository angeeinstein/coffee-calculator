# Cash Register Reconciliation Fix + Delete Events

## Summary

Fixed the cash register expected cash calculation to use proper accounting formula and added ability to delete withdrawal/deposit events.

## Problem

**Before:** Expected cash was only based on the latest reading, not accounting for cumulative sales and cash movements.

**User's scenario:**
1. Starting cash: €23.35
2. Sold products worth hundreds of euros
3. Withdrew €20.00 for milk
4. Expected showed: €4.15 (wrong!)
5. Should show: €23.35 + (all sales revenue) - €20.00

## Solution

### 1. Corrected Expected Cash Formula

**New Formula:**
```
Expected Cash = Starting Cash + Total Sales Revenue - Withdrawals + Deposits
```

**Where:**
- **Starting Cash**: The very first counter reading (baseline)
- **Total Sales Revenue**: Sum of all (quantity sold × vending price) from ALL counter readings
- **Withdrawals**: Sum of all money taken out
- **Deposits**: Sum of all money added

### 2. Implementation Details

#### Backend Changes (`app.py`):

```python
# Get FIRST reading as starting cash (not latest)
cursor.execute('''
    SELECT cash_in_register
    FROM counter_readings
    WHERE config_id = ?
    ORDER BY reading_date ASC  # First reading
    LIMIT 1
''', (config_id,))

starting_cash = first_reading[0] if first_reading else 0

# Get ALL sales (not just since last reading)
cursor.execute('''
    SELECT COALESCE(SUM(total_revenue), 0)
    FROM sales_records
    WHERE end_reading_id <= ?  # All up to current
''', (reading_id,))

total_sales = cursor.fetchone()[0]

# Get ALL withdrawals and deposits (not just recent)
cursor.execute('''
    SELECT 
        COALESCE(SUM(CASE WHEN event_type = 'withdrawal' THEN amount ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN event_type = 'deposit' THEN amount ELSE 0 END), 0)
    FROM cash_register_events
    WHERE config_id = ? AND event_date <= ?
''', (config_id, last_reading_date))

# Calculate expected
expected_cash = starting_cash + total_sales - withdrawals + deposits
```

### 3. Delete Cash Events Feature

Added ability to delete withdrawal/deposit events including their auto-created readings.

#### New Endpoint (`app.py`):

```python
@app.route('/api/cash-register/events/<int:event_id>', methods=['DELETE'])
@login_required
def delete_cash_event(event_id):
    # Verify permissions
    # Find auto-created reading with matching note
    # Delete both the reading and the event
    # Recalculate balances
```

**Features:**
- Permission checks (owner or shared with edit access)
- Finds and deletes the auto-created counter reading
- Deletes the cash event itself
- Refreshes all displays

#### Frontend Changes (`app.js`):

Added delete button to each cash event:

```javascript
function displayCashEvents(events) {
    // ... each event now has a delete button
    <button onclick="deleteCashEvent(${event.id})">🗑️ Delete</button>
}

async function deleteCashEvent(eventId) {
    if (!confirm('Delete this cash event?')) return;
    
    await fetch(`/api/cash-register/events/${eventId}`, {
        method: 'DELETE'
    });
    
    // Reload all data
    loadCashEvents();
    loadCashRegisterBalance();
    loadRecentReadings();
}
```

## Example Calculation

**Scenario:**
1. **Starting Cash**: €23.35 (first reading)
2. **Products Sold**:
   - 25 Cafe Crema @ €2.50 = €62.50
   - 11 Cappuccino @ €3.00 = €33.00
   - 8 Doppler Espresso @ €4.50 = €36.00
   - ... more products ...
   - **Total Sales**: €450.00
3. **Withdrawals**: €20.00 (milk purchase)
4. **Deposits**: €0.00

**Expected Cash Calculation:**
```
Expected = €23.35 + €450.00 - €20.00 + €0.00 = €453.35
```

**If Actual Cash** (from latest reading) = €453.35
**Difference** = €0.00 ✅ (Perfect reconciliation!)

**If Actual Cash** = €450.00
**Difference** = -€3.35 ⚠️ (Missing €3.35)

## API Response Structure

```json
{
  "success": true,
  "starting_cash": 23.35,
  "total_sales": 450.00,
  "withdrawals": 20.00,
  "deposits": 0.00,
  "expected_cash": 453.35,
  "actual_cash": 453.35,
  "difference": 0.00,
  "last_reading_date": "2025-10-20T18:37:41"
}
```

## User Workflow

### Normal Operation:

1. **Start of Day**: Submit counter reading with starting cash (e.g., €23.35)
2. **Throughout Day**: 
   - Sell products (counters increment)
   - Record withdrawals for supplies
   - Record deposits if adding change
3. **End of Day**: Submit new counter reading
   - System calculates sales from counter differences
   - Expected cash shows what SHOULD be in register
   - Actual cash is what you count
   - Difference shows discrepancies

### Deleting Events:

1. **Accidental Withdrawal**: Recorded €20 instead of €2
2. **Click Delete** button on the event
3. **Confirms**: "Delete this cash event? This will also remove the associated auto-created reading."
4. **Result**: 
   - Event removed from history
   - Auto-created reading deleted
   - Expected cash recalculated
   - Balance updated

## Files Modified

### Backend
- **`app.py`** (Lines 1448-1520)
  - `get_cash_register_balance()` - Changed to cumulative calculation
  - Added `delete_cash_event()` - New DELETE endpoint

### Frontend  
- **`static/app.js`** (Lines 1931-1985)
  - `displayCashEvents()` - Added delete buttons
  - `deleteCashEvent()` - New function to handle deletions

## Testing Checklist

- [x] Expected cash uses starting cash as baseline
- [x] All sales revenue included (not just recent)
- [x] All withdrawals/deposits included
- [x] Formula: Starting + Sales - Withdrawals + Deposits
- [x] Delete button appears on each event
- [x] Delete removes both event and auto-reading
- [x] Balance updates after deletion
- [x] Permission checks work for shared configs
- [x] Difference calculation is accurate

## Edge Cases Handled

1. **No first reading**: Starting cash = 0
2. **No sales**: Total sales = 0
3. **No events**: Withdrawals/deposits = 0
4. **Auto-created readings**: Identified by note pattern, deleted with event
5. **Permission denied**: Users can't delete events in configs they don't own/edit
6. **Missing event**: Returns 404 error
7. **Database errors**: Rolled back via try-catch

## Performance Impact

- **Minimal**: Query sums are indexed operations
- **Scales well**: Even with thousands of events/readings
- **No N+1 queries**: Single query per data type

## Future Enhancements

Potential improvements:

1. **Bulk delete**: Delete multiple events at once
2. **Edit events**: Change amount/description without deleting
3. **Undo delete**: Restore deleted events within timeframe
4. **Event categories**: Tag events (supplies, maintenance, etc.)
5. **Daily summaries**: Aggregate view by day/week/month
6. **Cash flow report**: Visualization of money in/out over time
7. **Variance alerts**: Notify if difference exceeds threshold

## Troubleshooting

### Issue: Expected cash seems too high
**Cause**: Includes all sales from the beginning
**Solution**: This is correct - it's cumulative accounting

### Issue: Can't delete event
**Cause**: Insufficient permissions or shared config without edit access
**Solution**: Ask config owner to grant edit permissions or have them delete

### Issue: Difference not zero after matching
**Cause**: Auto-created readings or rounding
**Solution**: Check Recent Readings for auto-updates, verify vending prices set

## Migration Notes

**No database changes required** - Uses existing tables and columns.

**Backward compatible** - Existing data works with new formula.

**Auto-readings respected** - System identifies and handles them correctly.
