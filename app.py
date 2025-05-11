from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_mysqldb import MySQL
from datetime import datetime
from datetime import date
from werkzeug.utils import secure_filename
from MySQLdb.cursors import DictCursor

# from flask_wtf.csrf import CSRFProtect
import os
from dotenv import load_dotenv
from flask import jsonify

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.secret_key = "Project370-key"
ADMIN_SECRET_KEY ='ADMIN_SECRET_KEY'
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '012585')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'animeflix')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, role):
        self.id = id
        self.username = username
        self.email = email
        self.role = role

    def is_admin(self):
        return self.role == 'admin'

@login_manager.user_loader
def load_user(user_id):
    print(f"DEBUG: Loading user {user_id}")  # Important debug line
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        if user:
            return User(user['id'], user['username'], user['email'], user['role'])
        return None
    except Exception as e:
        print(f"DEBUG: Error loaing user: {e}")
        return None

def get_db_data(query, params=None):
    """Helper function to execute queries and fetch results"""
    cur = mysql.connection.cursor()
    cur.execute(query, params or ())
    result = cur.fetchall()
    cur.close()
    return result

@app.route('/')
def home():
    trending_anime = get_db_data("SELECT * FROM anime WHERE is_trending = TRUE LIMIT 3")
    top_searches = get_db_data("SELECT term FROM top_searches ORDER BY id LIMIT 10")
    trending_posts = get_db_data("SELECT * FROM trending_posts ORDER BY id LIMIT 2")
    
    return render_template('index.html',
                        trending_anime=trending_anime,
                        top_searches=top_searches,
                        trending_posts=trending_posts)



# Add this temporary route to your Flask app
@app.route('/test-api')
def test_api():
    return jsonify({"message": "API is working", "status": "success"})


@app.route('/api/minimal')
def minimal_api():
    return jsonify({"data": [1, 2, 3]})

@app.route('/minimal-test')
def minimal_test():
    return """
    <html>
    <body>
        <div id="data-container"></div>
        <script>
            fetch('/api/minimal')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('data-container').innerHTML = 
                        JSON.stringify(data);
                    console.log("Data loaded:", data);
                });
        </script>
    </body>
    </html>
    """

@app.route('/movies')
def movies():
    movies = get_db_data("SELECT * FROM anime WHERE type = 'movie'")
    return render_template('movies.html', movies=movies)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                   (username, email, hashed_pw, 'user'))
        mysql.connection.commit()
        cur.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    print("\n--- NEW LOGIN ATTEMPT ---")  # Debug separator
    
    if request.method == 'POST':
        print("DEBUG: Request form data:", dict(request.form))  # Show all form data
        
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        print(f"DEBUG: Email: {email}, Password: {password}")

        if not email or not password:
            print("DEBUG: Missing email or password")
            flash('Both email and password are required', 'danger')
            return redirect(url_for('login'))

        try:
            # Verify database connection
            print("DEBUG: Testing DB connection...")
            cur = mysql.connection.cursor()
            cur.execute("SELECT 1")
            cur.close()
            
            # Get user
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            cur.close()
            
            print("DEBUG: User query result:", user)
            
            if user:
                print("DEBUG: User exists, checking password...")
                if bcrypt.check_password_hash(user['password'], password):
                    print("DEBUG: Password correct!")
                    user_obj = User(user['id'], user['username'], user['email'], user.get('role', 'user'))
                    print("DEBUG: Attempting login...")
                    login_user(user_obj)
                    print("DEBUG: Current user after login:", current_user)
                    
                    # flash('Logged in successfully!', 'success')
                    
                    print("DEBUG: Should be redirecting to profile now")
                    
                    # flash('Login successful', 'success')
                    
                    
                    next_page = request.args.get('next') or url_for('profile')
                    print(f"DEBUG: Redirecting to {next_page}")
                    return redirect(next_page)
                else:
                    print("DEBUG: Password incorrect")
            else:
                print("DEBUG: No user found with that email")
            
            flash('Invalid email or password', 'danger')
            
        except Exception as e:
            print(f"DEBUG: ERROR: {str(e)}")
            flash('An error occurred during login', 'danger')

    return render_template('login.html')



