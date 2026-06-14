from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import random
import requests
import re  # Used to clean up HTML text from the API

# 1. Initialize the Flask App
app = Flask(__name__)
app.secret_key = 'super_secret_cinematch_key'

# ==========================================
# 💾 DATABASE SETUP (For Users & Watchlist)
# ==========================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cinematch_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class SavedMovie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_name = db.Column(db.String(100), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    number = db.Column(db.String(20), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False) 
    password = db.Column(db.String(200), nullable=False) 
    role = db.Column(db.String(20), default='user')

with app.app_context():
    db.create_all()

# ==========================================
# 🌐 MAIN WEB ROUTES
# ==========================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/movies')
def movies_page():
    return render_template('movies.html')

@app.route('/tv_shows')
def tv_shows_page():
    return render_template('tv_shows.html')

# ==========================================
# 🔍 1. LIVE SEARCH API
# ==========================================
@app.route('/recommend', methods=['POST'])
def recommend():
    query = request.form.get('movie', '').strip()
    if not query: return jsonify({"error": "Please enter a search term."}), 400

    try:
        url = f"https://api.tvmaze.com/search/shows?q={query}"
        response = requests.get(url)
        data = response.json()

        if not data: return jsonify({"error": f'No results found for "{query}".'})

        recommendation_list = []
        for item in data[:10]:
            show = item['show']
            poster = show['image']['medium'] if show.get('image') else "https://placehold.co/200x300/1a1e26/e50914?text=No+Poster"
            recommendation_list.append({
                'title': show.get('name', 'Unknown'),
                'poster_url': poster
            })

        return jsonify(recommendation_list)
    except Exception as e:
        return jsonify({"error": "API connection failed."}), 500

# ==========================================
# 🎬 2. LIVE MOVIE DETAILS (Runs when you click a card)
# ==========================================
@app.route('/api/movie/<path:movie_title>')
def get_movie_details(movie_title):
    # Clean the title just in case the JS sent the star emoji
    clean_title = movie_title.replace("⭐ YOU SEARCHED: ", "").strip()
    
    try:
        # Ask TVMaze for the exact details of this specific show
        url = f"https://api.tvmaze.com/singlesearch/shows?q={clean_title}"
        response = requests.get(url)
        
        if response.status_code != 200:
            return jsonify({"error": "Movie not found in live database."})
            
        show = response.json()
        
        # Clean the HTML tags out of the API's description text
        raw_desc = show.get('summary', 'No description available.')
        clean_desc = re.sub('<[^<]+>', '', raw_desc) if raw_desc else "No description available."
        
        poster = show['image']['original'] if show.get('image') else "https://placehold.co/200x300/1a1e26/e50914?text=No+Poster"
        genres = " & ".join(show.get('genres', ['Drama']))
        if not genres: genres = "Drama"

        # Reliable test trailers since TVmaze doesn't provide YouTube links
        mock_trailers = [
            "https://www.youtube.com/embed/b9EkMc79ZSU", # Stranger Things
            "https://www.youtube.com/embed/HhesaQXLuRY", # Breaking Bad
            "https://www.youtube.com/embed/aOC8E8z_ifw"  # Mandalorian
        ]

        details = {
            "title": show.get('name', 'Unknown'),
            "genre": genres,
            "runtime": str(show.get('averageRuntime', '60')),
            "rating": str(show.get('rating', {}).get('average', '8.0')),
            "age_match": str(random.randint(85, 99)),
            "description": clean_desc,
            "poster_url": poster,
            "cast": "View Official Cast on TVmaze",
            "views": f"{random.randint(10, 250)} Million",
            "review": "Highly rated by users globally!",
            "trailer_url": random.choice(mock_trailers) 
        }
        
        return jsonify(details)
    except Exception as e:
        return jsonify({"error": "Failed to fetch details."})

# ==========================================
# 📺 3. LIVE HOMEPAGE ROWS (Trending, Action, SciFi)
# ==========================================
@app.route('/api/row/<category>', methods=['GET'])
def get_row(category):
    try:
        # Map the row categories to API search keywords
        query_map = {
            'trending': 'best',
            'action': 'action',
            'scifi': 'space'
        }
        query = query_map.get(category, 'world')
        
        url = f"https://api.tvmaze.com/search/shows?q={query}"
        response = requests.get(url)
        data = response.json()
        
        movies = []
        for item in data[:10]:
            show = item['show']
            poster = show['image']['medium'] if show.get('image') else "https://placehold.co/200x300/1a1e26/e50914?text=No+Poster"
            movies.append({
                'title': show.get('name', 'Unknown'),
                'poster_url': poster
            })
            
        return jsonify(movies)
    except:
        return jsonify([])

