# Listify.lol 🎵  

### Generate Personalized Spotify Playlists Effortlessly  

[![Website](https://img.shields.io/badge/Website-Listify.lol-blue)](https://listify.lol)  
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black)](https://github.com/Lisify-LLC/website)  

## 📌 About  

**Listify.lol** is a web app designed to enhance the way users create Spotify playlists. By integrating with Spotify’s Developer API, Listify.lol allows users to log in with their Spotify account and generate playlists based on their listening habits over a chosen period.  

## ✨ Features  

- **Customizable Time Period** – Users can generate playlists from different time frames (e.g., last 15 days, past year).  
- **Top Songs Selection** – Automatically compiles a playlist of the user’s most-played songs.  
- **Spotify API Integration** – Securely retrieves user listening data to create personalized playlists.  
- **Embedded Playlist Preview** – Users can see their playlist before adding it to Spotify.  

## 🛠️ Tech Stack  

- **Backend:** Python (Flask)  
- **Frontend:** HTML, CSS  
- **Deployment:** Render.com  
- **Version Control:** GitHub  

## 🚀 Getting Started  

### Prerequisites  

- Python 3.x installed  
- Spotify Developer Account & API credentials  

### Installation  

1. Clone the repository:  
   ```bash
   git clone https://github.com/Lisify-LLC/website.git
   cd website
   ```  
2. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```  
3. Set up Spotify API credentials in a `.env` file:  
   ```plaintext
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   SPOTIFY_REDIRECT_URI=http://localhost:5000/callback
   ```  
4. Run the application:  
   ```bash
   python app.py
   ```  
5. Open `http://localhost:5000` in your browser.  

## 📄 License  

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.  

## 📩 Contact  

For any inquiries or contributions, reach out via GitHub Issues.