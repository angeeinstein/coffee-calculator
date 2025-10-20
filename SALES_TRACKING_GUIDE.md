# Sales Tracking & Cash Register Management Guide

## Overview

The Coffee Calculator now includes comprehensive sales tracking and cash register management features. This allows you to:
- Track sales by recording machine counter readings
- Monitor cash register balance (expected vs actual)
- Record cash withdrawals and deposits
- View detailed sales statistics and reports
- Export sales data in PDF reports

## Features

### 1. Counter Reading System

Track your coffee machine's counter values to automatically calculate sales.

**How it works:**
1. Define your drinks in the "Define Your Drinks" section
2. Navigate to the "Sales Tracking & Cash Register" section
3. Click the "Counter Reading" tab
4. Enter current counter values for each drink from your machine
5. Enter the actual cash currently in your register
6. Add optional notes (e.g., "End of day reading")
7. Click "Submit Reading"

**What happens:**
- The system compares your current reading with the previous one
- Calculates how many of each drink were sold
- Calculates expected revenue based on your drink costs
- Stores the data for statistics and reporting

### 2. Cash Register Management

Keep track of your cash register and identify discrepancies.

**Cash Balance Display:**
- **Expected Cash**: Calculated based on previous cash + sales + deposits - withdrawals
- **Actual Cash**: What you entered in your last counter reading
- **Difference**: Shows if there's a discrepancy
  - Green: Difference < €5 (OK)
  - Orange: Difference €5-10 (Warning)
  - Red: Difference > €10 (Check Required)

**Recording Cash Events:**

**Withdrawals** (money taken out):
- Buying supplies (milk, coffee beans, etc.)
- Petty cash
- Bank deposits
- Other expenses

**Deposits** (money added):
- Adding change
- Returning borrowed money
- Corrections

**Steps:**
1. Navigate to "Cash Register" tab
2. Select event type (Withdrawal or Deposit)
3. Enter amount
4. Add description (e.g., "Bought 5L milk at supermarket")
5. Click "Record Event"

The system automatically adjusts expected cash calculations to account for these events.

### 3. Sales Statistics

View comprehensive analytics about your business performance.

**Available Metrics:**
- Total revenue (for selected period)
- Total items sold
- Number of counter readings recorded
- Sales by product (quantity, average price, revenue)
- Daily sales trends

**Time Periods:**
- Last 7 days
- Last 30 days (default)
- Last 90 days
- Last year

**To view statistics:**
1. Navigate to "Statistics" tab
2. Select desired time period
3. Review summary cards and product breakdown table

### 4. PDF Reports with Sales Data

PDF reports now automatically include:
- Sales statistics for the last 30 days
- Total revenue and items sold
- Sales breakdown by product
- Cash register reconciliation status
- Difference alerts if discrepancies exist

This gives you a complete snapshot of both your cost structure and actual sales performance.

## Workflow Example

### Daily Routine

**Morning:**
1. Record opening counter reading and cash amount

**During Day:**
- If you buy supplies, record a withdrawal event
  - Example: "Withdrawal, €25.00, Bought milk at supermarket"

**Evening:**
1. Record closing counter reading
2. Count cash in register
3. Enter values in system
4. Check if expected vs actual matches
5. If there's a large discrepancy, review your entries

### Weekly Review

1. Go to Statistics tab
2. Select "Last 7 days"
3. Review which products sell best
4. Calculate actual profit margins
5. Generate PDF report for your records

### Monthly Analysis

1. Go to Statistics tab
2. Select "Last 30 days"
3. Compare revenue with ingredient costs
4. Identify best-selling products
5. Plan menu adjustments
6. Download comprehensive PDF report

## Multi-User Support

Each user has their own:
- Counter readings
- Cash register events
- Sales records
- Statistics

**Important Notes:**
- Sales tracking is per-user, not per configuration
- Sharing a configuration does NOT share sales data
- Each user tracks their own machine's sales independently

This is useful for:
- Multiple locations with different operators
- Separate tracking for different machines
- Testing vs production environments

## Tips for Accurate Tracking

1. **Regular Readings**: Take counter readings at consistent times (daily is recommended)

2. **Record All Cash Events**: Always record when you take money out or add money

3. **Accurate Drink Prices**: Keep your drink costs up-to-date for accurate revenue calculations

4. **Note Taking**: Use the notes field to record unusual events
   - "Gave free drinks to charity event"
   - "Machine was down for 2 hours"
   - "New price list started today"

5. **Weekly Verification**: Check statistics weekly to catch any data entry errors early

6. **Cash Discrepancies**: Small differences (< €5) are normal due to:
   - Rounding
   - Free drinks given
   - Price adjustments
   - Data entry timing

   Large differences (> €10) should be investigated:
   - Check for missing cash event records
   - Verify counter readings were entered correctly
   - Review if any sales were made without the counter incrementing

## Troubleshooting

### "No readings yet" message
- You need to submit at least one counter reading first
- Make sure you've defined drinks in the main section

### Expected cash is wrong
- Check that all withdrawals/deposits are recorded
- Verify previous counter reading was accurate
- Make sure drink prices in your configuration are correct

### Sales statistics show zero
- You need at least TWO counter readings to calculate sales
- The second reading must have higher counter values than the first
- Make sure drink prices were available when you submitted readings

### Cash difference is large
1. Review recent cash events - did you forget to record something?
2. Check if counter values were entered correctly
3. Verify drink prices haven't changed without updating your configuration
4. Look for any manual cash adjustments that weren't recorded

## Database Tables

For technical users, the system uses three new tables:

**counter_readings**: Stores snapshots of machine counters and cash
- Counter values for each drink
- Cash in register
- Timestamp and notes

**cash_register_events**: Records all cash movements
- Withdrawals and deposits
- Amount and description
- Timestamp

**sales_records**: Calculated sales between readings
- Product name and quantity sold
- Unit price and total revenue
- Links to start/end counter readings

All tables include `user_id` for multi-user isolation.

## Privacy & Data

- All sales data is private to your user account
- Other users cannot see your sales statistics
- Data is stored in the local SQLite database
- Regular backups of the database are recommended

## Server Deployment

When updating your server with this new feature:

```bash
cd /path/to/coffee-calculator
git pull
sudo ./install.sh
# Select option 2 (Update to latest version)
```

The database will automatically create the new tables on first run.
Existing data (users, configurations, tea bags) remains untouched.

## Support

The sales tracking system is designed to work seamlessly with existing features:
- ✅ User authentication
- ✅ Configuration sharing
- ✅ Tea bag management
- ✅ PDF generation
- ✅ Multi-user isolation

Everything continues to work as before, with powerful sales analytics added on top.