@app.route('/test-login-flow', methods=['GET', 'POST'])
def test_login_flow():
    """Test route that bypasses all potential issues"""
    if request.method == 'POST':
        # Hardcoded successful login
        user_obj = User(id=1, username='testuser', email='test@test.com', role='user')
        login_user(user_obj)
        print("DEBUG: User should be logged in now")
        return redirect(url_for('profile'))
    
    return '''
    <form method="POST">
        <button type="submit">Test Login</button>
    </form>
    <p>After clicking, check:</p>
    <ol>
        <li>Flask console for debug message</li>
        <li>Browser network tab for 302 redirect</li>
        <li>Whether profile page loads</li>
    </ol>
    '''

@app.route('/test-db')
def test_db():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        return f"Database connection working: {result}"
    except Exception as e:
        return f"Database error: {str(e)}"


# @app.route('/simple-login', methods=['GET', 'POST'])
# def simple_login():
#     if request.method == 'POST':
#         email = request.form.get('email')
#         password = request.form.get('password')
        
#         # Hardcoded test credentials
#         if email == "test@test.com" and password == "test123":
#             user_obj = User(1, "testuser", "test@test.com", "user")
#             login_user(user_obj)
#             return redirect(url_for('profile'))
        
#         return "Invalid credentials"
    
#     return '''
#     <form method="POST">
#         <input type="email" name="email" placeholder="Email">
#         <input type="password" name="password" placeholder="Password">
#         <button type="submit">Login</button>
#     </form>
#     '''

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', username=current_user.username, role=current_user.role)