# ==========================================
# 🤖 4. LIVE AI CHATBOT
# ==========================================
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        user_msg = request.form.get('message', '').lower().strip()
        
        # 1. Map user moods/keywords to actual TVmaze genres
        target_genre = None
        mood_detected = "Movie"
        
        if any(word in user_msg for word in ['romantic', 'romance', 'love', 'couple', 'date']):
            target_genre = "Romance"
            mood_detected = "❤️ Romantic"
        elif any(word in user_msg for word in ['action', 'excited', 'fight', 'adventure', 'thrill']):
            target_genre = "Action"
            mood_detected = "💥 Action-packed"
        elif any(word in user_msg for word in ['sci-fi', 'future', 'space', 'alien', 'fantasy']):
            target_genre = "Science-Fiction"
            mood_detected = "🚀 Sci-Fi"
        elif any(word in user_msg for word in ['funny', 'laugh', 'comedy', 'bored', 'happy']):
            target_genre = "Comedy"
            mood_detected = "😂 Hilarious"
        elif any(word in user_msg for word in ['sad', 'cry', 'emotional', 'drama']):
            target_genre = "Drama"
            mood_detected = "😢 Deep Drama"
        elif any(word in user_msg for word in ['scary', 'horror', 'spooky', 'ghost', 'fear', 'halloween']):
            target_genre = "Horror"
            mood_detected = "👻 Spooky Horror"

        # 2. Fetch data from TVmaze API based on the mood
        if target_genre:
            # Pull from a random page of the database so recommendations stay fresh!
            random_page = random.randint(0, 5)
            response = requests.get(f"https://api.tvmaze.com/shows?page={random_page}", timeout=5)
            
            if response.status_code == 200:
                all_shows = response.json()
                
                # Filter out shows that don't match our target genre OR don't have posters
                matched_shows = [s for s in all_shows if s.get('genres') and target_genre in s['genres'] and s.get('image')]
                
                if matched_shows:
                    selected_show = random.choice(matched_shows)
                    show_name = selected_show.get('name')
                    rating = selected_show.get('rating', {}).get('average') or '8.0'
                    poster_url = selected_show['image']['medium']
                    
                    bot_text = f"Since you're looking for a {mood_detected} vibe, I highly recommend watching <b>{show_name}</b> (⭐ {rating})!"
                    return jsonify({"response": bot_text, "poster": poster_url})

        # 3. Fallback: If they typed a specific movie title instead of a mood, just search for it!
        fallback_res = requests.get(f"https://api.tvmaze.com/search/shows?q={user_msg}", timeout=5)
        fallback_data = fallback_res.json()
        
        if fallback_data:
            show = fallback_data[0]['show']
            show_name = show.get('name')
            poster_url = show['image']['medium'] if show.get('image') else ""
            bot_text = f"I didn't detect a specific mood, but I found this matching your text: <b>{show_name}</b>!"
            return jsonify({"response": bot_text, "poster": poster_url})
            
        # 4. Total Fallback
        return jsonify({"response": "I couldn't find a good match right now. Try typing a mood like 'romantic', 'funny', or 'scary'!"})

    except Exception as e:
        print(f"Chatbot API error: {e}")
        return jsonify({"response": "My connection to the TVmaze database is down! Please try again."})
    
# ==========================================
# 🍿 5. LIVE PAGES API (Movies & TV Shows Fix)
# ==========================================
@app.route('/api/all_movies')
def all_movies():
    try:
        # Fetch a massive list of shows directly from TVmaze's main index
        response = requests.get("https://api.tvmaze.com/shows")
        data = response.json()
        
        movies = []
        # Grab items 100 to 200 to fill the Movies Grid
        for show in data[100:200]: 
            poster = show['image']['medium'] if show.get('image') else "https://placehold.co/200x300/1a1e26/e50914?text=No+Poster"
            movies.append({'title': show.get('name', 'Unknown'), 'poster_url': poster})
            
        return jsonify(movies)
    except Exception as e:
        print(f"Error loading movies page: {e}")
        return jsonify([])

@app.route('/api/all_tv_shows')
def all_tv_shows():
    try:
        # Fetch a massive list of shows directly from TVmaze's main index
        response = requests.get("https://api.tvmaze.com/shows")
        data = response.json()
        
        shows = []
        # Grab the first 100 items to fill the TV Shows Grid
        for show in data[:100]: 
            poster = show['image']['medium'] if show.get('image') else "https://placehold.co/200x300/1a1e26/e50914?text=No+Poster"
            shows.append({'title': show.get('name', 'Unknown'), 'poster_url': poster})
            
        return jsonify(shows)
    except Exception as e:
        print(f"Error loading TV shows page: {e}")
        return jsonify([])
    

# ==========================================
# 🔐 AUTHENTICATION ROUTES (Unchanged)
# ==========================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        number = request.form.get('number')
        age = request.form.get('age')
        password = request.form.get('password')

        existing_user = User.query.filter((User.email == email) | (User.number == number)).first()
        if existing_user:
            flash("Email or phone number already registered!", "error")
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, email=email, number=number, age=age, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form.get('login_id')
        password = request.form.get('password')

        user = User.query.filter((User.email == login_id) | (User.number == login_id)).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['role'] = user.role
            return redirect(url_for('home'))
        else:
            flash("Invalid email/number or password.", "error")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)