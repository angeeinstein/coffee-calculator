"""
Migration script to retroactively create sales records for first readings.
This treats the first reading's counter values as sales (assuming counters started at 0).
"""

import sqlite3
import json

DATABASE_PATH = 'coffee_calculator.db'

def fix_first_readings():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Find all first readings that don't have sales records yet
    cursor.execute('''
        SELECT cr.id, cr.user_id, cr.config_id, cr.counter_data
        FROM counter_readings cr
        WHERE NOT EXISTS (
            SELECT 1 FROM sales_records sr 
            WHERE sr.end_reading_id = cr.id
        )
        AND NOT EXISTS (
            SELECT 1 FROM counter_readings cr2 
            WHERE cr2.config_id = cr.config_id 
            AND cr2.id < cr.id
        )
    ''')
    
    first_readings = cursor.fetchall()
    
    print(f"Found {len(first_readings)} first readings without sales records")
    
    for reading_id, user_id, config_id, counter_data_json in first_readings:
        counter_data = json.loads(counter_data_json)
        
        # Get product prices from configuration
        if config_id:
            cursor.execute('SELECT config_data FROM configurations WHERE id = ?', (config_id,))
            config_row = cursor.fetchone()
            if config_row:
                config_data = json.loads(config_row[0])
                product_prices = config_data.get('product_prices', {})
            else:
                product_prices = {}
        else:
            product_prices = {}
        
        print(f"\nProcessing reading {reading_id} for user {user_id}, config {config_id}")
        print(f"Counter data: {counter_data}")
        print(f"Product prices: {product_prices}")
        
        sales_created = 0
        total_revenue = 0
        
        # Create sales records for each product in the first reading
        for product_name, count in counter_data.items():
            if count > 0:
                if product_name in product_prices:
                    unit_price = product_prices[product_name]
                    revenue = count * unit_price
                    
                    cursor.execute('''
                        INSERT INTO sales_records 
                        (user_id, config_id, start_reading_id, end_reading_id, product_name, quantity_sold, unit_price, total_revenue)
                        VALUES (?, ?, NULL, ?, ?, ?, ?, ?)
                    ''', (user_id, config_id, reading_id, product_name, count, unit_price, revenue))
                    
                    sales_created += 1
                    total_revenue += revenue
                    print(f"  - {product_name}: {count} × €{unit_price} = €{revenue}")
                else:
                    print(f"  - WARNING: No price for {product_name} ({count} units)")
        
        print(f"  Created {sales_created} sales records, total revenue: €{total_revenue:.2f}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Migration complete! Fixed {len(first_readings)} first readings.")

if __name__ == '__main__':
    fix_first_readings()