@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        bio = request.form.get('bio', '')

        avatar_filename = None

        # Handle avatar
        file = request.files.get('avatar')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            avatar_filename = filename  # will update only if uploaded

        # SQL Update query
        cursor = mysql.connection.cursor()
        if avatar_filename:
            cursor.execute("""
                UPDATE users SET username = %s, email = %s, bio = %s, avatar = %s WHERE id = %s
            """, (username, email, bio, avatar_filename, current_user.id))
        else:
            cursor.execute("""
                UPDATE users SET username = %s, email = %s, bio = %s WHERE id = %s
            """, (username, email, bio, current_user.id))

        mysql.connection.commit()
        cursor.close()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('edit_profile.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))



###watchlist###


# Add to watchlist
@app.route('/add_to_watchlist', methods=['POST'])
@login_required
def add_to_watchlist():
    if 'anime_id' not in request.form:
        flash('Invalid request', 'error')
        return redirect(request.referrer or url_for('home'))
    
    anime_id = request.form['anime_id']
    cur = mysql.connection.cursor()
    
    try:
        # Check if already in watchlist first
        cur.execute("SELECT 1 FROM watchlist WHERE user_id = %s AND anime_id = %s", 
                   (current_user.id, anime_id))
        if cur.fetchone():
            flash('This anime is already in your watchlist', 'info')
        else:
            # Add to watchlist if not already there
            cur.execute("INSERT INTO watchlist (user_id, anime_id) VALUES (%s, %s)", 
                       (current_user.id, anime_id))
            mysql.connection.commit()
            flash('Added to watchlist!', 'success')
            
    except Exception as e:
        mysql.connection.rollback()
        flash('Error updating your watchlist', 'error')
        print(f"Database error: {e}")
    finally:
        cur.close()
    
    return redirect(request.referrer or url_for('home'))

@app.route('/watchlist')
@login_required
def watchlist():
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT a.id, a.title, a.image 
            FROM anime a
            JOIN watchlist w ON a.id = w.anime_id
            WHERE w.user_id = %s
            ORDER BY a.title
        """, (current_user.id,))
        watchlist_items = cur.fetchall()
        
        if not watchlist_items:
            flash('Your watchlist is empty', 'info')
            
    except Exception as e:
        flash('Error loading your watchlist', 'error')
        print(f"Database error: {e}")
        watchlist_items = []
    finally:
        cur.close()
    
    return render_template('watchlist.html', watchlist=watchlist_items)


# Remove from watchlist
@app.route('/remove_from_watchlist/<anime_id>', methods=['POST'])
@login_required
def remove_from_watchlist(anime_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM watchlist WHERE user_id = %s AND anime_id = %s", 
               (current_user.id, anime_id))
    mysql.connection.commit()
    cur.close()
    
    flash('Removed from watchlist', 'success')
    return redirect(url_for('watchlist'))


@app.route('/tv-series')
def tv_series():
    series = get_db_data("SELECT * FROM anime WHERE type = 'tv_series'")
    return render_template('tv_series.html', series=series)

@app.route('/most-popular')
def most_popular():
    popular = get_db_data("SELECT * FROM anime WHERE is_popular = TRUE")
    return render_template('most_popular.html', popular=popular)

@app.route('/top-airing')
def top_airing():
    airing = get_db_data("SELECT * FROM anime WHERE is_top_airing = TRUE")
    return render_template('top_airing.html', airing=airing)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('home'))
    
    results = get_db_data("SELECT * FROM anime WHERE title LIKE %s", 
                         (f"%{query}%",))
    
    return render_template('search_results.html', 
                         results=results, 
                         query=query)

@app.route('/anime/<int:anime_id>')
def anime_detail(anime_id):
    anime = get_db_data("SELECT * FROM anime WHERE id = %s", (anime_id,))
    if not anime:
        flash('Anime not found', 'danger')
        return redirect(url_for('home'))
    return render_template('anime_detail.html', anime=anime[0])


# @app.route('/watch/<anime_id>')
# @app.route('/watch/<anime_id>/<int:episode>')
# def watch(anime_id, episode=1):
#     # In a real app, you would fetch the anime and episode data from your database
#     anime = {
#         'id': anime_id,
#         'title': title,
#         'episode': episode,
#         'video_url': "/static/videos/sample.mp4"  # Sample video path
#     }
#     return render_template('watch.html', anime=anime)

# Admin Panel (Add/Edit/Delete Anime)

# @app.route('/events')
# def events():
#     upcoming_events = get_db_data("SELECT * FROM anime_events WHERE event_date >= CURDATE() ORDER BY event_date")
#     past_events = get_db_data("SELECT * FROM anime_events WHERE event_date < CURDATE() ORDER BY event_date DESC")
#     return render_template('events/events.html', 
#                          upcoming_events=upcoming_events,
#                          past_events=past_events)

# @app.route('/event/<int:event_id>')
# def event_detail(event_id):
#     event = get_db_data("SELECT * FROM anime_events WHERE id = %s", (event_id,))
#     if not event:
#         flash('Event not found', 'danger')
#         return redirect(url_for('events'))
#     return render_template('event_detail.html', event=event[0])




####manga section####


@app.route('/manga')
def manga_list():
    cur = mysql.connection.cursor(DictCursor)
    
    query = """
        SELECT 
            m.id,
            m.title,
            m.cover_image,
            m.description,
            m.genre,
            m.status,
            m.chapters,
            m.anime_id,
            a.title AS anime_title
        FROM manga m
        LEFT JOIN anime a ON m.anime_id = a.id
        ORDER BY m.title
    """
    cur.execute(query)
    results = cur.fetchall()
    cur.close()

    manga_data = []
    for row in results:
        # Handle NULL values with defaults
        anime_data = None
        if row['anime_id'] is not None:  # Explicit None check
            anime_data = {
                'id': row['anime_id'],
                'title': row['anime_title'] or "Untitled Anime"  # Fallback if title is None
            }
        
        manga_entry = {
            'id': row['id'],
            'title': row['title'],
            'cover_image': row['cover_image'] or "/static/images/default_cover.jpg",  # Fallback image
            'description': row['description'] or "No description available",
            'genre': row['genre'] or "Genre not specified",
            'status': row['status'] or "unknown",
            'chapters': row['chapters'] or 0,
            'anime': anime_data  # This will be None if no anime_id
        }
        manga_data.append(manga_entry)

    return render_template('manga_list.html', mangas=manga_data)

@app.route('/manga/<int:manga_id>')
def manga_page(manga_id):
    cur = mysql.connection.cursor()

    # Fetch complete manga details
    query = """
        SELECT 
            m.id,
            m.title,
            m.cover_image,
            m.description,
            m.genre,
            m.status,
            m.chapters,
            m.created_at,
            m.anime_id,
            a.title AS anime_title,
            a.image AS anime_image
        FROM manga m
        LEFT JOIN anime a ON m.anime_id = a.id
        WHERE m.id = %s
    """
    cur.execute(query, (manga_id,))
    manga = cur.fetchone()
    cur.close()

    if not manga:
        return "Manga not found", 404

    # Prepare detailed manga data
    manga_details = {
        'id': manga[0],
        'title': manga[1],
        'cover_image': manga[2],
        'description': manga[3],
        'genre': manga[4],
        'status': manga[5],
        'chapters': manga[6],
        'created_at': manga[7],
        'anime': {
            'id': manga[8],
            'title': manga[9],
            'image': manga[10]
        } if manga[8] else None
    }

    return render_template('manga_page.html', manga=manga_details)

    # Fetch manga details with associated anime info
    query = """
        SELECT 
            manga.id,
            manga.title,
            manga.image,
            manga.description,
            anime.id AS anime_id,
            anime.title AS anime_title
        FROM manga
        LEFT JOIN anime ON manga.anime_id = anime.id
        WHERE manga.id = %s
    """
    cur.execute(query, (manga_id,))
    manga = cur.fetchone()
    cur.close()

    # Check if manga exists
    if not manga:
        return "Manga not found", 404

    # Prepare data for template
    manga_data = {
        'id': manga[0],
        'title': manga[1],
        'image': manga[2],
        'description': manga[3],
        'anime': {
            'id': manga[4],
            'title': manga[5]
        } if manga[4] else None
    }

    return render_template('manga_page.html', manga=manga_data)









####merchandise section####



@app.route('/merch')
@login_required
def merchandise():
    items = get_db_data("""
        SELECT m.*, u.username 
        FROM merchandise m
        JOIN users u ON m.user_id = u.id
        WHERE m.status = 'available'
        ORDER BY m.created_at DESC
    """)
    return render_template('merch/index.html', items=items)

@app.route('/merch/add', methods=['GET', 'POST'])
@login_required
def add_merchandise():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        category = request.form['category']
        
        # Handle file upload
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                filename = secure_filename(image.filename)
                image_path = os.path.join('static/uploads/merch', filename)
                image.save(os.path.join(app.root_path, image_path))
                image_url = url_for('static', filename=f'uploads/merch/{filename}')
            else:
                image_url = None
        else:
            image_url = None
        
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO merchandise 
            (user_id, title, description, price, image_url, category, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'available')
        """, (current_user.id, title, description, price, image_url, category))
        mysql.connection.commit()
        cur.close()
        
        flash('Your merchandise has been listed!', 'success')
        return redirect(url_for('merchandise'))
    
    return render_template('merch/add.html')

