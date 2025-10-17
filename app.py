from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from datetime import datetime
import sqlite3
import json
import os

app = Flask(__name__)
CORS(app)

# Database configuration
DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'coffee_calculator.db')

# Ensure data directory exists
os.makedirs(DATABASE_DIR, exist_ok=True)

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            cleaning_cost REAL DEFAULT 0,
            products_per_day INTEGER DEFAULT 1,
            ingredients TEXT NOT NULL,
            drinks TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if we need to add the new columns to existing tables
    cursor.execute("PRAGMA table_info(configurations)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'cleaning_cost' not in columns:
        cursor.execute('ALTER TABLE configurations ADD COLUMN cleaning_cost REAL DEFAULT 0')
    
    if 'products_per_day' not in columns:
        cursor.execute('ALTER TABLE configurations ADD COLUMN products_per_day INTEGER DEFAULT 1')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        ingredients = data.get('ingredients', {})
        drinks = data.get('drinks', [])
        cleaning_cost = data.get('cleaning_cost', 0)
        products_per_day = data.get('products_per_day', 1)
        
        # Calculate cleaning cost per product
        cleaning_cost_per_product = cleaning_cost / products_per_day if products_per_day > 0 else 0
        
        # Calculate cost for each drink
        results = []
        for drink in drinks:
            drink_cost = 0
            breakdown = []
            
            for ingredient_name, amount in drink.get('ingredients', {}).items():
                if ingredient_name in ingredients:
                    ingredient_cost = ingredients[ingredient_name]
                    cost = ingredient_cost * amount
                    drink_cost += cost
                    breakdown.append({
                        'ingredient': ingredient_name,
                        'amount': amount,
                        'unit_cost': ingredient_cost,
                        'total_cost': round(cost, 2)
                    })
            
            # Add cleaning cost to total
            total_cost = drink_cost + cleaning_cost_per_product
            
            results.append({
                'name': drink.get('name'),
                'total_cost': round(total_cost, 2),
                'cleaning_cost_per_product': round(cleaning_cost_per_product, 2),
                'total_cleaning_cost': round(cleaning_cost, 2),
                'breakdown': breakdown
            })
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.json
        cleaning_cost = data.get('cleaning_cost', 0)
        products_per_day = data.get('products_per_day', 1)
        ingredients = data.get('ingredients', {})
        drinks = data.get('drinks', [])
        results = data.get('results', [])
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        title = Paragraph("Coffee Cost Calculator Report", title_style)
        elements.append(title)
        
        # Date
        date_text = Paragraph(f"<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>", 
                             styles['Normal'])
        elements.append(date_text)
        elements.append(Spacer(1, 20))
        
        # Fixed Costs Section
        if cleaning_cost > 0:
            elements.append(Paragraph("Fixed Daily Costs", heading_style))
            
            fixed_cost_data = [
                ['Cost Type', 'Amount'],
                ['Daily Cleaning Cost', f"€{cleaning_cost:.2f}"],
                ['Expected Products per Day', str(int(products_per_day))],
                ['Cleaning Cost per Product', f"€{(cleaning_cost / products_per_day):.2f}"]
            ]
            
            fixed_cost_table = Table(fixed_cost_data, colWidths=[3*inch, 2*inch])
            fixed_cost_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            elements.append(fixed_cost_table)
            elements.append(Spacer(1, 30))
        
        # Ingredients Section
        elements.append(Paragraph("Ingredient Costs", heading_style))
        
        # Define liquid ingredients
        liquid_ingredients = ['milk', 'water', 'vanilla_syrup']
        
        ingredient_data = [['Ingredient', 'Cost per Unit']]
        for name, cost in ingredients.items():
            unit = 'L' if name in liquid_ingredients else 'kg'
            ingredient_data.append([name.replace('_', ' ').title(), f"€{cost:.2f}/{unit}"])
        
        ingredient_table = Table(ingredient_data, colWidths=[3*inch, 2*inch])
        ingredient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        elements.append(ingredient_table)
        elements.append(Spacer(1, 30))
        
        # Drinks Section
        elements.append(Paragraph("Drink Costs Breakdown", heading_style))
        
        for result in results:
            # Drink name
            drink_name = Paragraph(f"<b>{result['name']}</b> - Total Cost: €{result['total_cost']:.2f}", 
                                  styles['Heading3'])
            elements.append(drink_name)
            elements.append(Spacer(1, 6))
            
            # Breakdown table
            breakdown_data = [['Item', 'Amount', 'Unit Cost', 'Total']]
            
            ingredient_subtotal = 0
            for item in result['breakdown']:
                ingredient_name = item['ingredient']
                amount_in_base = item['amount']
                ingredient_subtotal += item['total_cost']
                
                # Convert to g/ml for display
                if ingredient_name in liquid_ingredients:
                    amount_display = f"{amount_in_base * 1000:.1f} ml"
                    unit_display = "L"
                else:
                    amount_display = f"{amount_in_base * 1000:.1f} g"
                    unit_display = "kg"
                
                breakdown_data.append([
                    ingredient_name.replace('_', ' ').title(),
                    amount_display,
                    f"€{item['unit_cost']:.2f}/{unit_display}",
                    f"€{item['total_cost']:.2f}"
                ])
            
            # Add cleaning cost row if present
            if result.get('cleaning_cost_per_product', 0) > 0:
                breakdown_data.append([
                    'Daily Cleaning Cost',
                    'Per product',
                    f"€{result.get('total_cleaning_cost', 0):.2f}/day",
                    f"€{result['cleaning_cost_per_product']:.2f}"
                ])
            
            breakdown_table = Table(breakdown_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            breakdown_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            elements.append(breakdown_table)
            elements.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'coffee_cost_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/configs', methods=['GET'])
def get_configs():
    """Get all saved configurations"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, created_at, updated_at 
            FROM configurations 
            ORDER BY updated_at DESC
        ''')
        
        configs = []
        for row in cursor.fetchall():
            configs.append({
                'id': row[0],
                'name': row[1],
                'created_at': row[2],
                'updated_at': row[3]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'configs': configs
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/configs/<int:config_id>', methods=['GET'])
def get_config(config_id):
    """Get a specific configuration by ID"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, cleaning_cost, products_per_day, ingredients, drinks, created_at, updated_at 
            FROM configurations 
            WHERE id = ?
        ''', (config_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify({
                'success': True,
                'config': {
                    'id': row[0],
                    'name': row[1],
                    'cleaning_cost': row[2] or 0,
                    'products_per_day': row[3] or 1,
                    'ingredients': json.loads(row[4]),
                    'drinks': json.loads(row[5]),
                    'created_at': row[6],
                    'updated_at': row[7]
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Configuration not found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/configs', methods=['POST'])
def save_config():
    """Save a new configuration or update existing one"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        cleaning_cost = data.get('cleaning_cost', 0)
        products_per_day = data.get('products_per_day', 1)
        ingredients = data.get('ingredients', {})
        drinks = data.get('drinks', [])
        config_id = data.get('id')
        
        if not name:
            return jsonify({
                'success': False,
                'error': 'Configuration name is required'
            }), 400
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        if config_id:
            # Update existing configuration
            cursor.execute('''
                UPDATE configurations 
                SET name = ?, cleaning_cost = ?, products_per_day = ?, ingredients = ?, drinks = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (name, cleaning_cost, products_per_day, json.dumps(ingredients), json.dumps(drinks), config_id))
            
            if cursor.rowcount == 0:
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Configuration not found'
                }), 404
            
            result_id = config_id
        else:
            # Insert new configuration
            try:
                cursor.execute('''
                    INSERT INTO configurations (name, cleaning_cost, products_per_day, ingredients, drinks)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, cleaning_cost, products_per_day, json.dumps(ingredients), json.dumps(drinks)))
                
                result_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'A configuration with this name already exists'
                }), 400
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'id': result_id,
            'message': 'Configuration saved successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/configs/<int:config_id>', methods=['DELETE'])
def delete_config(config_id):
    """Delete a configuration"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM configurations WHERE id = ?', (config_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Configuration not found'
            }), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Configuration deleted successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
