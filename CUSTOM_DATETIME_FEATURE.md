# Custom Date/Time for Counter Readings

## Feature Overview

Added the ability to specify a custom date and time when submitting counter readings. By default, it uses the current date/time, but you can change it to any date/time you need.

## Use Cases

1. **Backdating Readings**: Enter readings you forgot to record yesterday
2. **Scheduled Readings**: Set future timestamps for planned readings
3. **Exact Timestamps**: Record the precise moment you took the reading
4. **Historical Data**: Import old readings with their original timestamps
5. **Multiple Daily Readings**: Record morning, afternoon, and evening readings with exact times

## How It Works

### User Interface

**Location**: Counter Reading tab, above the "Cash in Register" field

**Field**: 📅 Reading Date & Time
- Type: `datetime-local` input
- Format: YYYY-MM-DD HH:MM (e.g., "2025-10-20 18:30")
- Default: Current date and time
- Can be changed before submitting

### Behavior

1. **On Page Load**: Automatically set to current date/time
2. **Before Submission**: Can be edited to any past or future date/time
3. **After Submission**: Resets to current date/time for next reading
4. **If Left Empty**: Uses current date/time automatically (fallback)

## Implementation Details

### Frontend Changes (`templates/index.html`)

Added datetime-local input field:

```html
<div class="input-group" style="margin-top: 20px;">
    <label for="reading-datetime">📅 Reading Date & Time</label>
    <input type="datetime-local" id="reading-datetime" 
           style="padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px;">
</div>
```

### JavaScript Changes (`static/app.js`)

#### 1. Set Current Date/Time Function

```javascript
function setCurrentDateTime() {
    const datetimeInput = document.getElementById('reading-datetime');
    if (datetimeInput) {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        
        datetimeInput.value = `${year}-${month}-${day}T${hours}:${minutes}`;
    }
}
```

#### 2. Initialize on Page Load

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // ... other initialization ...
    if (salesTrackingSection && !salesTrackingSection.classList.contains('hidden')) {
        setCurrentDateTime();  // Set current time
        // ... load data ...
    }
});
```

#### 3. Send Custom Date/Time on Submit

```javascript
async function submitCounterReading() {
    // ... collect form data ...
    
    // Get the reading date/time (use current if not set)
    const readingDatetimeInput = document.getElementById('reading-datetime');
    const readingDatetime = readingDatetimeInput.value || new Date().toISOString();
    
    const response = await fetch('/api/counter-readings', {
        method: 'POST',
        body: JSON.stringify({
            counter_data: counterData,
            cash_in_register: cashInRegister,
            notes: notes,
            product_prices: productPrices,
            config_id: currentConfigId,
            reading_date: readingDatetime  // Include custom date
        })
    });
}
```

#### 4. Reset After Submission

```javascript
// After successful submission
setCurrentDateTime();  // Reset to current time for next reading
```

### Backend Changes (`app.py`)

Modified `submit_counter_reading()` endpoint:

```python
@app.route('/api/counter-readings', methods=['POST'])
@login_required
def submit_counter_reading():
    try:
        data = request.get_json()
        counter_data = data.get('counter_data', {})
        cash_in_register = float(data.get('cash_in_register', 0))
        notes = data.get('notes', '')
        product_prices = data.get('product_prices', {})
        config_id = data.get('config_id')
        reading_date = data.get('reading_date')  # NEW: Custom date/time
        
        # If no custom date provided, use current time
        if not reading_date:
            reading_date = datetime.now().isoformat()
        
        # ... verify permissions ...
        
        # Insert with custom date/time
        cursor.execute('''
            INSERT INTO counter_readings 
            (user_id, config_id, counter_data, cash_in_register, notes, reading_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_user.id, config_id, json.dumps(counter_data), 
              cash_in_register, notes, reading_date))
        
        # ... calculate sales ...
```

## User Workflow Examples

### Example 1: Normal Daily Reading (Default Behavior)

1. Open Counter Reading tab
2. **Date/time field shows**: "2025-10-21 14:30" (current time)
3. Enter counter values
4. Click "Submit Reading"
5. **Result**: Reading saved with timestamp "2025-10-21 14:30"

### Example 2: Backdating Yesterday's Reading

1. Open Counter Reading tab
2. **Date/time field shows**: "2025-10-21 14:30" (current)
3. **Change to**: "2025-10-20 18:00" (yesterday evening)
4. Enter counter values from yesterday
5. Click "Submit Reading"
6. **Result**: Reading saved with timestamp "2025-10-20 18:00"

### Example 3: Multiple Readings Same Day

**Morning Reading:**
1. Set date/time: "2025-10-21 08:00"
2. Enter morning counter values
3. Submit

**Afternoon Reading:**
1. Date/time auto-resets to current: "2025-10-21 14:30"
2. Enter afternoon counter values
3. Submit

**Evening Reading:**
1. Change date/time: "2025-10-21 22:00"
2. Enter evening counter values
3. Submit

**Result**: Three readings with different times showing sales trends throughout the day

## Database Schema

No changes required! The `counter_readings` table already has a `reading_date` column with default `CURRENT_TIMESTAMP`.

```sql
CREATE TABLE counter_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    config_id INTEGER,
    reading_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Accepts custom values
    counter_data TEXT NOT NULL,
    cash_in_register REAL NOT NULL DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (config_id) REFERENCES configurations(id)
)
```

## Edge Cases Handled

1. **Empty Input**: Falls back to `datetime.now().isoformat()`
2. **Invalid Format**: HTML5 datetime-local ensures valid format before submission
3. **Future Dates**: Allowed (useful for scheduled readings)
4. **Very Old Dates**: Allowed (useful for importing historical data)
5. **Time Zones**: Stores as-is (user's local time)

## Benefits

✅ **Flexibility**: Record readings at any time  
✅ **Accuracy**: Precise timestamps for better tracking  
✅ **Data Recovery**: Can backdate forgotten readings  
✅ **Historical Import**: Import old data with original dates  
✅ **User-Friendly**: Defaults to current time (no extra work for normal use)  
✅ **No Breaking Changes**: Existing functionality preserved  

## Testing Checklist

- [x] Default shows current date/time on page load
- [x] Can change date/time before submission
- [x] Custom date/time is saved to database
- [x] Date/time resets to current after submission
- [x] Empty field uses current time (fallback)
- [x] Can backdate readings
- [x] Can set future readings
- [x] Works with sales calculations (uses reading_date for comparisons)
- [x] Works with cash register balance (uses reading_date for filtering)
- [x] Recent readings display shows custom timestamps

## Future Enhancements

Potential improvements:

1. **Time Zone Selector**: Specify readings from different time zones
2. **Quick Presets**: Buttons for "Yesterday", "This Morning", "Last Night"
3. **Date Validation**: Warn if date is very old or too far in future
4. **Bulk Import**: Upload CSV with historical readings and timestamps
5. **Calendar View**: Visual calendar showing all reading dates
6. **Reading Reminders**: Notify user if they haven't recorded today
7. **Auto-Populate**: Use last reading's time + 24 hours as default

## Migration Notes

**No database migration required** - Uses existing `reading_date` column.

**Backward compatible** - Existing readings keep their timestamps unchanged.

**API compatible** - `reading_date` is optional, falls back to current time.
