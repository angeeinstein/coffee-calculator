from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
CORS(app, supports_credentials=True)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Disable caching for static files to prevent outdated JavaScript/CSS
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# Database configuration
DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'coffee_calculator.db')

# Ensure data directory exists
os.makedirs(DATABASE_DIR, exist_ok=True)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, email, name):
        self.id = id
        self.email = email
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, name FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Configurations table with user_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            cleaning_cost REAL DEFAULT 0,
            products_per_day INTEGER DEFAULT 1,
            ingredients TEXT NOT NULL,
            drinks TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, name)
        )
    ''')
    
    # Shared configurations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shared_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_id INTEGER NOT NULL,
            shared_with_user_id INTEGER NOT NULL,
            can_edit BOOLEAN DEFAULT 0,
            shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (config_id) REFERENCES configurations(id) ON DELETE CASCADE,
            FOREIGN KEY (shared_with_user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(config_id, shared_with_user_id)
        )
    ''')
    
    # Tea bags table (per-unit cost items)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tea_bags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            cost_per_unit REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, name)
        )
    ''')
    
    # Counter readings table - stores snapshots of machine counter values
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS counter_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            config_id INTEGER,
            reading_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            counter_data TEXT NOT NULL,
            cash_in_register REAL NOT NULL,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (config_id) REFERENCES configurations(id) ON DELETE SET NULL
        )
    ''')
    
    # Cash register events - withdrawals, deposits, adjustments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cash_register_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            config_id INTEGER,
            event_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (config_id) REFERENCES configurations(id) ON DELETE SET NULL
        )
    ''')
    
    # Sales records - calculated from counter differences
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            config_id INTEGER,
            start_reading_id INTEGER NOT NULL,
            end_reading_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity_sold INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_revenue REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (config_id) REFERENCES configurations(id) ON DELETE SET NULL,
            FOREIGN KEY (start_reading_id) REFERENCES counter_readings(id) ON DELETE CASCADE,
            FOREIGN KEY (end_reading_id) REFERENCES counter_readings(id) ON DELETE CASCADE
        )
    ''')
    
    # Migration: Add user_id to existing configurations if it doesn't exist
    cursor.execute("PRAGMA table_info(configurations)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'user_id' not in columns:
        # For migration: add user_id column, default to 1 (first user)
        cursor.execute('ALTER TABLE configurations ADD COLUMN user_id INTEGER DEFAULT 1')
        # Remove the old UNIQUE constraint on name only
        # SQLite doesn't support dropping constraints, so we'll handle duplicates in the app
    
    if 'cleaning_cost' not in columns:
        cursor.execute('ALTER TABLE configurations ADD COLUMN cleaning_cost REAL DEFAULT 0')
    
    if 'products_per_day' not in columns:
        cursor.execute('ALTER TABLE configurations ADD COLUMN products_per_day INTEGER DEFAULT 1')
    
    # Migration: Add config_id to sales tracking tables if it doesn't exist
    cursor.execute("PRAGMA table_info(counter_readings)")
    cr_columns = [column[1] for column in cursor.fetchall()]
    if 'config_id' not in cr_columns:
        cursor.execute('ALTER TABLE counter_readings ADD COLUMN config_id INTEGER')
    
    cursor.execute("PRAGMA table_info(cash_register_events)")
    cre_columns = [column[1] for column in cursor.fetchall()]
    if 'config_id' not in cre_columns:
        cursor.execute('ALTER TABLE cash_register_events ADD COLUMN config_id INTEGER')
    
    cursor.execute("PRAGMA table_info(sales_records)")
    sr_columns = [column[1] for column in cursor.fetchall()]
    if 'config_id' not in sr_columns:
        cursor.execute('ALTER TABLE sales_records ADD COLUMN config_id INTEGER')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Authentication routes
@app.route('/')
@login_required
def index():
    return render_template('index.html', user=current_user)

@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        password = data.get('password', '')
        
        if not email or not name or not password:
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        # Hash password and create user
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor.execute(
            'INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)',
            (email, name, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        # Log the user in
        user = User(user_id, email, name)
        login_user(user)
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, email, name, password_hash FROM users WHERE email = ?', (email,))
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data or not bcrypt.check_password_hash(user_data[3], password):
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        user = User(user_data[0], user_data[1], user_data[2])
        login_user(user, remember=True)
        
        return jsonify({'success': True, 'message': 'Login successful'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/calculate', methods=['POST'])
@login_required
def calculate():
    try:
        data = request.json
        ingredients = data.get('ingredients', {})
        drinks = data.get('drinks', [])
        cleaning_cost = data.get('cleaning_cost', 0)
        products_per_day = data.get('products_per_day', 1)
        tea_bags = data.get('tea_bags', {})  # Tea bags with per-unit costs
        
        # Calculate cleaning cost per product
        cleaning_cost_per_product = cleaning_cost / products_per_day if products_per_day > 0 else 0
        
        # Calculate cost for each drink
        results = []
        for drink in drinks:
            drink_cost = 0
            breakdown = []
            
            # Calculate bulk ingredients (kg/L based)
            for ingredient_name, amount in drink.get('ingredients', {}).items():
                if ingredient_name in ingredients:
                    ingredient_cost = ingredients[ingredient_name]
                    cost = ingredient_cost * amount
                    drink_cost += cost
                    breakdown.append({
                        'ingredient': ingredient_name,
                        'amount': amount,
                        'unit_cost': ingredient_cost,
                        'total_cost': round(cost, 2),
                        'type': 'bulk'
                    })
            
            # Calculate per-unit items (tea bags, etc.)
            for tea_name, quantity in drink.get('tea_bags', {}).items():
                if tea_name in tea_bags:
                    cost_per_unit = tea_bags[tea_name]
                    cost = cost_per_unit * quantity
                    drink_cost += cost
                    breakdown.append({
                        'ingredient': tea_name,
                        'amount': quantity,
                        'unit_cost': cost_per_unit,
                        'total_cost': round(cost, 2),
                        'type': 'per_unit'
                    })
            
            # Calculate custom items (cookies, etc.)
            for custom_item in drink.get('custom_items', []):
                cost = custom_item.get('cost', 0)
                drink_cost += cost
                breakdown.append({
                    'ingredient': custom_item.get('name', 'Custom Item'),
                    'amount': 1,
                    'unit_cost': cost,
                    'total_cost': round(cost, 2),
                    'type': 'custom'
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
            # Find matching drink data for vending price
            drink_data = next((d for d in drinks if d.get('name') == result['name']), None)
            vending_price = drink_data.get('vending_price', 0) if drink_data else 0
            
            # Drink name with profit info
            if vending_price > 0:
                profit = vending_price - result['total_cost']
                profit_margin = (profit / vending_price) * 100
                drink_name = Paragraph(
                    f"<b>{result['name']}</b> - Production Cost: €{result['total_cost']:.2f} | "
                    f"Vending Price: €{vending_price:.2f} | "
                    f"Profit: €{profit:.2f} ({profit_margin:.1f}%)", 
                    styles['Heading3']
                )
            else:
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
        
        # Sales Statistics Section (if user is logged in)
        if current_user.is_authenticated:
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                
                # Get sales statistics for last 30 days
                cursor.execute('''
                    SELECT 
                        product_name,
                        SUM(quantity_sold) as total_quantity,
                        SUM(total_revenue) as total_revenue,
                        AVG(unit_price) as avg_price
                    FROM sales_records
                    WHERE user_id = ? AND created_at >= datetime('now', '-30 days')
                    GROUP BY product_name
                    ORDER BY total_revenue DESC
                ''', (current_user.id,))
                
                sales_data = cursor.fetchall()
                
                if sales_data:
                    elements.append(Spacer(1, 30))
                    elements.append(Paragraph("Sales Statistics (Last 30 Days)", heading_style))
                    
                    total_revenue = sum(row[2] for row in sales_data)
                    total_items = sum(row[1] for row in sales_data)
                    
                    # Summary box
                    summary_data = [
                        ['Metric', 'Value'],
                        ['Total Items Sold', str(int(total_items))],
                        ['Total Revenue', f"€{total_revenue:.2f}"]
                    ]
                    
                    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
                    summary_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
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
                    elements.append(summary_table)
                    elements.append(Spacer(1, 20))
                    
                    # Product breakdown
                    elements.append(Paragraph("Sales by Product", styles['Heading3']))
                    elements.append(Spacer(1, 10))
                    
                    product_data = [['Product', 'Quantity', 'Avg Price', 'Revenue']]
                    for row in sales_data:
                        product_data.append([
                            row[0],
                            str(int(row[1])),
                            f"€{row[3]:.2f}",
                            f"€{row[2]:.2f}"
                        ])
                    
                    product_table = Table(product_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                    product_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')),
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
                    elements.append(product_table)
                    elements.append(Spacer(1, 20))
                    
                    # Cash register reconciliation
                    cursor.execute('''
                        SELECT cash_in_register, reading_date
                        FROM counter_readings
                        WHERE user_id = ?
                        ORDER BY reading_date DESC
                        LIMIT 1
                    ''', (current_user.id,))
                    
                    latest_reading = cursor.fetchone()
                    
                    if latest_reading:
                        elements.append(Paragraph("Cash Register Status", styles['Heading3']))
                        elements.append(Spacer(1, 10))
                        
                        # Calculate expected vs actual
                        actual_cash = latest_reading[0]
                        last_date = latest_reading[1]
                        
                        cursor.execute('''
                            SELECT COALESCE(SUM(total_revenue), 0)
                            FROM sales_records
                            WHERE user_id = ? AND created_at >= ?
                        ''', (current_user.id, last_date))
                        
                        sales_since = cursor.fetchone()[0]
                        
                        cursor.execute('''
                            SELECT 
                                COALESCE(SUM(CASE WHEN event_type = 'withdrawal' THEN amount ELSE 0 END), 0) as withdrawals,
                                COALESCE(SUM(CASE WHEN event_type = 'deposit' THEN amount ELSE 0 END), 0) as deposits
                            FROM cash_register_events
                            WHERE user_id = ? AND event_date >= ?
                        ''', (current_user.id, last_date))
                        
                        cash_events = cursor.fetchone()
                        withdrawals = cash_events[0]
                        deposits = cash_events[1]
                        
                        # Get previous cash
                        cursor.execute('''
                            SELECT cash_in_register
                            FROM counter_readings
                            WHERE user_id = ? AND reading_date < ?
                            ORDER BY reading_date DESC
                            LIMIT 1
                        ''', (current_user.id, last_date))
                        
                        prev = cursor.fetchone()
                        prev_cash = prev[0] if prev else 0
                        
                        expected_cash = prev_cash + sales_since + deposits - withdrawals
                        difference = actual_cash - expected_cash
                        
                        cash_data = [
                            ['Description', 'Amount'],
                            ['Expected Cash in Register', f"€{expected_cash:.2f}"],
                            ['Actual Cash in Register', f"€{actual_cash:.2f}"],
                            ['Difference', f"€{difference:.2f}"],
                            ['Status', 'OK' if abs(difference) < 5 else ('Warning' if abs(difference) < 10 else 'Check Required')]
                        ]
                        
                        cash_table = Table(cash_data, colWidths=[3*inch, 2*inch])
                        cash_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c' if abs(difference) > 10 else '#e67e22' if abs(difference) > 5 else '#27ae60')),
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
                        elements.append(cash_table)
                
                conn.close()
            except Exception as e:
                # If sales tracking fails, just skip it and continue with regular PDF
                print(f"Sales statistics error in PDF: {e}")
        
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
@login_required
def get_configs():
    """Get all saved configurations (owned and shared with user)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get user's own configurations
        cursor.execute('''
            SELECT id, name, created_at, updated_at, 'owner' as access_type
            FROM configurations 
            WHERE user_id = ?
            ORDER BY updated_at DESC
        ''', (current_user.id,))
        
        configs = []
        for row in cursor.fetchall():
            configs.append({
                'id': row[0],
                'name': row[1],
                'created_at': row[2],
                'updated_at': row[3],
                'access_type': row[4],
                'can_edit': True
            })
        
        # Get configurations shared with user
        cursor.execute('''
            SELECT c.id, c.name, c.created_at, c.updated_at, 'shared' as access_type, sc.can_edit,
                   u.name as owner_name
            FROM configurations c
            JOIN shared_configs sc ON c.id = sc.config_id
            JOIN users u ON c.user_id = u.id
            WHERE sc.shared_with_user_id = ?
            ORDER BY c.updated_at DESC
        ''', (current_user.id,))
        
        for row in cursor.fetchall():
            configs.append({
                'id': row[0],
                'name': row[1],
                'created_at': row[2],
                'updated_at': row[3],
                'access_type': row[4],
                'can_edit': bool(row[5]),
                'owner_name': row[6]
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
@login_required
def get_config(config_id):
    """Get a specific configuration by ID (if owned or shared)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if user owns this config or has access via sharing
        cursor.execute('''
            SELECT c.id, c.name, c.cleaning_cost, c.products_per_day, c.ingredients, c.drinks, 
                   c.created_at, c.updated_at, c.user_id
            FROM configurations c
            WHERE c.id = ? AND (c.user_id = ? OR EXISTS (
                SELECT 1 FROM shared_configs sc 
                WHERE sc.config_id = c.id AND sc.shared_with_user_id = ?
            ))
        ''', (config_id, current_user.id, current_user.id))
        
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
                    'updated_at': row[7],
                    'is_owner': row[8] == current_user.id
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Configuration not found or access denied'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/configs', methods=['POST'])
@login_required
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
            # Update existing configuration (must be owner or have edit access)
            cursor.execute('''
                SELECT user_id FROM configurations WHERE id = ?
            ''', (config_id,))
            config_owner = cursor.fetchone()
            
            if not config_owner:
                conn.close()
                return jsonify({'success': False, 'error': 'Configuration not found'}), 404
            
            # Check if user is owner or has edit access
            is_owner = config_owner[0] == current_user.id
            has_edit_access = False
            
            if not is_owner:
                cursor.execute('''
                    SELECT can_edit FROM shared_configs 
                    WHERE config_id = ? AND shared_with_user_id = ?
                ''', (config_id, current_user.id))
                result = cursor.fetchone()
                has_edit_access = result and result[0]
            
            if not is_owner and not has_edit_access:
                conn.close()
                return jsonify({'success': False, 'error': 'Permission denied'}), 403
            
            cursor.execute('''
                UPDATE configurations 
                SET name = ?, cleaning_cost = ?, products_per_day = ?, ingredients = ?, drinks = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (name, cleaning_cost, products_per_day, json.dumps(ingredients), json.dumps(drinks), config_id))
            
            result_id = config_id
        else:
            # Insert new configuration for current user
            try:
                cursor.execute('''
                    INSERT INTO configurations (user_id, name, cleaning_cost, products_per_day, ingredients, drinks)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (current_user.id, name, cleaning_cost, products_per_day, json.dumps(ingredients), json.dumps(drinks)))
                
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
@login_required
def delete_config(config_id):
    """Delete a configuration (owner only)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM configurations WHERE id = ? AND user_id = ?', (config_id, current_user.id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Configuration not found or permission denied'
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

# Configuration Sharing Endpoints
@app.route('/api/configs/<int:config_id>/share', methods=['POST'])
@login_required
def share_config(config_id):
    """Share a configuration with another user"""
    try:
        data = request.json
        share_with_email = data.get('email', '').strip().lower()
        can_edit = data.get('can_edit', False)
        
        if not share_with_email:
            return jsonify({'success': False, 'error': 'Email required'}), 400
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Verify user owns the configuration
        cursor.execute('SELECT user_id FROM configurations WHERE id = ?', (config_id,))
        config = cursor.fetchone()
        
        if not config or config[0] != current_user.id:
            conn.close()
            return jsonify({'success': False, 'error': 'Configuration not found or permission denied'}), 404
        
        # Find user to share with
        cursor.execute('SELECT id FROM users WHERE email = ?', (share_with_email,))
        share_user = cursor.fetchone()
        
        if not share_user:
            conn.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        share_user_id = share_user[0]
        
        if share_user_id == current_user.id:
            conn.close()
            return jsonify({'success': False, 'error': 'Cannot share with yourself'}), 400
        
        # Add or update sharing
        try:
            cursor.execute('''
                INSERT INTO shared_configs (config_id, shared_with_user_id, can_edit)
                VALUES (?, ?, ?)
                ON CONFLICT(config_id, shared_with_user_id) 
                DO UPDATE SET can_edit = excluded.can_edit
            ''', (config_id, share_user_id, can_edit))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Configuration shared successfully'})
        except sqlite3.IntegrityError as e:
            conn.close()
            return jsonify({'success': False, 'error': 'Sharing failed'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/configs/<int:config_id>/shared-users', methods=['GET'])
@login_required
def get_shared_users(config_id):
    """Get list of users a configuration is shared with"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Verify user owns the configuration
        cursor.execute('SELECT user_id FROM configurations WHERE id = ?', (config_id,))
        config = cursor.fetchone()
        
        if not config or config[0] != current_user.id:
            conn.close()
            return jsonify({'success': False, 'error': 'Permission denied'}), 403
        
        cursor.execute('''
            SELECT u.id, u.email, u.name, sc.can_edit, sc.shared_at
            FROM shared_configs sc
            JOIN users u ON sc.shared_with_user_id = u.id
            WHERE sc.config_id = ?
        ''', (config_id,))
        
        shared_users = []
        for row in cursor.fetchall():
            shared_users.append({
                'user_id': row[0],
                'email': row[1],
                'name': row[2],
                'can_edit': bool(row[3]),
                'shared_at': row[4]
            })
        
        conn.close()
        
        return jsonify({'success': True, 'shared_users': shared_users})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/configs/<int:config_id>/unshare/<int:user_id>', methods=['DELETE'])
@login_required
def unshare_config(config_id, user_id):
    """Remove sharing access for a user"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Verify user owns the configuration
        cursor.execute('SELECT user_id FROM configurations WHERE id = ?', (config_id,))
        config = cursor.fetchone()
        
        if not config or config[0] != current_user.id:
            conn.close()
            return jsonify({'success': False, 'error': 'Permission denied'}), 403
        
        cursor.execute('''
            DELETE FROM shared_configs 
            WHERE config_id = ? AND shared_with_user_id = ?
        ''', (config_id, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Sharing removed successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# Tea Bag Management Endpoints
@app.route('/api/tea-bags', methods=['GET'])
@login_required
def get_tea_bags():
    """Get all tea bags for current user"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, cost_per_unit, created_at
            FROM tea_bags
            WHERE user_id = ?
            ORDER BY name
        ''', (current_user.id,))
        
        tea_bags = []
        for row in cursor.fetchall():
            tea_bags.append({
                'id': row[0],
                'name': row[1],
                'cost_per_unit': row[2],
                'created_at': row[3]
            })
        
        conn.close()
        
        return jsonify({'success': True, 'tea_bags': tea_bags})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/tea-bags', methods=['POST'])
@login_required
def add_tea_bag():
    """Add or update a tea bag"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        cost_per_unit = data.get('cost_per_unit', 0)
        tea_bag_id = data.get('id')
        
        if not name or cost_per_unit <= 0:
            return jsonify({'success': False, 'error': 'Name and cost are required'}), 400
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        if tea_bag_id:
            # Update existing
            cursor.execute('''
                UPDATE tea_bags 
                SET name = ?, cost_per_unit = ?
                WHERE id = ? AND user_id = ?
            ''', (name, cost_per_unit, tea_bag_id, current_user.id))
            
            if cursor.rowcount == 0:
                conn.close()
                return jsonify({'success': False, 'error': 'Tea bag not found'}), 404
        else:
            # Insert new
            try:
                cursor.execute('''
                    INSERT INTO tea_bags (user_id, name, cost_per_unit)
                    VALUES (?, ?, ?)
                ''', (current_user.id, name, cost_per_unit))
            except sqlite3.IntegrityError:
                conn.close()
                return jsonify({'success': False, 'error': 'Tea bag with this name already exists'}), 400
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Tea bag saved successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/tea-bags/<int:tea_bag_id>', methods=['DELETE'])
@login_required
def delete_tea_bag(tea_bag_id):
    """Delete a tea bag"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tea_bags WHERE id = ? AND user_id = ?', (tea_bag_id, current_user.id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Tea bag not found'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Tea bag deleted successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# Sales Tracking Endpoints

@app.route('/api/counter-readings', methods=['GET'])
@login_required
def get_counter_readings():
    """Get all counter readings for the current user/config"""
    try:
        config_id = request.args.get('config_id', type=int)
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Build query based on whether config_id is provided
        if config_id:
            # Verify user has access to this config
            cursor.execute('''
                SELECT id FROM configurations WHERE id = ? AND user_id = ?
                UNION
                SELECT c.id FROM configurations c
                JOIN shared_configs sc ON c.id = sc.config_id
                WHERE c.id = ? AND sc.shared_with_user_id = ?
            ''', (config_id, current_user.id, config_id, current_user.id))
            
            if not cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'error': 'Access denied'}), 403
            
            cursor.execute('''
                SELECT id, reading_date, counter_data, cash_in_register, notes, config_id
                FROM counter_readings
                WHERE config_id = ?
                ORDER BY reading_date DESC
                LIMIT 50
            ''', (config_id,))
        else:
            # Get all readings for user (backward compatibility)
            cursor.execute('''
                SELECT id, reading_date, counter_data, cash_in_register, notes, config_id
                FROM counter_readings
                WHERE user_id = ?
                ORDER BY reading_date DESC
                LIMIT 50
            ''', (current_user.id,))
        
        readings = []
        for row in cursor.fetchall():
            readings.append({
                'id': row[0],
                'reading_date': row[1],
                'counter_data': json.loads(row[2]),
                'cash_in_register': row[3],
                'notes': row[4],
                'config_id': row[5]
            })
        
        conn.close()
        return jsonify({'success': True, 'readings': readings})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/counter-readings', methods=['POST'])
@login_required
def submit_counter_reading():
    """Submit a new counter reading and calculate sales"""
    try:
        data = request.get_json()
        counter_data = data.get('counter_data', {})  # {productName: counterValue}
        cash_in_register = float(data.get('cash_in_register', 0))
        notes = data.get('notes', '')
        product_prices = data.get('product_prices', {})  # {productName: price}
        config_id = data.get('config_id')  # Link to configuration
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Verify user has access to this config if provided
        if config_id:
            cursor.execute('''
                SELECT id FROM configurations WHERE id = ? AND user_id = ?
                UNION
                SELECT c.id FROM configurations c
                JOIN shared_configs sc ON c.id = sc.config_id
                WHERE c.id = ? AND sc.shared_with_user_id = ?
            ''', (config_id, current_user.id, config_id, current_user.id))
            
            if not cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Insert new counter reading
        cursor.execute('''
            INSERT INTO counter_readings (user_id, config_id, counter_data, cash_in_register, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (current_user.id, config_id, json.dumps(counter_data), cash_in_register, notes))
        
        new_reading_id = cursor.lastrowid
        
        # Get the previous reading to calculate sales (same config or user if no config)
        if config_id:
            cursor.execute('''
                SELECT id, counter_data, cash_in_register
                FROM counter_readings
                WHERE config_id = ? AND id < ?
                ORDER BY reading_date DESC
                LIMIT 1
            ''', (config_id, new_reading_id))
        else:
            cursor.execute('''
                SELECT id, counter_data, cash_in_register
                FROM counter_readings
                WHERE user_id = ? AND id < ? AND config_id IS NULL
                ORDER BY reading_date DESC
                LIMIT 1
            ''', (current_user.id, new_reading_id))
        
        prev_reading = cursor.fetchone()
        
        sales_calculated = []
        
        if prev_reading:
            prev_id = prev_reading[0]
            prev_counter_data = json.loads(prev_reading[1])
            
            # Calculate sales for each product
            for product_name, current_count in counter_data.items():
                prev_count = prev_counter_data.get(product_name, 0)
                quantity_sold = current_count - prev_count
                
                if quantity_sold > 0:
                    if product_name in product_prices:
                        unit_price = product_prices[product_name]
                        total_revenue = quantity_sold * unit_price
                        
                        # Insert sales record
                        cursor.execute('''
                            INSERT INTO sales_records 
                            (user_id, config_id, start_reading_id, end_reading_id, product_name, quantity_sold, unit_price, total_revenue)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (current_user.id, config_id, prev_id, new_reading_id, product_name, quantity_sold, unit_price, total_revenue))
                        
                        sales_calculated.append({
                            'product': product_name,
                            'quantity': quantity_sold,
                            'revenue': total_revenue
                        })
                    else:
                        # Log warning if no price found for product with sales
                        print(f"Warning: No price found for product '{product_name}' with {quantity_sold} units sold")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'reading_id': new_reading_id,
            'sales_calculated': sales_calculated,
            'message': 'Counter reading submitted successfully'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/counter-readings/<int:reading_id>', methods=['DELETE'])
@login_required
def delete_counter_reading(reading_id):
    """Delete a counter reading and its associated sales records"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Verify the reading exists and user has access
        cursor.execute('''
            SELECT cr.user_id, cr.config_id
            FROM counter_readings cr
            WHERE cr.id = ?
        ''', (reading_id,))
        
        reading = cursor.fetchone()
        
        if not reading:
            conn.close()
            return jsonify({'success': False, 'error': 'Reading not found'}), 404
        
        # Check if user owns the reading or has access through shared config
        if reading[1]:  # Has config_id
            cursor.execute('''
                SELECT id FROM configurations WHERE id = ? AND user_id = ?
                UNION
                SELECT c.id FROM configurations c
                JOIN shared_configs sc ON c.id = sc.config_id
                WHERE c.id = ? AND sc.shared_with_user_id = ? AND sc.can_edit = 1
            ''', (reading[1], current_user.id, reading[1], current_user.id))
            
            if not cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'error': 'Permission denied'}), 403
        else:  # No config, check user ownership
            if reading[0] != current_user.id:
                conn.close()
                return jsonify({'success': False, 'error': 'Permission denied'}), 403
        
        # Delete associated sales records (CASCADE should handle this, but let's be explicit)
        cursor.execute('DELETE FROM sales_records WHERE start_reading_id = ? OR end_reading_id = ?', 
                      (reading_id, reading_id))
        
        # Delete the reading
        cursor.execute('DELETE FROM counter_readings WHERE id = ?', (reading_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Reading deleted successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/cash-register/balance', methods=['GET'])
@login_required
def get_cash_register_balance():
    """Get current cash register balance and reconciliation"""
    try:
        config_id = request.args.get('config_id', type=int)
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get the latest counter reading
        if config_id:
            cursor.execute('''
                SELECT id, cash_in_register, reading_date, config_id
                FROM counter_readings
                WHERE config_id = ?
                ORDER BY reading_date DESC
                LIMIT 1
            ''', (config_id,))
        else:
            cursor.execute('''
                SELECT id, cash_in_register, reading_date, config_id
                FROM counter_readings
                WHERE user_id = ?
                ORDER BY reading_date DESC
                LIMIT 1
            ''', (current_user.id,))
        
        latest_reading = cursor.fetchone()
        
        if not latest_reading:
            conn.close()
            return jsonify({
                'success': True,
                'actual_cash': 0,
                'expected_cash': 0,
                'difference': 0,
                'withdrawals': 0,
                'deposits': 0,
                'total_sales': 0,
                'last_reading_date': None
            })
        
        actual_cash = latest_reading[1]
        last_reading_date = latest_reading[2]
        reading_id = latest_reading[0]
        reading_config_id = latest_reading[3]
        
        # Calculate total sales revenue since last reading
        cursor.execute('''
            SELECT COALESCE(SUM(total_revenue), 0)
            FROM sales_records
            WHERE end_reading_id = ?
        ''', (reading_id,))
        
        total_sales = cursor.fetchone()[0]
        
        # CORRECTED LOGIC:
        # Since withdrawals/deposits auto-update the actual cash via new readings,
        # the latest reading's cash amount ALREADY includes all money movements.
        # 
        # Expected cash = actual cash from latest reading (which is correct baseline)
        # The difference should ONLY show discrepancies from manual counter vs system calculation
        #
        # If there are sales calculated but not yet in a new reading, expected > actual
        # If actual cash was manually counted and differs, there's a real discrepancy
        
        # For now, with auto-updates: Expected should equal Actual
        # Difference shows if you need to submit a new counter reading with sales
        expected_cash = actual_cash + total_sales
        
        # Difference: negative means you haven't deposited sales yet, positive means extra cash
        difference = actual_cash - expected_cash
        
        conn.close()
        
        return jsonify({
            'success': True,
            'actual_cash': round(actual_cash, 2),
            'expected_cash': round(expected_cash, 2),
            'difference': round(difference, 2),
            'withdrawals': 0,
            'deposits': 0,
            'total_sales': round(total_sales, 2),
            'last_reading_date': last_reading_date
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/cash-register/events', methods=['GET'])
@login_required
def get_cash_register_events():
    """Get cash register events history"""
    try:
        config_id = request.args.get('config_id', type=int)
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        if config_id:
            cursor.execute('''
                SELECT id, event_date, event_type, amount, description
                FROM cash_register_events
                WHERE config_id = ?
                ORDER BY event_date DESC
                LIMIT 100
            ''', (config_id,))
        else:
            cursor.execute('''
                SELECT id, event_date, event_type, amount, description
                FROM cash_register_events
                WHERE user_id = ?
                ORDER BY event_date DESC
                LIMIT 100
            ''', (current_user.id,))
        
        events = []
        for row in cursor.fetchall():
            events.append({
                'id': row[0],
                'event_date': row[1],
                'event_type': row[2],
                'amount': row[3],
                'description': row[4]
            })
        
        conn.close()
        return jsonify({'success': True, 'events': events})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/cash-register/events', methods=['POST'])
@login_required
def record_cash_event():
    """Record a cash register event (withdrawal/deposit) and auto-update actual cash"""
    try:
        data = request.get_json()
        event_type = data.get('event_type')  # 'withdrawal' or 'deposit'
        amount = float(data.get('amount', 0))
        description = data.get('description', '')
        config_id = data.get('config_id')  # Link to configuration
        
        if event_type not in ['withdrawal', 'deposit']:
            return jsonify({'success': False, 'error': 'Invalid event type'}), 400
        
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be positive'}), 400
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get the latest counter reading to update cash
        if config_id:
            cursor.execute('''
                SELECT id, counter_data, cash_in_register, notes
                FROM counter_readings
                WHERE config_id = ?
                ORDER BY reading_date DESC
                LIMIT 1
            ''', (config_id,))
        else:
            cursor.execute('''
                SELECT id, counter_data, cash_in_register, notes
                FROM counter_readings
                WHERE user_id = ? AND config_id IS NULL
                ORDER BY reading_date DESC
                LIMIT 1
            ''', (current_user.id,))
        
        latest_reading = cursor.fetchone()
        
        # Record the cash event
        cursor.execute('''
            INSERT INTO cash_register_events (user_id, config_id, event_type, amount, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (current_user.id, config_id, event_type, amount, description))
        
        # Auto-update actual cash by creating a new counter reading
        if latest_reading:
            old_cash = latest_reading[2]
            counter_data = latest_reading[1]  # Keep same counter values
            old_notes = latest_reading[3] or ''
            
            # Calculate new cash amount
            if event_type == 'withdrawal':
                new_cash = old_cash - amount
            else:  # deposit
                new_cash = old_cash + amount
            
            # Create auto-generated note
            auto_note = f"Auto-updated after {event_type}: {description}"
            if old_notes:
                auto_note = f"{old_notes} | {auto_note}"
            
            # Insert new counter reading with updated cash
            cursor.execute('''
                INSERT INTO counter_readings (user_id, config_id, counter_data, cash_in_register, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (current_user.id, config_id, counter_data, new_cash, auto_note))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{event_type.capitalize()} recorded and cash register updated automatically'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/sales-statistics', methods=['GET'])
@login_required
def get_sales_statistics():
    """Get sales statistics and analytics"""
    try:
        days = int(request.args.get('days', 30))  # Default 30 days
        config_id = request.args.get('config_id', type=int)
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get sales by product
        if config_id:
            cursor.execute('''
                SELECT 
                    product_name,
                    SUM(quantity_sold) as total_quantity,
                    SUM(total_revenue) as total_revenue,
                    AVG(unit_price) as avg_price
                FROM sales_records
                WHERE config_id = ? AND created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY product_name
                ORDER BY total_revenue DESC
            ''', (config_id, days))
        else:
            cursor.execute('''
                SELECT 
                    product_name,
                    SUM(quantity_sold) as total_quantity,
                    SUM(total_revenue) as total_revenue,
                    AVG(unit_price) as avg_price
                FROM sales_records
                WHERE user_id = ? AND created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY product_name
                ORDER BY total_revenue DESC
            ''', (current_user.id, days))
        
        products = []
        total_revenue = 0
        total_items = 0
        
        for row in cursor.fetchall():
            product_data = {
                'name': row[0],
                'quantity': row[1],
                'revenue': round(row[2], 2),
                'avg_price': round(row[3], 2)
            }
            products.append(product_data)
            total_revenue += row[2]
            total_items += row[1]
        
        # Get daily sales trend
        if config_id:
            cursor.execute('''
                SELECT 
                    DATE(created_at) as sale_date,
                    SUM(quantity_sold) as daily_quantity,
                    SUM(total_revenue) as daily_revenue
                FROM sales_records
                WHERE config_id = ? AND created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY DATE(created_at)
                ORDER BY sale_date ASC
            ''', (config_id, days))
        else:
            cursor.execute('''
                SELECT 
                    DATE(created_at) as sale_date,
                    SUM(quantity_sold) as daily_quantity,
                    SUM(total_revenue) as daily_revenue
                FROM sales_records
                WHERE user_id = ? AND created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY DATE(created_at)
                ORDER BY sale_date ASC
            ''', (current_user.id, days))
        
        daily_trend = []
        for row in cursor.fetchall():
            daily_trend.append({
                'date': row[0],
                'quantity': row[1],
                'revenue': round(row[2], 2)
            })
        
        # Get total cash register discrepancies
        if config_id:
            cursor.execute('''
                SELECT COUNT(*) as readings_count
                FROM counter_readings
                WHERE config_id = ? AND reading_date >= datetime('now', '-' || ? || ' days')
            ''', (config_id, days))
        else:
            cursor.execute('''
                SELECT COUNT(*) as readings_count
                FROM counter_readings
                WHERE user_id = ? AND reading_date >= datetime('now', '-' || ? || ' days')
            ''', (current_user.id, days))
        
        readings_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_revenue': round(total_revenue, 2),
                'total_items_sold': total_items,
                'products': products,
                'daily_trend': daily_trend,
                'readings_count': readings_count,
                'period_days': days
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