@app.route('/merch/purchase/<int:item_id>', methods=['POST'])
@login_required
def purchase_merchandise(item_id):
    cur = mysql.connection.cursor()
    
    # Verify item exists and is available
    cur.execute("""
        SELECT * FROM merchandise 
        WHERE id = %s AND status = 'available'
    """, (item_id,))
    item = cur.fetchone()
    
    if not item:
        flash('Item not available', 'danger')
        return redirect(url_for('merchandise'))
    
    # Update item status
    cur.execute("""
        UPDATE merchandise 
        SET status = 'sold'
        WHERE id = %s
    """, (item_id,))
    mysql.connection.commit()
    cur.close()
    
    flash('Purchase successful! The seller will contact you.', 'success')
    return redirect(url_for('merchandise'))



####### ADMIN SECTION #######




@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        # Simple hardcoded auth (replace with proper auth in production)
        if request.form['username'] == 'admin' and request.form['password'] == 'securepassword':
            session['admin_logged_in'] = True
            return redirect(url_for('anime_list'))
        flash('Invalid credentials', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))


@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')


@app.route('/admin/anime')
def anime_list():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, title, type, is_trending, is_popular FROM anime ORDER BY created_at DESC")
    anime_list = cur.fetchall()
    cur.close()
    return render_template('anime_list.html', anime_list=anime_list)

