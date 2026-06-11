# Smart G Networks Application
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import bcrypt
import jwt
import datetime
from functools import wraps
from config import Config

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config.from_object(Config)
CORS(app)

# Database initialization flag
_db_initialized = False

def init_db_on_startup():
    """Initialize database if not already done"""
    global _db_initialized
    if _db_initialized:
        return
    
    try:
        # Try to initialize database
        from init_railway import init_database
        init_database()
        _db_initialized = True
    except Exception as e:
        print(f"Note: Database initialization attempted: {e}")

# Database connection
def get_db():
    try:
        return mysql.connector.connect(
            host=app.config['MYSQL_HOST'] or 'localhost',
            user=app.config['MYSQL_USER'] or 'root',
            password=app.config['MYSQL_PASSWORD'] or '',
            database=app.config['MYSQL_DATABASE'] or 'smart_g_networks',
            port=app.config['MYSQL_PORT'] or 3306
        )
    except Exception as e:
        print(f"Database connection failed: {e}")
        print(f"Config - Host: {app.config['MYSQL_HOST']}, User: {app.config['MYSQL_USER']}, DB: {app.config['MYSQL_DATABASE']}")
        raise

# JWT Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            token = token.split(' ')[1] if ' ' in token else token
            data = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
            request.user = data
        except:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

# Helper function to hash password
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Serve index.html
@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({'status': 'healthy'}), 200

# ==================== AUTHENTICATION ====================
@app.route('/api/login', methods=['POST'])
def login():
    global _db_initialized
    if not _db_initialized:
        init_db_on_startup()
    
    data = request.json
    email = data.get('email')
    password = data.get('password')
    role_val = data.get('role')
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    
    if not user or not check_password(password, user['password_hash']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Role validation
    if role_val == 'admin' and user['role'] != 'admin':
        return jsonify({'error': 'Not admin'}), 403
    if role_val.startswith('branch_') and user['role'] != 'manager':
        return jsonify({'error': 'Invalid branch manager'}), 403
    if role_val.startswith('branch_'):
        branch_id = int(role_val.split('_')[1])
        if user['branch_id'] != branch_id:
            return jsonify({'error': 'Branch mismatch'}), 403
    
    token = jwt.encode({
        'id': user['id'],
        'email': user['email'],
        'role': user['role'],
        'branch_id': user['branch_id'],
        'branch_name': user['branch_name'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['JWT_SECRET'], algorithm='HS256')
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role'],
            'branch_id': user['branch_id'],
            'branch_name': user['branch_name']
        }
    })

# ==================== BRANCH MANAGEMENT ====================
@app.route('/api/public/branches', methods=['GET'])
def get_branches_public():
    """Public endpoint for login page to fetch branches"""
    global _db_initialized
    if not _db_initialized:
        init_db_on_startup()
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, branch_id, branch_name FROM users WHERE role = 'manager' ORDER BY branch_name")
    branches = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(branches)

@app.route('/api/branches', methods=['GET'])
@token_required
def get_branches():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, branch_id, branch_name FROM users WHERE role = 'manager'")
    branches = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(branches)

@app.route('/api/branches', methods=['POST'])
@token_required
def create_branch():
    if request.user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.json
    db = get_db()
    cursor = db.cursor()
    
    # Get next branch_id
    cursor.execute("SELECT MAX(branch_id) as max_id FROM users")
    result = cursor.fetchone()
    max_id = result[0] if result[0] else 1
    new_branch_id = max_id + 1
    
    password_hash = hash_password(data['password'])
    cursor.execute("""
        INSERT INTO users (name, email, password_hash, role, branch_id, branch_name)
        VALUES (%s, %s, %s, 'manager', %s, %s)
    """, (data['manager'], data['email'], password_hash, new_branch_id, data['name']))
    
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({'success': True, 'branch_id': new_branch_id})

@app.route('/api/branches/<int:branch_id>', methods=['DELETE'])
@token_required
def delete_branch(branch_id):
    if request.user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM users WHERE branch_id = %s AND role = 'manager'", (branch_id,))
    cursor.execute("DELETE FROM branch_stock WHERE branch_id = %s", (branch_id,))
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({'success': True})

