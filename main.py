from flask import Flask, redirect, url_for, session, request, render_template
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Spotify API credentials
CLIENT_ID = '23b153e787a14abe82424a9238c36101'
CLIENT_SECRET = '2809d34409d7424c9eab342e1deed3a5'
REDIRECT_URI = 'http://127.0.0.1:5000/callback'

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

@app.route('/data', methods=['GET', 'POST'])
def data():
    track_value = request.form.get('tracks')
    timeline = request.form.get('time')

    # Store values in the session
    session['track_value'] = track_value
    session['timeline'] = timeline

    print("Track value:", track_value)
    print("Timeline:", timeline)

    return render_template('customize.html', track_value=track_value, timeline=timeline)

@app.route('/generate_playlist', methods=['GET', 'POST'])
def generate_playlist():
    if 'access_token' not in session:
        return redirect(url_for('login'))
    
    # Retrieve values from the session
    timeline = session.get('timeline')
    track_value = session.get('track_value')

    if timeline == '1':
        time_range = 'short_term'
    elif timeline == '2':
        time_range = 'medium_term'
    else:
        time_range = 'long_term'

    print(track_value)
    print(timeline)
    print(time_range)
    
   # Retrieve user's top tracks from Spotify
    top_tracks_url = f"{SPOTIFY_API_URL}/me/top/tracks"
    headers = {'Authorization': f"Bearer {session['access_token']}"}
    params = {'time_range': time_range, 'limit': track_value}
    response = requests.get(top_tracks_url, headers=headers, params=params)
    print("Top tracks response status:", response.status_code)  # Debug line
    print("Top tracks response data:", response.json())  # Debug line
    top_tracks_data = response.json()

    # Create a new playlist
    create_playlist_url = f"{SPOTIFY_API_URL}/me/playlists"
    playlist_name = "Top 20 Tracks Last Year"
    playlist_data = {
        'name': playlist_name,
        'description': '',
        'public': True
    }
    response = requests.post(create_playlist_url, json=playlist_data, headers=headers)
    playlist_id = response.json()['id']

    # Check if 'id' is in the response before accessing it
    response_data = response.json()
    if 'id' in response_data:
        playlist_id = response_data['id']
    else:
        print("Error: 'id' not found in response data")
        return "Error: 'id' not found in response data", 400

    # Add tracks to the playlist
    track_uris = [track['uri'] for track in top_tracks_data['items']]
    add_tracks_url = f"{SPOTIFY_API_URL}/playlists/{playlist_id}/tracks"
    tracks_data = {'uris': track_uris}
    response = requests.post(add_tracks_url, json=tracks_data, headers=headers)
    print("Add tracks response status:", response.status_code)  # Debug line
    print("Add tracks response data:", response.json())  # Debug line
    
    # Create Variables for Embedded Playlist
    playlist_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
    playlist_title = playlist_name

    return render_template('complete.html', playlist_url=playlist_url, playlist_title=playlist_title)



if __name__ == '__main__':
    app.run(debug=True)