@app.route('/admin/anime/add', methods=['GET', 'POST'])
def add_anime():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        try:
            data = {
                'id': request.form['id'],
                'title': request.form['title'],
                'image': request.form['image'],
                'description': request.form['description'],
                'type': request.form['type'],
                'is_trending': 1 if request.form.get('is_trending') else 0,
                'is_popular': 1 if request.form.get('is_popular') else 0,
                'is_top_airing': 1 if request.form.get('is_top_airing') else 0
            }

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO anime 
                (id, title, image, description, type, is_trending, is_popular, is_top_airing)
                VALUES (%(id)s, %(title)s, %(image)s, %(description)s, %(type)s, 
                        %(is_trending)s, %(is_popular)s, %(is_top_airing)s)
            """, data)
            mysql.connection.commit()
            cur.close()
            
            flash('Anime added successfully!', 'success')
            return redirect(url_for('anime_list'))
            
        except Exception as e:
            flash(f'Error adding anime: {str(e)}', 'danger')

    return render_template('add_anime.html')

@app.route('/admin/anime/delete/<anime_id>')
def delete_anime(anime_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM anime WHERE id = %s", (anime_id,))
        mysql.connection.commit()
        cur.close()
        flash('Anime deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting anime: {str(e)}', 'danger')
    
    return redirect(url_for('anime_list'))
def initialize_database():
    """Populate the database with initial data"""
    cur = mysql.connection.cursor()
    
    # Check if database is already populated
    cur.execute("SELECT COUNT(*) as count FROM anime")
    if cur.fetchone()['count'] > 0:
        cur.close()
        return
    




@app.route('/admin/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        date = request.form.get('date')
        location = request.form.get('location')
        
        # Handle file upload
        if 'image' not in request.files:
            flash('No image uploaded', 'error')
            return redirect(request.url)
        
        file = request.files['image']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Save to database
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO anime_events (title, description, image_url, event_date, location, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (title, description, filename, date, location, datetime.now()))
            mysql.connection.commit()
            cur.close()
            
            flash('Event created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        
    return render_template('create_event.html')

@app.route('/events')
def events():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, title, description, image_url, event_date, location
        FROM anime_events
        WHERE event_date >= %s
        ORDER BY event_date ASC
    """, (date.today(),))

    rows = cur.fetchall()
    cur.close()

    events = []
    for row in rows:
        events.append({
            'id': row['id'],
            'title': row['title'],
            'description': row['description'],
            'image_path': row['image_url'],
            'date': row['event_date'],
            'location': row['location'],
        })

    return render_template("events/events.html", events=events)


    
    # Insert sample data
    # anime_data = [
    #     ('1', 'Bleach', '/static/images/placeholder1.jpg', 'Description for Wind Breaker Season 2', 'tv_series', True, False, True, '2023'),
    #     ('2', 'Chainsaw Man', '/static/images/placeholder2.jpg', 'Description for Solo Leveling Season 2', 'tv_series', True, False, True, '2023'),
    #     ('3', 'Jujutsu Kaisen', '/static/images/placeholder3.jpg', 'Description for One Piece', 'tv_series', True, True, False, '2023'),
    #     ('4', 'Demon Slayer: Mugen Train', '/static/images/placeholder4.jpg', 'Description for Demon Slayer: Mugen Train', 'movie', False, False, False, '2023'),
    #     ('5', 'Your Name', '/static/images/placeholder5.jpg', 'Description for Your Name', 'movie', False, False, False, '2023'),
    #     ('6', 'Attack on Titan', '/static/images/placeholder6.jpg', 'Description for Attack on Titan', 'tv_series', False, True, False, '2023'),
    #     ('7', 'Jujutsu Kaisen', '/static/images/placeholder7.jpg', 'Description for Jujutsu Kaisen', 'tv_series', False, False, True, '2023')
    # ]
    
    # cur.executemany("""
    #     INSERT INTO anime (id, title, image, description, type, is_trending, is_popular, is_top_airing, release_year)
    #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    # """, anime_data)
    
    # Insert top searches
    searches = [
        'Wind Breaker Season 2', 'Solo Leveling Season 2', 'Aris',
        'One Piece', 'The Beginning After the End', 'Please Put Them On, Takamine-san',
        'Devil May Cry', 'Solo Leveling', 'Sword of the Demon Hunter',
        'Wind Breaker', 'Attack on Titan'
    ]
    
    for term in searches:
        cur.execute("INSERT INTO top_searches (term) VALUES (%s)", (term,))
    
    # Insert trending posts
    posts = [
        ('1', 'Chat I\'m soo close to angelfish', 'General', '2 hours ago', 33),
        ('2', 'Ok guys crunchyroll vote have started just don\'t let solo leveling win', 'General', '12 hours ago', 187)
    ]
    
    cur.executemany("""
        INSERT INTO trending_posts (id, title, category, time_posted, comment_count)
        VALUES (%s, %s, %s, %s, %s)
    """, posts)
    
    mysql.connection.commit()
    cur.close()

if __name__ == '__main__':
    with app.app_context():
        initialize_database()
        app.run(debug=True)