@app.route('/api/branches/<int:branch_id>/reset-password', methods=['POST'])
@token_required
def reset_branch_password(branch_id):
    if request.user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.json
    password_hash = hash_password(data['new_password'])
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET password_hash = %s WHERE branch_id = %s AND role = 'manager'", 
                   (password_hash, branch_id))
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({'success': True})

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')
    new_password = data.get('new_password')
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    if not user:
        cursor.close()
        db.close()
        return jsonify({'error': 'Email not found'}), 404
    
    password_hash = hash_password(new_password)
    cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", (password_hash, email))
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({'success': True})

# ==================== PRODUCT MANAGEMENT ====================
@app.route('/api/products', methods=['GET'])
@token_required
def get_products():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products ORDER BY id")
    products = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
@token_required
def create_product():
    if request.user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.json
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        INSERT INTO products (product_code, name, price, cost, sales_commission, manager_commission, central_stock, low_stock_threshold)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (data['product_code'], data['name'], data['price'], data['cost'], 
          data.get('sales_commission', 0), data.get('manager_commission', 0),
          data.get('central_stock', 0), data.get('low_stock_threshold', 5)))
    
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({'success': True})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(product_id):
    if request.user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    db = get_db()
    cursor = db.cursor()
    try:
        # Delete related records first
        cursor.execute("DELETE FROM sale_items WHERE product_id = %s", (product_id,))
        cursor.execute("DELETE FROM branch_stock WHERE product_id = %s", (product_id,))
        cursor.execute("DELETE FROM stock_approvals WHERE product_id = %s", (product_id,))
        # Now delete the product
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        cursor.close()
        db.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>/add-stock', methods=['POST'])
