from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '012585'
app.config['MYSQL_DB'] = 'anime_db'

mysql = MySQL(app)

# Homepage
@app.route('/')
def index():
    return render_template('index.html')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        cur.close()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

# User Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('You must be logged in to view your profile.')
        return redirect(url_for('login'))
    
    # Fetch the user data from the database
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    cur.close()

    return render_template('profile.html', user=user_data)


# Browse Anime List
@app.route('/anime')
def anime_list():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM anime")
    anime_data = cur.fetchall()
    cur.close()
    return render_template('anime_list.html', anime=anime_data)

# Search Anime
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM anime WHERE title LIKE %s OR genre LIKE %s", (f"%{query}%", f"%{query}%"))
        results = cur.fetchall()
        cur.close()
        return render_template('search_results.html', results=results)
    return render_template('search.html')

# Rate Anime
@app.route('/rate/<int:anime_id>', methods=['POST'])
def rate(anime_id):
    if 'user_id' not in session:
        flash('Please log in to rate anime.')
        return redirect(url_for('login'))
    user_id = session['user_id']
    rating = request.form['rating']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO user_ratings (user_id, anime_id, rating) VALUES (%s, %s, %s)", (user_id, anime_id, rating))
    mysql.connection.commit()
    cur.close()
    flash('Rating submitted!')
    return redirect(url_for('anime_list'))

# Add Anime to Favorites
@app.route('/favorite/<int:anime_id>', methods=['POST'])
def favorite(anime_id):
    if 'user_id' not in session:
        flash('Please log in to add to favorites.')
        return redirect(url_for('login'))
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO favorites (user_id, anime_id) VALUES (%s, %s)", (user_id, anime_id))
    mysql.connection.commit()
    cur.close()
    flash('Added to favorites!')
    return redirect(url_for('anime_list'))

# View Anime Details
@app.route('/anime/<int:anime_id>')
def anime_details(anime_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM anime WHERE id = %s", (anime_id,))
    anime = cur.fetchone()
    cur.close()
    return render_template('anime_details.html', anime=anime)

# Admin Panel (Add/Edit/Delete Anime)
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user_id' not in session:
        flash('Please log in as admin.')
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        genre = request.form['genre']
        rating = request.form['rating']
        synopsis = request.form['synopsis']
        episodes = request.form['episodes']
        release_year = request.form['release_year']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO anime (title, genre, rating, synopsis, episodes, release_year) VALUES (%s, %s, %s, %s, %s, %s)",
                    (title, genre, rating, synopsis, episodes, release_year))
        mysql.connection.commit()
        cur.close()
        flash('Anime added successfully!')
        return redirect(url_for('admin'))
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)