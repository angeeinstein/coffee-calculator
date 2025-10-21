# Sales Trend Chart Feature

## Overview

Added an interactive line chart in the Statistics tab that visualizes the development of:
- **Products Sold** (cumulative counter values)
- **Expected Revenue** (cumulative sales revenue)
- **Actual Cash** (cash in register at each reading)

This allows you to track your business performance over time and spot trends or discrepancies.

## Features

### Multi-Line Chart

**Three data series:**
1. **Products Sold** (Blue line, left Y-axis)
   - Shows cumulative total of all products at each reading
   - Helps track sales volume over time

2. **Expected Revenue** (Green line, right Y-axis)
   - Shows cumulative revenue from all sales
   - Based on quantity sold × vending price
   - Excludes withdrawals/deposits

3. **Actual Cash** (Orange line, right Y-axis)
   - Shows physical cash in register at each reading
   - Compare with expected revenue to spot discrepancies

### Chart Features

✅ **Interactive**: Hover over points to see exact values  
✅ **Dual Y-Axes**: Products count on left, money (€) on right  
✅ **Responsive**: Adapts to screen size  
✅ **Date Labels**: X-axis shows reading dates  
✅ **Period Filter**: Switch between 7/30/90/365 days  
✅ **Auto-Updates**: Refreshes when you change period  

## Implementation Details

### Backend (`app.py`)

Added new endpoint: `GET /api/sales-trend-chart`

```python
@app.route('/api/sales-trend-chart', methods=['GET'])
@login_required
def get_sales_trend_chart():
    """Get sales trend data for chart visualization"""
    # Parameters: days, config_id (optional)
    
    # For each counter reading:
    # - reading_date
    # - products_sold (sum of counter values)
    # - revenue (sales from this reading)
    # - cumulative_revenue (total up to this point)
    # - actual_cash (cash in register)
```

**Query Logic:**
1. Get all counter readings in the period
2. For each reading:
   - Sum all counter values = total products
   - Query sales_records for revenue
   - Calculate cumulative revenue
   - Include cash_in_register

**Response Structure:**
```json
{
  "success": true,
  "chart_data": [
    {
      "date": "2025-10-20T18:37:41",
      "products_sold": 67,
      "revenue": 38.20,
      "cumulative_revenue": 38.20,
      "actual_cash": 23.35
    },
    {
      "date": "2025-10-21T09:15:00",
      "products_sold": 89,
      "revenue": 52.50,
      "cumulative_revenue": 90.70,
      "actual_cash": 75.85
    }
  ]
}
```

### Frontend (`templates/index.html`)

Added Chart.js library:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
```

Added canvas element in Statistics tab:
```html
<h3>📈 Sales Trend</h3>
<div style="background: white; padding: 20px; border-radius: 12px;">
    <canvas id="sales-trend-chart" style="max-height: 400px;"></canvas>