@token_required
def add_product_stock(product_id):
    if request.user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.json
    quantity = int(data.get('quantity', 0))
    
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be greater than 0'}), 400
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Check if product exists
    cursor.execute("SELECT id, central_stock FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        cursor.close()
        db.close()
        return jsonify({'error': 'Product not found'}), 404
    
    # Update stock
    cursor.execute("UPDATE products SET central_stock = central_stock + %s WHERE id = %s", 
                   (quantity, product_id))
    db.commit()
    
    # Get updated stock
    cursor.execute("SELECT central_stock FROM products WHERE id = %s", (product_id,))
    updated = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    return jsonify({'success': True, 'new_stock': updated['central_stock']})

# ==================== BRANCH STOCK ====================
@app.route('/api/branch-stock', methods=['GET'])
@token_required
def get_branch_stock():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if request.user['role'] == 'admin':
        cursor.execute("SELECT * FROM branch_stock")
    else:
        cursor.execute("SELECT * FROM branch_stock WHERE branch_id = %s", (request.user['branch_id'],))
    
    stock = cursor.fetchall()
    cursor.close()
    db.close()
    
    return jsonify(stock)

# ==================== STOCK TRANSFER ====================
@app.route('/api/stock-transfer', methods=['POST'])
@token_required
def transfer_stock():
    if request.user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.json
    product_id = data.get('product_id')
    branch_id = data.get('branch_id')
    quantity = data.get('quantity')
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Check central stock
    cursor.execute("SELECT name, central_stock FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    
    if not product or product['central_stock'] < quantity:
        cursor.close()
        db.close()
        return jsonify({'error': 'Insufficient central stock'}), 400
    
    # Reduce central stock
    cursor.execute("UPDATE products SET central_stock = central_stock - %s WHERE id = %s", 
                   (quantity, product_id))
    
    # Update branch stock
    cursor.execute("""
        INSERT INTO branch_stock (branch_id, product_id, quantity) 
        VALUES (%s, %s, %s) 
        ON DUPLICATE KEY UPDATE quantity = quantity + %s
    """, (branch_id, product_id, quantity, quantity))
    
    # Create approval record
    cursor.execute("""
        INSERT INTO stock_approvals (product_id, product_name, branch_id, quantity, status)
        VALUES (%s, %s, %s, %s, 'pending')
    """, (product_id, product['name'], branch_id, quantity))
    
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({'success': True})

@app.route('/api/stock-approvals', methods=['GET'])
@token_required
def get_stock_approvals():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if request.user['role'] == 'admin':
        cursor.execute("SELECT * FROM stock_approvals ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM stock_approvals WHERE branch_id = %s ORDER BY created_at DESC", 
                       (request.user['branch_id'],))
    
    approvals = cursor.fetchall()
    cursor.close()
    db.close()
    
    return jsonify(approvals)

@app.route('/api/stock-approvals/<int:approval_id>/<string:action>', methods=['POST'])
@token_required
def approve_stock_transfer(approval_id, action):
    if action not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid action'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("UPDATE stock_approvals SET status = %s WHERE id = %s", (action, approval_id))
    
    if action == 'rejected':
        # Restore central stock if rejected
        cursor.execute("""
            SELECT product_id, quantity FROM stock_approvals WHERE id = %s
        """, (approval_id,))
        approval = cursor.fetchone()
        if approval:
            cursor.execute("UPDATE products SET central_stock = central_stock + %s WHERE id = %s", 
                           (approval[1], approval[0]))
    
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({'success': True})

# ==================== SALES ====================
@app.route('/api/sales', methods=['POST'])
@token_required
def create_sale():
    data = request.json
    items = data.get('items', [])
    branch_id = request.user['branch_id']
    branch_name = request.user['branch_name']
    sale_date = datetime.datetime.now().date()
    
    if not items or len(items) == 0:
        return jsonify({'error': 'Sale must contain at least one item'}), 400
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    total_amount = 0
    total_commission = 0
    
    # Check stock availability and calculate totals
    for item in items:
        if not item.get('product_id') or not item.get('quantity'):
            cursor.close()
            db.close()
            return jsonify({'error': 'Product ID and quantity required for all items'}), 400
        
        if int(item['quantity']) <= 0:
            cursor.close()
            db.close()
            return jsonify({'error': 'Quantity must be greater than 0'}), 400
        cursor.execute("SELECT * FROM products WHERE id = %s", (item['product_id'],))
        product = cursor.fetchone()
        if not product:
            cursor.close()
            db.close()
            return jsonify({'error': f'Product not found'}), 404
        
        # Check branch stock
        cursor.execute("SELECT quantity FROM branch_stock WHERE branch_id = %s AND product_id = %s", 
                       (branch_id, item['product_id']))
        stock = cursor.fetchone()
        
        if not stock or stock['quantity'] < item['quantity']:
            cursor.close()
            db.close()
            return jsonify({'error': f'Insufficient stock for {product["name"]}'}), 400
        
        total_amount += product['price'] * item['quantity']
        total_commission += product['sales_commission'] * item['quantity']
    
    # Create sale record
    cursor.execute("""
        INSERT INTO sales (sale_date, branch_id, branch_name, total_amount, total_sales_commission)
        VALUES (%s, %s, %s, %s, %s)
    """, (sale_date, branch_id, branch_name, total_amount, total_commission))
    
    sale_id = cursor.lastrowid
    
    # Create sale items and deduct stock
    for item in items:
        cursor.execute("SELECT * FROM products WHERE id = %s", (item['product_id'],))
        product = cursor.fetchone()
        
        cursor.execute("""
            INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, total_price, commission)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (sale_id, item['product_id'], product['name'], item['quantity'], 
              product['price'], product['price'] * item['quantity'], product['sales_commission'] * item['quantity']))
        
        # Deduct from branch stock
        cursor.execute("""
            UPDATE branch_stock SET quantity = quantity - %s 
            WHERE branch_id = %s AND product_id = %s
        """, (item['quantity'], branch_id, item['product_id']))
    
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({'success': True, 'sale_id': sale_id})

@app.route('/api/sales', methods=['GET'])
@token_required
def get_sales():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if request.user['role'] == 'admin':
        cursor.execute("SELECT * FROM sales ORDER BY sale_date DESC, created_at DESC")
    else:
        cursor.execute("SELECT * FROM sales WHERE branch_id = %s ORDER BY sale_date DESC, created_at DESC", 
                       (request.user['branch_id'],))
    
    sales = cursor.fetchall()
    
    # Get sale items for each sale
    for sale in sales:
        cursor.execute("SELECT * FROM sale_items WHERE sale_id = %s", (sale['id'],))
        sale['items'] = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return jsonify(sales)

# ==================== EXPENSES ====================
@app.route('/api/expenses', methods=['POST'])
@token_required
def add_expense():
    data = request.json
    branch_id = request.user['branch_id'] if request.user['role'] == 'manager' else data.get('branch_id', request.user.get('branch_id'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO expenses (branch_id, amount, reason, type)
        VALUES (%s, %s, %s, %s)
    """, (branch_id, data['amount'], data.get('reason', ''), data.get('type', 'expense')))
    
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({'success': True})

@app.route('/api/expenses', methods=['GET'])
@token_required
def get_expenses():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if request.user['role'] == 'admin':
        cursor.execute("SELECT * FROM expenses ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM expenses WHERE branch_id = %s ORDER BY created_at DESC", 
                       (request.user['branch_id'],))
    
    expenses = cursor.fetchall()
    cursor.close()
    db.close()
    
    return jsonify(expenses)

# ==================== REPORTS ====================
@app.route('/api/reports', methods=['POST'])
@token_required
def submit_report():
    data = request.json
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO branch_reports (branch_id, branch_name, title, summary, daily_production, 
                   sales_commission, total_deductions, deduction_reason, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
    """, (request.user['branch_id'], request.user['branch_name'], data['title'], 
          data.get('summary', ''), data['daily_production'], data['sales_commission'],
          data['total_deductions'], data.get('deduction_reason', '')))
    
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({'success': True})

@app.route('/api/reports', methods=['GET'])
@token_required
def get_reports():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if request.user['role'] == 'admin':
        cursor.execute("SELECT * FROM branch_reports ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM branch_reports WHERE branch_id = %s ORDER BY created_at DESC", 
                       (request.user['branch_id'],))
    
    reports = cursor.fetchall()
    cursor.close()
    db.close()
    
    return jsonify(reports)

@app.route('/api/reports/<int:report_id>/<string:action>', methods=['POST'])
@token_required
def approve_report(report_id, action):
    if request.user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    if action not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid action'}), 400
    
    data = request.json
    admin_comment = data.get('admin_comment', '')
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE branch_reports SET status = %s, admin_comment = %s WHERE id = %s", 
                   (action, admin_comment, report_id))
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({'success': True})

# ==================== DASHBOARD STATS ====================
@app.route('/api/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    today = datetime.datetime.now().date()
    
    # Today's sales
    if request.user['role'] == 'admin':
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as today_sales FROM sales WHERE sale_date = %s", (today,))
    else:
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as today_sales FROM sales WHERE branch_id = %s AND sale_date = %s", 
                       (request.user['branch_id'], today))
    today_sales = cursor.fetchone()['today_sales']
    
    # Total revenue
    if request.user['role'] == 'admin':
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as total_revenue FROM sales")
    else:
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as total_revenue FROM sales WHERE branch_id = %s", 
                       (request.user['branch_id'],))
    total_revenue = cursor.fetchone()['total_revenue']
    
    # Product count
    cursor.execute("SELECT COUNT(*) as count FROM products")
    product_count = cursor.fetchone()['count']
    
    # Low stock count
    if request.user['role'] == 'admin':
        cursor.execute("""
            SELECT COUNT(*) as count FROM branch_stock bs 
            JOIN products p ON bs.product_id = p.id 
            WHERE bs.quantity <= p.low_stock_threshold
        """)
    else:
        cursor.execute("""
            SELECT COUNT(*) as count FROM branch_stock bs 
            JOIN products p ON bs.product_id = p.id 
            WHERE bs.branch_id = %s AND bs.quantity <= p.low_stock_threshold
        """, (request.user['branch_id'],))
    low_stock = cursor.fetchone()['count']
    
    cursor.close()
    db.close()
    
    return jsonify({
        'today_sales': float(today_sales),
        'total_revenue': float(total_revenue),
        'product_count': product_count,
        'low_stock': low_stock
    })

# ==================== COMPANY PROFITS ====================
@app.route('/api/company/profits', methods=['GET'])
@token_required
def get_company_profits():
    if request.user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Total revenue
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as total_revenue FROM sales")
    total_revenue = cursor.fetchone()['total_revenue']
    
    # Total sales commission
    cursor.execute("SELECT COALESCE(SUM(total_sales_commission), 0) as total_commission FROM sales")
    total_commission = cursor.fetchone()['total_commission']
    
    # Total expenses
    cursor.execute("SELECT COALESCE(SUM(amount), 0) as total_expenses FROM expenses")
    total_expenses = cursor.fetchone()['total_expenses']
    
    # Gross profit (revenue - cost)
    cursor.execute("""
        SELECT COALESCE(SUM((p.price - p.cost) * si.quantity), 0) as gross_profit
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
    """)
    gross_profit = cursor.fetchone()['gross_profit']
    
    cursor.close()
    db.close()
    
    net_profit = gross_profit - total_commission - total_expenses
    
    return jsonify({
        'totalRevenue': float(total_revenue),
        'totalSalesCommission': float(total_commission),
        'totalExpenses': float(total_expenses),
        'grossProfit': float(gross_profit),
        'netProfit': float(net_profit)
    })

# ==================== TODAY'S PRODUCTION ====================
@app.route('/api/today-production', methods=['GET'])
@token_required
def get_today_production():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    today = datetime.datetime.now().date()
    
    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0) as daily_production,
               COALESCE(SUM(total_sales_commission), 0) as sales_commission
        FROM sales 
        WHERE branch_id = %s AND sale_date = %s
    """, (request.user['branch_id'], today))
    
    result = cursor.fetchone()
    cursor.close()
    db.close()
    
    return jsonify({
        'daily_production': float(result['daily_production']),
        'sales_commission': float(result['sales_commission'])
    })

# ==================== ADMIN FEATURES ====================
@app.route('/api/admin/change-password', methods=['POST'])
@token_required
def admin_change_password():
    if request.user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'All fields required'}), 400
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Get admin's current password hash
    cursor.execute("SELECT password_hash FROM users WHERE id = %s", (request.user['id'],))
    user = cursor.fetchone()
    
    if not user or not check_password(current_password, user['password_hash']):
        cursor.close()
        db.close()
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # Update password
    password_hash = hash_password(new_password)
    cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", 
                   (password_hash, request.user['id']))
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})

