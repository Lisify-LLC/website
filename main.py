from flask import Flask, redirect, url_for, session, request, render_template, abort
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import os
import time
import secrets

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Spotify API credentials
#CLIENT_ID = '23b153e787a14abe82424a9238c36101'
#CLIENT_SECRET = '2809d34409d7424c9eab342e1deed3a5'
#REDIRECT_URI = 'http://127.0.0.1:5000/callback'

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
STATE = secrets.token_hex(16)

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
    state = request.args.get('state')
    if state != STATE:
        abort(403)  # Forbidden
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
    refresh_token = response_data['refresh_token']  # Store the refresh token

    session['access_token'] = access_token
    session['refresh_token'] = refresh_token  # Store the refresh token in the session

    return redirect(url_for('generate_playlist'))

def refresh_access_token():
    refresh_token = session['refresh_token']
    refresh_url = "https://accounts.spotify.com/api/token"
    refresh_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    refresh_response = requests.post(refresh_url, data=refresh_data)
    refresh_response_data = refresh_response.json()
    new_access_token = refresh_response_data['access_token']
    session['access_token'] = new_access_token  # Store the new access token in the session

@app.route('/data', methods=['GET', 'POST'])
def data():
    track_value = request.form.get('tracks')
    timeline = request.form.get('time')

    # If track_value is 0 and set it to 1
    if track_value == '0':
        track_value = '1'

    # Store values in the session
    session['track_value'] = track_value
    session['timeline'] = timeline

    print("Track value:", track_value)
    print("Timeline:", timeline)

    return render_template('customize.html', track_value=track_value, timeline=timeline)

@app.route('/generate_playlist', methods=['GET', 'POST'])
def generate_playlist():
    print("Generating a new playlist")
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

    if response.status_code == 401:  # If the access token has expired
        refresh_access_token()  # Refresh the access token
        response = requests.get(top_tracks_url, headers=headers, params=params)  # Try the request again

    print("Top tracks response status:", response.status_code)  # Debug line
    top_tracks_data = response.json()

    # Retrieve values from the session
    timeline = session.get('timeline')
    track_value = session.get('track_value')

    # Create a dictionary to map timeline values to their string representations
    timeline_dict = {'1': 'Last 4 Weeks', '2': 'Last 6 Months', '3': 'Last 12 Months'}

    if timeline is None:
        timeline = '2'
    
    if track_value is None:
        track_value = '25'

    # Create the playlist name
    playlist_name = f"Top {track_value} Tracks - {timeline_dict[timeline]}"

     # Calculate the start date based on the timeline value
    end_date = datetime.now()
    if timeline == '1':
        start_date = end_date - relativedelta(weeks=4)
    elif timeline == '2':
        start_date = end_date - relativedelta(months=6)
    else:
        start_date = end_date - relativedelta(years=1)

    # Format the dates
    start_date_str = start_date.strftime("%m/%d/%Y")
    end_date_str = end_date.strftime("%m/%d/%Y")

    # Include the dates in the playlist description
    playlist_description = f"Your top {track_value} songs from {start_date_str} to {end_date_str}. Generated by Listify."


    # Create a new playlist
    create_playlist_url = f"{SPOTIFY_API_URL}/me/playlists"
    playlist_data = {
        'name': playlist_name,
        'description': playlist_description,
        'public': True
    }
    response = requests.post(create_playlist_url, json=playlist_data, headers=headers)
    if response.status_code not in [200, 201]:  # If the request was not successful
        print("Playlist creation failed with status:", response.status_code)
        print("Response data:", response.json())
        return render_template('error.html', message="Playlist creation failed.")  # Return an error page
    
    # Check the response for errors
    response_data = response.json()
    if 'error' in response_data:
        print("Error in playlist creation response:", response_data['error'])
        return  # Exit the function

    # Get the playlist ID
    playlist_id = response_data.get('id')
    if not playlist_id:  # If the playlist ID is not found in the response
        print("Playlist ID not found in the response.")
        return render_template('error.html', message="Playlist ID not found.")  # Return an error page

    print("Playlist ID:", playlist_id)  # Print the playlist ID

    time.sleep(1)  # Wait for 1 second before adding tracks to the playlist

    # Add a check here to ensure the playlist exists before adding tracks
    check_playlist_url = f"{SPOTIFY_API_URL}/playlists/{playlist_id}"
    response = requests.get(check_playlist_url, headers=headers)
    if response.status_code != 200:  # If the request was not successful
        print("Playlist check failed with status:", response.status_code)
        print("Response data:", response.json())
        return render_template('error.html', message="Playlist check failed.")  # Return an error page

    # Add tracks to the playlist
    track_uris = [track['uri'] for track in top_tracks_data['items']]
    add_tracks_url = f"{SPOTIFY_API_URL}/playlists/{playlist_id}/tracks"
    tracks_data = {'uris': track_uris}
    print("Track URIs:", track_uris)  # Print the track URIs

    # Before the request
    start_time = time.time()

    for i in range(10):  # Retry up to 10 times
        response = requests.post(add_tracks_url, json=tracks_data, headers=headers)
        if response.status_code in [200, 201]:  # If the request was successful
            print(f"Attempt {i+1} was successful.")
            break
        elif response.status_code == 400:  # Bad Request
            print("Bad Request: The request could not be understood or was missing required parameters.")
            break
        elif response.status_code == 401:  # Unauthorized
            print("Unauthorized: Authentication failed or was not provided.")
            refresh_access_token()  # Refresh the access token
            headers = {'Authorization': f"Bearer {session['access_token']}"}  # Update headers with new access token
            continue
        elif response.status_code == 403:  # Forbidden
            print("Forbidden: The request was understood, but it has been refused or access is not allowed.")
            break
        elif response.status_code == 404:  # Not Found
            print("Not Found: The requested resource could not be found.")
            return render_template('error.html', message="The playlist could not be found or is not accessible.")  # Return an error page
        elif response.status_code == 502:  # Bad Gateway
            print("Bad Gateway: The server was acting as a gateway or proxy and received an invalid response from the upstream server.")
            if i < 9:  # If this is not the last attempt
                print(f"Attempt {i+1} failed, retrying in 5 seconds...")
                time.sleep(5)  # Wait for 5 seconds before the next try
            continue
        else:
            print(f"Attempt {i+1} failed, retrying in 0.5 seconds...")
            time.sleep(0.5)  # Wait for 0.5 seconds before the next try

    # After the request
    end_time = time.time()

    print("Time taken to add tracks:", end_time - start_time)  # Debug line
    print("Add tracks response status:", response.status_code)  # Debug line
    print("Add tracks response data:", response.json())  # Debug line
    
    # Create Variables for Embedded Generated Playlist
    playlist_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
    playlist_title = playlist_name

    # Reset timeline and track_value in the session
    session['timeline'] = '2'
    session['track_value'] = '25'

    time.sleep(1) # Wait for 1 second before redirecting to the complete page

    return render_template('complete.html', playlist_url=playlist_url, playlist_title=playlist_title)

if __name__ == '__main__':
    app.run(debug=True)