from flask import Flask, render_template, redirect, url_for, session, request
import sqlite3
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)

app.secret_key = 'SECRET_KEY'  # Change this to a random secret key

# Define Spotify OAuth parameters
SPOTIPY_CLIENT_ID = 'your_client_id'
SPOTIPY_CLIENT_SECRET = 'your_client_secret'
SPOTIPY_REDIRECT_URI = 'http://localhost:5000/callback'
SCOPE = 'user-top-read playlist-modify-public'

# Initialize SQLite database
conn = sqlite3.connect('sessions.db')
conn.execute('''CREATE TABLE IF NOT EXISTS sessions
             (session_id TEXT PRIMARY KEY, token_info TEXT)''')
conn.commit()

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/customize")
def customize():
    return render_template('customize.html')

@app.route('/login')
def login():
    # Initialize SpotifyOAuth with client ID, client secret, redirect URI, and scope
    sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                            client_secret=SPOTIPY_CLIENT_SECRET,
                            redirect_uri=SPOTIPY_REDIRECT_URI,
                            scope=SCOPE)
    # Get the authorization URL
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/callback')
def callback():
    # Get the authorization code from the callback URL
    code = request.args.get('code')
    # Initialize SpotifyOAuth
    sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                            client_secret=SPOTIPY_CLIENT_SECRET,
                            redirect_uri=SPOTIPY_REDIRECT_URI,
                            scope=SCOPE)
    # Exchange authorization code for access token
    token_info = sp_oauth.get_access_token(code)
    # Generate a unique session identifier
    session_id = generate_session_id()
    # Store token information in the database
    conn.execute("INSERT INTO sessions (session_id, token_info) VALUES (?, ?)", (session_id, token_info))
    conn.commit()
    # Store session_id in the user's session
    session['session_id'] = session_id
    return redirect(url_for('customize'))

@app.route('/generate_playlist')
def generate_playlist():
    session_id = session.get('session_id')
    if not session_id:
        return redirect(url_for('login'))
    # Retrieve token information from the database based on the session_id
    cursor = conn.execute("SELECT token_info FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        return redirect(url_for('login'))
    token_info = row[0]
    # Create a Spotify client object using the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])
    # Get the user's top tracks from the last month
    top_tracks = sp.current_user_top_tracks(limit=30, time_range='short_term')
    # Extract URIs of top tracks
    top_track_uris = [track['uri'] for track in top_tracks['items']]
    # Define playlist name
    playlist_name = 'Top 30 Tracks from Last Month'
    # Get user ID
    user_id = sp.current_user()['id']
    # Create a playlist with the specified name
    playlist_id = sp.user_playlist_create(user=user_id, name=playlist_name)['id']
    # Add top tracks to the created playlist
    sp.playlist_add_items(playlist_id, items=top_track_uris)
    return "Playlist generated successfully!"

def generate_session_id():
    # Generate a unique session identifier (you can use UUID or any other method)
    return 'session_id_placeholder'

if __name__ == '__main__':
   app.run()