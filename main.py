from flask import Flask, redirect, url_for, session, request, render_template
import requests
import base64
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Spotify API credentials
CLIENT_ID = 'd61b59a21f5f41a980741d941d94b003'
CLIENT_SECRET = '0a8ee53e3e4348d7bc5bb0aeca4d2996'
REDIRECT_URI = 'https://listify.lol/callback'

# Spotify API endpoints
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1'
SPOTIFY_API_VERSION = 'v1'
SPOTIFY_API_URL = f'{SPOTIFY_API_BASE_URL}'

# Scopes for Spotify API
SCOPE = 'user-top-read playlist-modify-public playlist-modify-private'
STATE = ''

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/privacy-policy")
def privacy_policy():
    return render_template('privacy-policy.html')

@app.route("/customize")
def customize():
    return render_template('customize.html')

@app.route('/login')
def login():
    payload = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
        'state': STATE
    }
    playlist_type = request.args.get('playlist_type')
    if playlist_type:
        session['playlist_type'] = playlist_type
    auth_url = f'{SPOTIFY_AUTH_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPE}&state={STATE}'
    return redirect(auth_url)

@app.route('/callback')
def callback():
    auth_token = request.args['code']
    code_payload = {
        'grant_type': 'authorization_code',
        'code': str(auth_token),
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    response_data = post_request.json()
    access_token = response_data['access_token']

    session['access_token'] = access_token


    return redirect(url_for('generate_playlist'))



@app.route('/generate_playlist')
def generate_playlist():
    if 'access_token' not in session:
        return redirect(url_for('login'))

    # Create a new playlist
    create_playlist_url = f"{SPOTIFY_API_URL}/me/playlists"
    playlist_name = "Top 30 Tracks Last Month"
    playlist_data = {
        'name': playlist_name,
        'description': '',
        'public': True
    }
    response = requests.post(create_playlist_url, json=playlist_data, headers=headers)
    playlist_id = response.json()['id']

    # Retrieve user's top tracks from Spotify
    top_tracks_url = f"{SPOTIFY_API_URL}/me/top/tracks"
    headers = {'Authorization': f"Bearer {session['access_token']}"}
    params = {'time_range': 'short_term', 'limit': 30}
    response = requests.get(top_tracks_url, headers=headers, params=params)
    top_tracks_data = response.json()

    # Add tracks to the playlist
    track_uris = [track['uri'] for track in top_tracks_data['items']]
    add_tracks_url = f"{SPOTIFY_API_URL}/playlists/{playlist_id}/tracks"
    tracks_data = {'uris': track_uris}
    response = requests.post(add_tracks_url, json=tracks_data, headers=headers)

    return render_template('complete.html')


if __name__ == '__main__':
    app.run(host= "0.0.0.0", port=5000)
