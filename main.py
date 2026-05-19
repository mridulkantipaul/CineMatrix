from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import pandas as pd
import random

# 1. Initialize the Flask App
app = Flask(__name__)
app.secret_key = 'super_secret_cinematch_key' # Required for user sessions!

# ==========================================
# 💾 DATABASE SETUP
# ==========================================
# TRICK: We changed the name to cinematch_v2.db to force a completely fresh database!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cinematch_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 1. Old Table 
class SavedMovie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_name = db.Column(db.String(100), nullable=False)

# 2. NEW TABLE: User Accounts
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    number = db.Column(db.String(20), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False) # <--- NEW AGE COLUMN
    password = db.Column(db.String(200), nullable=False) 
    role = db.Column(db.String(20), default='user')

# AUTOMATIC BUILDER: This makes sure the database builds itself!
with app.app_context():
    db.create_all()
# ==========================================

# ... (Keep your ML Model and CSV loading code here) ...

# 2. Load Models & Data
try:
    transform_model = pickle.load(open('tranform.pkl', 'rb'))
    nlp_model = pickle.load(open('nlp_model.pkl', 'rb'))
    print("✅ ML Models loaded successfully!")
except Exception as e:
    print(f"⚠️ Warning: Could not load .pkl files.")

# --- NEW: Load the CSV Data ---
try:
    movies_df = pd.read_csv('movies.csv')
    print("✅ Movie CSV Data loaded successfully!")
except Exception as e:
    movies_df = None
    print("⚠️ Warning: Could not load movies.csv file.")

# ... (Keep your @app.route('/') and other routes exactly the same below this line) ...
# 3. Route for the Homepage (Loads the HTML)
@app.route('/')
def home():
    return render_template('index.html')


# 4. Route for the Search/Recommend Button
@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        user_movie = request.form.get('movie')
        if not user_movie: return jsonify({"error": "No movie provided"}), 400
        if movies_df is None: return jsonify([{"title": "Error: Data not loaded", "poster_url": ""}])

        # Make search case-insensitive
        lower_titles = movies_df['title'].str.lower().tolist()
        user_movie_lower = user_movie.strip().lower()

        # Check if movie is in our database
        if user_movie_lower not in lower_titles:
            return jsonify({"error": f"Sorry, '{user_movie}' is not in our database yet!"})

        # --- NEW LOGIC: GRAB THE SEARCHED MOVIE ---
        searched_row = movies_df[movies_df['title'].str.lower() == user_movie_lower].iloc[0]
        movie_genre = searched_row['genre']
        
        # Create a special card for the movie they searched for
        searched_movie_dict = {
            "title": f"⭐ YOU SEARCHED: {searched_row['title']}",
            "poster_url": searched_row['poster_url']
        }

        # --- FIND RECOMMENDATIONS ---
        # Find 3 similar movies (same genre, exclude the searched one)
        similar_movies = movies_df[(movies_df['genre'] == movie_genre) & (movies_df['title'].str.lower() != user_movie_lower)]
        
        if similar_movies.empty:
            similar_movies = movies_df[movies_df['title'].str.lower() != user_movie_lower].sample(min(3, len(movies_df)-1))
        else:
            similar_movies = similar_movies.head(3) # Just get the top 3

        # Convert recommendations to a list
        recommendation_list = similar_movies[['title', 'poster_url']].to_dict('records')

        # --- COMBINE THEM ---
        # Put the searched movie at the very front of the list, followed by the 3 recommendations
        final_list = [searched_movie_dict] + recommendation_list
        
        return jsonify(final_list)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

import random # Add this import at the very top of your file!

# ... (Keep your existing code for @app.route('/') and @app.route('/recommend')) ...

