# Palette Share

A Flask-based web application for sharing and discovering large color palettes organized by categories. Perfect for designers, developers, and anyone working with extensive color systems.

## Features

- **User Authentication**: Secure registration and login system
- **Create Palettes**: Build large color palettes with unlimited colors
- **Organize by Categories**: Group colors into meaningful categories within each palette
- **Multiple Color Formats**: Input colors in HEX, RGB, or HSL formats - all formats are automatically stored and displayed
- **Public/Private Palettes**: Choose to share your palettes publicly or keep them private
- **Browse & Search**: Discover palettes shared by the community with search and filter options
- **Rich Color Information**: Store and view colors in HEX, RGB, and HSL formats with optional color names
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Tech Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite
- **Authentication**: Flask-Login with password hashing
- **Frontend**: HTML5, CSS3, Jinja2 templates

## Installation

1. Clone the repository:
```bash
git clone https://github.com/LazerThings/palette-share.git
cd palette-share
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python init_db.py
```

5. Set a secret key (optional, for production):
```bash
export SECRET_KEY='your-secret-key-here'
```

## Usage

### Development Mode

1. Start the application:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Register a new account and start creating palettes!

### Production Mode (with Gunicorn)

1. Make sure the database is initialized:
```bash
python init_db.py
```

2. Start Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Note**: The database is automatically initialized on first run if it doesn't exist, but you can also run `init_db.py` manually to ensure proper setup.

## Application Structure

```
palette-share/
├── app.py                 # Main Flask application
├── init_db.py            # Database initialization script
├── requirements.txt       # Python dependencies
├── palettes.db           # SQLite database (created automatically)
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── browse.html
│   ├── my_palettes.html
│   ├── new_palette.html
│   ├── view_palette.html
│   └── edit_palette.html
└── static/               # Static files
    └── style.css         # CSS styling
```

## Database Schema

### Users
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `password_hash`: Hashed password
- `created_at`: Registration timestamp

### Palettes
- `id`: Primary key
- `user_id`: Foreign key to users
- `name`: Palette name
- `description`: Optional description
- `is_public`: Public/private flag
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Categories
- `id`: Primary key
- `palette_id`: Foreign key to palettes
- `name`: Category name

### Colors
- `id`: Primary key
- `category_id`: Foreign key to categories
- `hex_code`: Hex color code (e.g., #FF5733)
- `r`, `g`, `b`: RGB color values (0-255)
- `h`, `s`, `l`: HSL color values (H: 0-360, S: 0-100, L: 0-100)
- `name`: Optional color name
- `position`: Order within category

## Features Walkthrough

### Creating a Palette
1. Log in to your account
2. Click "Create Palette" in the navigation bar
3. Enter a name and optional description
4. Choose whether to make it public
5. Click "Create Palette"

### Adding Categories and Colors
1. After creating a palette, you'll be taken to the edit page
2. Add categories using the "Add Category" form
3. Within each category, add colors in any of these formats:
   - **HEX**: `#FF5733` or `FF5733`
   - **RGB**: `255,87,51` or `rgb(255, 87, 51)`
   - **HSL**: `9,100,60` or `hsl(9, 100%, 60%)`
   - Optional color name
4. Colors are displayed with visual swatches showing all three formats (HEX, RGB, HSL)

### Browsing Palettes
1. Click "Browse" in the navigation bar
2. Use the search bar to find palettes by name or description
3. Filter by username to see palettes from specific users
4. Click on any palette to view its full details

## Security Features

- Password hashing using Werkzeug's security utilities
- Session management with Flask-Login
- User authentication required for creating/editing palettes
- Permission checks to prevent unauthorized access
- CSRF protection through Flask's session management

## Development

To run in development mode with debug enabled:

```bash
python app.py
```

For production deployment:
- Set `app.debug = False` in app.py
- Use a production WSGI server (e.g., Gunicorn)
- Set a secure SECRET_KEY environment variable
- Use a production database (PostgreSQL recommended)

## License

This project is licensed under the Open Source Permissive License (OSPL). See the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.
