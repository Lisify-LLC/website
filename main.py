from flask import Flask, render_template, redirect, url_for, session, request
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import secrets

app = Flask(__name__)

my_secret_key = secrets.token_hex(16)
app.secret_key = my_secret_key 

# Define Spotify OAuth parameters
SPOTIPY_CLIENT_ID = '82948513a27844e2835f901062dfceea'
SPOTIPY_CLIENT_SECRET = '98eaebd996fc45d59f104ab768be87f5'
SPOTIPY_REDIRECT_URI = 'http://localhost:5000/callback'
SCOPE = 'user-top-read playlist-modify-public'

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
    # Store token information in session
    session['token_info'] = token_info
    return redirect(url_for('customize'))

@app.route('/generate_playlist')
def generate_playlist():
    if 'token_info' not in session:
        return redirect(url_for('login'))

    # Retrieve token information from session
    token_info = session['token_info']

    # Check if the token has expired, and refresh if necessary
    sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                            client_secret=SPOTIPY_CLIENT_SECRET,
                            redirect_uri=SPOTIPY_REDIRECT_URI,
                            scope=SCOPE)
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info

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

if __name__ == '__main__':
    app.run()
