from flask import Flask, redirect, url_for, session, request, render_template
import requests
import os
import time

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
    timeline = session.get('timeline', '2')
    track_value = session.get('track_value', '25')

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

    # Retrieve values from the session
    timeline = session.get('timeline')
    track_value = session.get('track_value')

    # Create a dictionary to map timeline values to their string representations
    timeline_dict = {'1': 'Last Month', '2': 'Last 6 Months', '3': 'Last Year'}

    if timeline is None:
        timeline = '2'
    
    if track_value is None:
        track_value = '25'

    # Create the playlist name
    playlist_name = f"Top {track_value} Tracks - {timeline_dict[timeline]}"

    # Create a new playlist
    create_playlist_url = f"{SPOTIFY_API_URL}/me/playlists"
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

    # Before the request
    start_time = time.time()

    for i in range(2):  # Retry up to 2 times
            response = requests.post(add_tracks_url, json=tracks_data, headers=headers)
            if response.status_code == 201:  # If the request was successful, break the loop
                break
            print(f"Attempt {i+1} failed, retrying in 1 seconds...")
            time.sleep(1)  # Wait for 1 seconds before the next try

    # After the request
    end_time = time.time()

    print("Time taken to add tracks:", end_time - start_time)  # Debug line
    
    print("Add tracks response status:", response.status_code)  # Debug line
    print("Add tracks response data:", response.json())  # Debug line
    
    # Create Variables for Embedded Playlist
    playlist_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
    playlist_title = playlist_name

    # Reset timeline and track_value in the session
    session['timeline'] = '2'
    session['track_value'] = '25'

    return render_template('complete.html', playlist_url=playlist_url, playlist_title=playlist_title)



if __name__ == '__main__':
    app.run(debug=True)