</div>
```

### JavaScript (`static/app.js`)

#### Chart Loading

```javascript
async function loadSalesTrendChart(days) {
    // Fetch data from /api/sales-trend-chart
    // Call renderSalesTrendChart(data)
}
```

Called automatically when:
- Statistics tab is loaded
- Period filter is changed
- Configuration is switched

#### Chart Rendering

```javascript
function renderSalesTrendChart(chartData) {
    // Destroy existing chart if present
    if (salesTrendChart) {
        salesTrendChart.destroy();
    }
    
    // Prepare data arrays
    const labels = chartData.map(item => formatDate(item.date));
    const productsData = chartData.map(item => item.products_sold);
    const revenueData = chartData.map(item => item.cumulative_revenue);
    const cashData = chartData.map(item => item.actual_cash);
    
    // Create Chart.js instance with dual Y-axes
    salesTrendChart = new Chart(ctx, {
        type: 'line',
        data: { ... },
        options: { ... }
    });
}
```

**Chart Configuration:**
- Type: Line chart with area fill
- Tension: 0.4 (smooth curves)
- Two Y-axes: Products (left) and Money (right)
- Interaction mode: Index (shows all values at once)

## Usage Examples

### Example 1: Tracking Weekly Performance

**Scenario:** You want to see how your coffee shop performed this week

1. Go to **Statistics** tab
2. Select **"Last 7 days"** from period dropdown
3. View the chart:
   - Blue line shows total products sold increasing
   - Green line shows expected revenue growing
   - Orange line shows actual cash (should track green line)
   - Gap between green and orange = discrepancies

### Example 2: Spotting Cash Discrepancies

**Readings:**
- Day 1: 50 products sold, €125 expected, €125 actual ✅ Perfect
- Day 2: 72 products sold, €180 expected, €165 actual ⚠️ Missing €15
- Day 3: 95 products sold, €237 expected, €220 actual ⚠️ Missing €17

**Chart shows:**
- Blue line: Steady upward trend (good sales)
- Green line: Growing revenue (expected)
- Orange line: Below green line (cash shortage)

**Action:** Investigate missing cash (employee error? theft? wrong prices?)

### Example 3: Seasonal Trends

**Monthly view:**
- Week 1: High sales (blue line steep)
- Week 2: Lower sales (blue line flatter)
- Week 3: Recovery (blue line steeper again)
- Week 4: Peak sales (steepest climb)

**Insight:** Identify peak days/weeks, plan inventory accordingly

## Visual Design

### Colors
- **Blue (#667eea)**: Products Sold - Primary brand color
- **Green (#27ae60)**: Expected Revenue - Money/profit color
- **Orange (#f39c12)**: Actual Cash - Warning/attention color

### Layout
```
┌─────────────────────────────────────────┐
│  📈 Sales Trend                         │
│  ┌─────────────────────────────────┐   │
│  │                          120│    │   │
│  │                    /        │    │   │
│  │              /    /         │100 │   │
│  │        /    /    /          │    │   │
│  │  /    /    /    /           │ 80 │   │
│  │ /────/────/────/            │    │   │
│  │                         0│  │ 60 │   │
│  └─────────────────────────────────┘   │
│   Oct 18  Oct 19  Oct 20  Oct 21       │
│                                         │
│   ─ Products Sold  ─ Revenue  ─ Cash   │
└─────────────────────────────────────────┘
```

## Benefits

✅ **Visual Tracking**: See trends at a glance  
✅ **Quick Insights**: Identify patterns immediately  
✅ **Discrepancy Detection**: Spot cash shortages visually  
✅ **Performance Metrics**: Track growth over time  
✅ **Data-Driven Decisions**: Base inventory/staffing on trends  
✅ **Professional Reports**: Screenshot for presentations  

## Technical Considerations

### Performance
- Queries optimized with indexes on reading_date
- Chart reuses canvas (no memory leaks)
- Destroys old chart before creating new one
- Efficient data aggregation in SQL

### Browser Compatibility
- Chart.js 4.4.0 supports all modern browsers
- Falls back gracefully on older browsers
- Responsive design works on mobile

### Data Accuracy
- Uses actual database timestamps
- Cumulative revenue ensures accuracy
- Excludes withdrawals/deposits (pure sales tracking)
- Products sold = sum of counter values at each reading

## Future Enhancements

Possible improvements:

1. **Toggle Lines**: Click legend to show/hide specific lines
2. **Zoom/Pan**: Interact with chart to focus on date ranges
3. **Annotations**: Mark special events (holidays, promotions)
4. **Comparison View**: Compare this period to last period
5. **Export Chart**: Download as PNG/PDF
6. **Profit Line**: Add line showing profit (revenue - costs)
7. **Forecasting**: Predict future sales based on trend
8. **Daily Breakdown**: Toggle between cumulative and daily values
9. **Product-Specific**: Filter chart by specific products
10. **Multiple Configs**: Compare different configurations side-by-side

## Troubleshooting

### Chart Not Showing
- Check browser console for errors
- Verify Chart.js loaded (check network tab)
- Ensure you have counter readings in the selected period

### Lines Flat/Weird
- Check that readings have different dates
- Verify product prices are set (needed for revenue)
- Ensure counter values are increasing

### Data Doesn't Match
- Revenue uses vending prices (not cost prices)
- Cumulative values keep growing (by design)
- Actual cash includes all money, not just from sales

## Testing Checklist

- [x] Chart renders with multiple readings
- [x] Chart shows correct dates on X-axis
- [x] Products line uses left Y-axis
- [x] Revenue and cash lines use right Y-axis
- [x] Hover shows exact values with € symbol
- [x] Period filter updates chart
- [x] Configuration switch updates chart
- [x] Chart destroys/recreates properly (no duplicates)
- [x] Responsive on mobile/tablet
- [x] Works with 1 reading (doesn't crash)
- [x] Works with 0 readings (shows empty chart)

## Files Modified

1. **app.py**: Added `/api/sales-trend-chart` endpoint
2. **templates/index.html**: Added Chart.js library + canvas element
3. **static/app.js**: Added `loadSalesTrendChart()` and `renderSalesTrendChart()` functions

## Migration Notes

**No database changes** - Uses existing tables  
**Backward compatible** - Doesn't affect existing features  
**Library added** - Chart.js 4.4.0 from CDN (no install needed)