# 5. Route for the "Surprise Me" Button
@app.route('/surprise', methods=['POST'])
def surprise():
    try:
        if movies_df is None:
            return jsonify([{"title": "Error: Data not loaded", "poster_url": ""}])
            
        # Pick one random movie row from the dataframe
        random_row = movies_df.sample(1).iloc[0]
        
        # Send both title and poster URL back as a dictionary
        movie_data = {
            "title": f"You should watch: {random_row['title']}",
            "poster_url": random_row['poster_url']
        }
        return jsonify([movie_data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 6. Route for the "Trending Now" Button
@app.route('/trending', methods=['POST'])
def trending():
    try:
        if movies_df is None:
            return jsonify([{"title": "Error: Data not loaded", "poster_url": ""}])
            
        # Sort by rating and grab the top 4
        top_movies = movies_df.sort_values(by='rating', ascending=False).head(4)
        
        # Convert those 4 rows into a list of dictionaries (containing title and poster_url)
        trending_list = top_movies[['title', 'poster_url']].to_dict('records')
        
        return jsonify(trending_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Keep this at the very bottom:
# if __name__ == '__main__':
#     app.run(debug=True, port=5000)

# 7. Route to Save a Movie to the Database
@app.route('/save_movie', methods=['POST'])
def save_movie():
    try:
        movie_to_save = request.form.get('movie')
        if not movie_to_save:
            return jsonify({"error": "No movie provided"}), 400

        # Create a new database entry and save it
        new_movie = SavedMovie(movie_name=movie_to_save)
        db.session.add(new_movie)
        db.session.commit() # This officially writes it to the database

        return jsonify({"success": f"'{movie_to_save}' was saved to your database!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 📺 NEW STREAMING UI ROUTES
# ==========================================

# Feeds the "Trending", "Action", and "SciFi" rows on the homepage
@app.route('/api/row/<category>', methods=['GET'])
def get_row(category):
    if movies_df is None: return jsonify([])
    
    if category == 'trending':
        movies = movies_df.sort_values(by='rating', ascending=False).head(10)
    elif category == 'action':
        movies = movies_df[movies_df['genre'].str.contains('Action', case=False, na=False)].head(10)
    elif category == 'scifi':
        # Handles both Sci-Fi and Fantasy
        movies = movies_df[movies_df['genre'].str.contains('Sci-Fi|Fantasy', case=False, na=False, regex=True)].head(10)
    else:
        movies = movies_df.sample(5)
        
    return jsonify(movies[['title', 'poster_url']].to_dict('records'))

# --- NEW PAGE ROUTES ---
@app.route('/movies')
def movies_page():
    return render_template('movies.html')

@app.route('/tv_shows')
def tv_shows_page():
    return render_template('tv_shows.html')

# --- NEW DATA API ROUTES ---
@app.route('/api/all_movies')
def all_movies():
    if movies_df is None: return jsonify([])
    # Grab the top 100 highest-rated movies for the massive grid
    movies = movies_df.sort_values(by='rating', ascending=False).head(100)
    return jsonify(movies[['title', 'poster_url']].to_dict('records'))

@app.route('/api/all_tv_shows')
def all_tv_shows():
    if movies_df is None: return jsonify([])
    # Placeholder: Grab 50 random items to pretend they are TV shows for the demo!
    shows = movies_df.sample(min(50, len(movies_df)))
    return jsonify(shows[['title', 'poster_url']].to_dict('records'))


# ==========================================
# 🤖 MOOD CHATBOT AI ROUTE
# ==========================================
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        user_msg = request.form.get('message', '').lower()
        if movies_df is None:
            return jsonify({"response": "I'm sorry, my movie database is currently offline!"})
            
        # 1. Simple NLP: Map words to genres
        mood_mapping = {
            'happy': ['Comedy', 'Animation', 'Adventure'],
            'good': ['Comedy', 'Animation', 'Action'],
            'sad': ['Drama', 'Romance'],
            'depressed': ['Comedy', 'Animation'], # Cheer them up!
            'angry': ['Action', 'Crime', 'Thriller'],
            'bored': ['Sci-Fi', 'Action', 'Fantasy'],
            'excited': ['Action', 'Sci-Fi', 'Adventure'],
            'relaxed': ['Romance', 'Drama', 'Fantasy']
        }
        
        target_genres = ['Action'] # Default fallback
        detected_mood = None
        
        for word, genres in mood_mapping.items():
            if word in user_msg:
                target_genres = genres
                detected_mood = word
                break
                
        # 2. Filter the dataframe by the chosen genre
        genre_filter = random.choice(target_genres)
        available_movies = movies_df[movies_df['genre'].str.contains(genre_filter, case=False, na=False)]
        
        # 3. Pick a random movie from that genre
        if available_movies.empty:
            movie = movies_df.sample(1).iloc[0]
        else:
            movie = available_movies.sample(1).iloc[0]
            
        # 4. Generate the bot's response text
        if detected_mood in ['sad', 'depressed']:
            bot_text = f"I'm sorry you're feeling down. Sometimes a good {genre_filter} movie can help escape reality for a bit. I highly recommend watching <strong>{movie['title']}</strong>."
        elif detected_mood:
            bot_text = f"Since you are feeling {detected_mood}, a {genre_filter} movie is perfect! You should definitely check out <strong>{movie['title']}</strong>."
        else:
            bot_text = f"I see! Based on that, I think you'd really enjoy a {genre_filter} movie like <strong>{movie['title']}</strong>."
        
        return jsonify({"response": bot_text, "poster": movie['poster_url']})
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"response": "Oops, my AI circuits got confused. Try asking again!"})

# ==========================================
# 🔐 AUTHENTICATION ROUTES
# ==========================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        number = request.form.get('number')
        age = request.form.get('age') # <--- Grab Age from the form
        password = request.form.get('password')

        # Check if user already exists
        existing_user = User.query.filter((User.email == email) | (User.number == number)).first()
        if existing_user:
            flash("Email or phone number already registered!", "error")
            return redirect(url_for('register'))

        # Secure the password
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')

        # Save to database (Now including age!)
        new_user = User(name=name, email=email, number=number, age=age, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form.get('login_id') # Can be email or number
        password = request.form.get('password')

        # Find user by email OR number
        user = User.query.filter((User.email == login_id) | (User.number == login_id)).first()

        # Check if user exists and password is correct
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['role'] = user.role # 'admin' or 'user'
            return redirect(url_for('home')) # Redirect to the main movie page
        else:
            flash("Invalid email/number or password.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear() # Erase the user's session
    return redirect(url_for('login'))

# 5. Start the Server
if __name__ == '__main__':
    # debug=True automatically restarts the server when you save changes to this file!
    app.run(debug=True, port=5000)