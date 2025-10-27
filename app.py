import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

DATABASE = 'palettes.db'

def get_db():
    """Get database connection"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize the database with tables"""
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS palettes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            is_public INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            palette_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (palette_id) REFERENCES palettes (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS colors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            hex_code TEXT NOT NULL,
            name TEXT,
            position INTEGER DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_palettes_user ON palettes(user_id);
        CREATE INDEX IF NOT EXISTS idx_categories_palette ON categories(palette_id);
        CREATE INDEX IF NOT EXISTS idx_colors_category ON colors(category_id);
    ''')
    db.commit()
    db.close()

class User(UserMixin):
    """User class for Flask-Login"""
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    db = get_db()
    user_data = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    db.close()
    if user_data:
        return User(user_data['id'], user_data['username'], user_data['email'])
    return None

@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@app.route('/browse')
def browse():
    """Browse all public palettes"""
    db = get_db()

    # Get search and filter parameters
    search = request.args.get('search', '').strip()
    username_filter = request.args.get('username', '').strip()

    query = '''
        SELECT p.*, u.username,
               COUNT(DISTINCT c.id) as category_count,
               COUNT(DISTINCT col.id) as color_count
        FROM palettes p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN categories c ON p.id = c.palette_id
        LEFT JOIN colors col ON c.id = col.category_id
        WHERE p.is_public = 1
    '''
    params = []

    if search:
        query += ' AND (p.name LIKE ? OR p.description LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param])

    if username_filter:
        query += ' AND u.username LIKE ?'
        params.append(f'%{username_filter}%')

    query += ' GROUP BY p.id ORDER BY p.created_at DESC'

    palettes = db.execute(query, params).fetchall()
    db.close()

    return render_template('browse.html', palettes=palettes, search=search, username_filter=username_filter)

@app.route('/my-palettes')
@login_required
def my_palettes():
    """View current user's palettes"""
    db = get_db()
    palettes = db.execute('''
        SELECT p.*, COUNT(DISTINCT c.id) as category_count,
               COUNT(DISTINCT col.id) as color_count
        FROM palettes p
        LEFT JOIN categories c ON p.id = c.palette_id
        LEFT JOIN colors col ON c.id = col.category_id
        WHERE p.user_id = ?
        GROUP BY p.id
        ORDER BY p.created_at DESC
    ''', (current_user.id,)).fetchall()
    db.close()
    return render_template('my_palettes.html', palettes=palettes)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('my_palettes'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('register'))

        db = get_db()

        # Check if username or email already exists
        existing_user = db.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            (username, email)
        ).fetchone()

        if existing_user:
            flash('Username or email already exists', 'error')
            db.close()
            return redirect(url_for('register'))

        # Create user
        password_hash = generate_password_hash(password)
        cursor = db.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        user_id = cursor.lastrowid
        db.commit()
        db.close()

        # Log in the user
        user = User(user_id, username, email)
        login_user(user)

        flash('Registration successful! Welcome!', 'success')
        return redirect(url_for('my_palettes'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('my_palettes'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('login'))

        db = get_db()
        user_data = db.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?',
            (username, username)
        ).fetchone()
        db.close()

        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data['id'], user_data['username'], user_data['email'])
            login_user(user, remember=True)

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('my_palettes'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@app.route('/palette/<int:palette_id>')
def view_palette(palette_id):
    """View a specific palette with all categories and colors"""
    db = get_db()

    palette = db.execute('''
        SELECT p.*, u.username
        FROM palettes p
        JOIN users u ON p.user_id = u.id
        WHERE p.id = ?
    ''', (palette_id,)).fetchone()

    if not palette:
        flash('Palette not found', 'error')
        return redirect(url_for('browse'))

    # Check if user has permission to view
    if not palette['is_public']:
        if not current_user.is_authenticated or current_user.id != palette['user_id']:
            flash('You do not have permission to view this palette', 'error')
            return redirect(url_for('browse'))

    categories = db.execute('''
        SELECT c.*, COUNT(col.id) as color_count
        FROM categories c
        LEFT JOIN colors col ON c.id = col.category_id
        WHERE c.palette_id = ?
        GROUP BY c.id
        ORDER BY c.id
    ''', (palette_id,)).fetchall()

    # Get colors for each category
    category_colors = {}
    for category in categories:
        colors = db.execute('''
            SELECT * FROM colors
            WHERE category_id = ?
            ORDER BY position, id
        ''', (category['id'],)).fetchall()
        category_colors[category['id']] = colors

    db.close()
    return render_template('view_palette.html', palette=palette, categories=categories, category_colors=category_colors)

@app.route('/palette/new', methods=['GET', 'POST'])
@login_required
def new_palette():
    """Create a new palette"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        is_public = 1 if request.form.get('is_public') == 'on' else 0

        if not name:
            flash('Palette name is required', 'error')
            return redirect(url_for('new_palette'))

        db = get_db()
        cursor = db.execute(
            'INSERT INTO palettes (user_id, name, description, is_public) VALUES (?, ?, ?, ?)',
            (current_user.id, name, description, is_public)
        )
        palette_id = cursor.lastrowid
        db.commit()
        db.close()

        flash('Palette created successfully!', 'success')
        return redirect(url_for('edit_palette', palette_id=palette_id))

    return render_template('new_palette.html')

@app.route('/palette/<int:palette_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_palette(palette_id):
    """Edit a palette's categories and colors"""
    db = get_db()

    palette = db.execute('SELECT * FROM palettes WHERE id = ?', (palette_id,)).fetchone()

    if not palette:
        flash('Palette not found', 'error')
        return redirect(url_for('my_palettes'))

    # Check if user owns this palette
    if palette['user_id'] != current_user.id:
        flash('You do not have permission to edit this palette', 'error')
        return redirect(url_for('view_palette', palette_id=palette_id))

    if request.method == 'POST':
        # Update palette info
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        is_public = 1 if request.form.get('is_public') == 'on' else 0

        if not name:
            flash('Palette name is required', 'error')
        else:
            db.execute(
                'UPDATE palettes SET name = ?, description = ?, is_public = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (name, description, is_public, palette_id)
            )
            db.commit()
            flash('Palette updated successfully!', 'success')

    categories = db.execute('''
        SELECT c.*, COUNT(col.id) as color_count
        FROM categories c
        LEFT JOIN colors col ON c.id = col.category_id
        WHERE c.palette_id = ?
        GROUP BY c.id
        ORDER BY c.id
    ''', (palette_id,)).fetchall()

    category_colors = {}
    for category in categories:
        colors = db.execute('''
            SELECT * FROM colors
            WHERE category_id = ?
            ORDER BY position, id
        ''', (category['id'],)).fetchall()
        category_colors[category['id']] = colors

    db.close()
    return render_template('edit_palette.html', palette=palette, categories=categories, category_colors=category_colors)

@app.route('/palette/<int:palette_id>/category/add', methods=['POST'])
@login_required
def add_category(palette_id):
    """Add a category to a palette"""
    db = get_db()
    palette = db.execute('SELECT user_id FROM palettes WHERE id = ?', (palette_id,)).fetchone()

    if not palette or palette['user_id'] != current_user.id:
        flash('You do not have permission to edit this palette', 'error')
        db.close()
        return redirect(url_for('my_palettes'))

    category_name = request.form.get('category_name', '').strip()

    if not category_name:
        flash('Category name is required', 'error')
        db.close()
        return redirect(url_for('edit_palette', palette_id=palette_id))

    db.execute(
        'INSERT INTO categories (palette_id, name) VALUES (?, ?)',
        (palette_id, category_name)
    )
    db.commit()
    db.close()

    flash('Category added successfully!', 'success')
    return redirect(url_for('edit_palette', palette_id=palette_id))

@app.route('/category/<int:category_id>/color/add', methods=['POST'])
@login_required
def add_color(category_id):
    """Add a color to a category"""
    hex_code = request.form.get('hex_code', '').strip()
    color_name = request.form.get('color_name', '').strip()

    # Get palette_id and check ownership
    db = get_db()
    category = db.execute('''
        SELECT c.palette_id, p.user_id
        FROM categories c
        JOIN palettes p ON c.palette_id = p.id
        WHERE c.id = ?
    ''', (category_id,)).fetchone()

    if not category:
        flash('Category not found', 'error')
        db.close()
        return redirect(url_for('my_palettes'))

    if category['user_id'] != current_user.id:
        flash('You do not have permission to edit this palette', 'error')
        db.close()
        return redirect(url_for('my_palettes'))

    palette_id = category['palette_id']

    if not hex_code:
        flash('Hex code is required', 'error')
        db.close()
        return redirect(url_for('edit_palette', palette_id=palette_id))

    # Ensure hex code starts with #
    if not hex_code.startswith('#'):
        hex_code = '#' + hex_code

    db.execute(
        'INSERT INTO colors (category_id, hex_code, name) VALUES (?, ?, ?)',
        (category_id, hex_code, color_name)
    )
    db.commit()
    db.close()

    flash('Color added successfully!', 'success')
    return redirect(url_for('edit_palette', palette_id=palette_id))

@app.route('/palette/<int:palette_id>/delete', methods=['POST'])
@login_required
def delete_palette(palette_id):
    """Delete a palette"""
    db = get_db()
    palette = db.execute('SELECT user_id FROM palettes WHERE id = ?', (palette_id,)).fetchone()

    if not palette or palette['user_id'] != current_user.id:
        flash('You do not have permission to delete this palette', 'error')
        db.close()
        return redirect(url_for('my_palettes'))

    db.execute('DELETE FROM palettes WHERE id = ?', (palette_id,))
    db.commit()
    db.close()

    flash('Palette deleted successfully!', 'success')
    return redirect(url_for('my_palettes'))

@app.route('/category/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """Delete a category"""
    db = get_db()
    category = db.execute('''
        SELECT c.palette_id, p.user_id
        FROM categories c
        JOIN palettes p ON c.palette_id = p.id
        WHERE c.id = ?
    ''', (category_id,)).fetchone()

    if category and category['user_id'] == current_user.id:
        palette_id = category['palette_id']
        db.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        db.commit()
        flash('Category deleted successfully!', 'success')
    else:
        flash('Category not found or permission denied', 'error')
        palette_id = None

    db.close()

    if palette_id:
        return redirect(url_for('edit_palette', palette_id=palette_id))
    return redirect(url_for('my_palettes'))

@app.route('/color/<int:color_id>/delete', methods=['POST'])
@login_required
def delete_color(color_id):
    """Delete a color"""
    db = get_db()
    color = db.execute('''
        SELECT c.palette_id, p.user_id
        FROM colors col
        JOIN categories c ON col.category_id = c.id
        JOIN palettes p ON c.palette_id = p.id
        WHERE col.id = ?
    ''', (color_id,)).fetchone()

    if color and color['user_id'] == current_user.id:
        palette_id = color['palette_id']
        db.execute('DELETE FROM colors WHERE id = ?', (color_id,))
        db.commit()
        flash('Color deleted successfully!', 'success')
    else:
        flash('Color not found or permission denied', 'error')
        palette_id = None

    db.close()

    if palette_id:
        return redirect(url_for('edit_palette', palette_id=palette_id))
    return redirect(url_for('my_palettes'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