@app.route('/api/admin/reset-sales', methods=['POST'])
@token_required
def admin_reset_sales():
    if request.user['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.json
    reset_type = data.get('reset_type', 'all')  # 'all', 'date', 'branch'
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        if reset_type == 'all':
            # Delete all sales and sale items
            cursor.execute("DELETE FROM sale_items")
            cursor.execute("DELETE FROM sales")
        elif reset_type == 'date':
            # Delete sales for specific date
            sale_date = data.get('sale_date')
            if not sale_date:
                return jsonify({'error': 'Sale date required'}), 400
            cursor.execute("SELECT id FROM sales WHERE sale_date = %s", (sale_date,))
            sale_ids = [row[0] for row in cursor.fetchall()]
            if sale_ids:
                for sale_id in sale_ids:
                    cursor.execute("DELETE FROM sale_items WHERE sale_id = %s", (sale_id,))
                cursor.execute("DELETE FROM sales WHERE sale_date = %s", (sale_date,))
        elif reset_type == 'branch':
            # Delete sales for specific branch
            branch_id = data.get('branch_id')
            if not branch_id:
                return jsonify({'error': 'Branch ID required'}), 400
            cursor.execute("SELECT id FROM sales WHERE branch_id = %s", (branch_id,))
            sale_ids = [row[0] for row in cursor.fetchall()]
            if sale_ids:
                for sale_id in sale_ids:
                    cursor.execute("DELETE FROM sale_items WHERE sale_id = %s", (sale_id,))
                cursor.execute("DELETE FROM sales WHERE branch_id = %s", (branch_id,))
        
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({'success': True, 'message': f'Sales history reset successfully ({reset_type})'})
    except Exception as e:
        db.rollback()
        cursor.close()
        db.close()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)