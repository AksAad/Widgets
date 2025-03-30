from base_widget import BaseWidget
from PyQt6.QtCore import Qt, QTimer, QRectF, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QImage, QPixmap, QFont, QIcon, QPainterPath,
    QLinearGradient, QRadialGradient, QFontMetrics
)
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QSlider, QFrame, QWidget
import psutil
import win32gui
import win32process
import re
import requests
import io
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from io import BytesIO
import win32api
import win32con
import win32ui
import win32com.client
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager
import asyncio
import threading
import webbrowser

class AlbumArtLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)  # Restore original size
        self.setStyleSheet("""
            QLabel {
                background: rgba(20, 20, 20, 0.4);
                border-radius: 15px;
                padding: 0;
                border: 1px solid rgba(147, 112, 219, 0.3);
            }
        """)
        
    def setPixmap(self, pixmap):
        if pixmap and not pixmap.isNull():
            # Create a rounded version of the pixmap
            rounded = QPixmap(self.size())
            rounded.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Create rounded rect path
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
            painter.setClipPath(path)
            
            # Scale and draw the pixmap
            scaled = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Center the scaled pixmap
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.end()
            
            super().setPixmap(rounded)
        else:
            self.clear()
            
    def paintEvent(self, event):
        if not self.pixmap():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw rounded rectangle background
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
            painter.fillPath(path, QColor(255, 255, 255, 25))
            
            # Draw music note icon
            painter.setPen(QColor(255, 255, 255, 127))
            font = QFont("Segoe UI Symbol", 20)  # Slightly smaller font
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "♪")
        else:
            super().paintEvent(event)

class ScrollingLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("color: rgba(180, 180, 180, 0.9);")
        self._scroll_pos = 0
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._update_scroll)
        self._animation_timer.setInterval(50)
        self._pause_timer = QTimer()
        self._pause_timer.timeout.connect(self._start_scroll)
        self._pause_timer.setSingleShot(True)
        self._text_width = 0
        self._should_scroll = False
        
    def setText(self, text):
        super().setText(text)
        self._reset_scroll()
        
    def _reset_scroll(self):
        self._scroll_pos = 0
        self._animation_timer.stop()
        self._pause_timer.stop()
        metrics = QFontMetrics(self.font())
        self._text_width = metrics.horizontalAdvance(self.text())
        self._should_scroll = self._text_width > self.width()
        if self._should_scroll:
            self._pause_timer.start(2000)
            
    def _start_scroll(self):
        if self._should_scroll:
            self._animation_timer.start()
            
    def _update_scroll(self):
        if not self._should_scroll:
            return
        self._scroll_pos = (self._scroll_pos + 1) % (self._text_width + self.width())
        self.update()
        
    def paintEvent(self, event):
        if not self._should_scroll:
            super().paintEvent(event)
            return
            
        painter = QPainter(self)
        painter.setFont(self.font())
        
        # Draw text
        text = self.text()
        x = -self._scroll_pos
        painter.setPen(QColor(180, 180, 180, 230))
        painter.drawText(x, 0, self._text_width, self.height(),
                        Qt.AlignmentFlag.AlignVCenter, text)
        
        # Draw second copy if needed
        if x + self._text_width < self.width():
            painter.drawText(x + self._text_width + 20, 0,
                           self._text_width, self.height(),
                           Qt.AlignmentFlag.AlignVCenter, text)
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reset_scroll()

class IconButton(QPushButton):
    def __init__(self, icon_char, size=24, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText(icon_char)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 0;
                color: rgba(180, 180, 180, 0.9);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                color: rgba(180, 180, 180, 1.0);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
                color: rgba(180, 180, 180, 0.8);
            }
        """)

class MusicWidget(BaseWidget):
    def __init__(self):
        super().__init__(size=(500, 100))
        self.title_label.setText("Now Playing")
        
        # Create main content layout
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(12, 8, 12, 12)
        content_layout.setSpacing(12)
        
        # Album art
        self.album_art = AlbumArtLabel()  # Switch back to AlbumArtLabel
        self.album_art.setFixedSize(100, 100)  # Match the container size
        content_layout.addWidget(self.album_art)
        
        # Right side container
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)
        
        # Track info
        self.track_name = ScrollingLabel()
        self.track_name.setFixedHeight(24)
        self.track_name.setFont(QFont("Segoe UI", 10))
        right_layout.addWidget(self.track_name)
        
        self.artist_name = ScrollingLabel()
        self.artist_name.setFixedHeight(20)
        self.artist_name.setFont(QFont("Segoe UI", 9))
        self.artist_name.setStyleSheet("color: rgba(180, 180, 180, 0.7);")
        right_layout.addWidget(self.artist_name)
        
        # Controls container
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        
        # Previous button
        self.prev_button = IconButton("⏮", size=28)  # Use Unicode character instead of icon file
        self.prev_button.setFont(QFont("Segoe UI Symbol", 14))
        controls_layout.addWidget(self.prev_button)
        
        # Play/Pause button
        self.play_button = IconButton("▶", size=32)  # Use Unicode character instead of icon file
        self.play_button.setFont(QFont("Segoe UI Symbol", 16))
        controls_layout.addWidget(self.play_button)
        
        # Next button
        self.next_button = IconButton("⏭", size=28)  # Use Unicode character instead of icon file
        self.next_button.setFont(QFont("Segoe UI Symbol", 14))
        controls_layout.addWidget(self.next_button)
        
        # Add stretch to center controls
        controls_layout.addStretch()
        
        right_layout.addWidget(controls_container)
        
        # Progress slider
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setFixedHeight(16)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 2px;
                background: rgba(40, 40, 45, 100);
                margin: 0;
            }
            QSlider::handle:horizontal {
                width: 8px;
                margin: -3px 0;
                border-radius: 4px;
                background: rgba(180, 180, 180, 180);
            }
            QSlider::sub-page:horizontal {
                background: rgba(180, 180, 180, 180);
            }
        """)
        right_layout.addWidget(self.progress_slider)
        
        content_layout.addWidget(right_container)
        self.layout.addLayout(content_layout)
        
        # Connect signals
        self.prev_button.clicked.connect(self.previous_track)
        self.play_button.clicked.connect(self.toggle_playback)
        self.next_button.clicked.connect(self.next_track)
        self.progress_slider.sliderMoved.connect(self.seek)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(1000)  # Update every second
        
        # Initialize state
        self.is_playing = False
        self.current_track = None
        self.album_art_cache = {}
        
        # Initial update
        self.update_data()
        
        # Override base widget background to be fully transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Initialize Spotify session and async loop
        self.spotify = None
        self.spotify_cache = {}
        self.loop = asyncio.new_event_loop()
        self.async_thread = None
        
        # Set up media controls and start async thread
        self.setup_media_controls()
        
        # Initialize Spotify in a separate thread
        threading.Thread(target=self.init_spotify, daemon=True).start()
        
    def init_spotify(self):
        """Initialize Spotify connection in a separate thread"""
        try:
            # Create cache handler
            cache_path = '.spotify_cache'
            
            # Initialize auth manager with proper scopes
            auth_manager = SpotifyOAuth(
                client_id='MAKE A CLIENT ID ON SPOTIFY DEVELOPER (STEP 1 SELECT OPTION TO MAKE AN APP THEN PROVIDE LOCALHOST CALL BACK THEN COPY PASTE THE IDS',
                client_secret=' ENter_your_id_here',
                redirect_uri='http://localhost:8888/callback',
                scope='user-read-currently-playing user-read-playback-state',
                open_browser=True,  # Open browser automatically
                cache_path=cache_path,
                show_dialog=True  # Always show the auth dialog
            )
            
            # Check if we have a cached token
            token_info = auth_manager.get_cached_token()
            if not token_info or auth_manager.is_token_expired(token_info):
                print("\nStarting Spotify authentication...")
                print("1. A browser window will open for Spotify authorization")
                print("2. Log in to Spotify if needed and click 'Agree'")
                print("3. After agreeing, you'll be redirected to a URL that starts with 'http://localhost:8888/callback?code=...'")
                print("4. Copy the ENTIRE URL (including the code parameter) and paste it here")
                print("\nWaiting for authorization...")
                
                # Get the authorization URL and open it
                auth_url = auth_manager.get_authorize_url()
                webbrowser.open(auth_url)
                
                # Wait for the redirect URL
                print("\nAfter authorizing, paste the FULL redirect URL here (including the code parameter):")
                redirect_url = input().strip()
                
                if not redirect_url:
                    print("No URL provided. Spotify features will be disabled.")
                    return
                    
                if 'code=' not in redirect_url:
                    print("Invalid URL provided. Make sure to copy the entire URL including the code parameter.")
                    print("The URL should look like: http://localhost:8888/callback?code=AQD...")
                    return
                
                try:
                    code = auth_manager.parse_response_code(redirect_url)
                    token_info = auth_manager.get_access_token(code)
                    print("Successfully authenticated with Spotify!")
                except Exception as e:
                    print(f"Error during Spotify authentication: {e}")
                    print("Please try restarting the widget and authenticating again.")
                    return
            
            # Create the Spotify client
            self.spotify = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test the connection
            try:
                current_playback = self.spotify.current_playback()
                print("\nSuccessfully connected to Spotify!")
                if current_playback:
                    track = current_playback['item']
                    print(f"Currently playing: {track['name']} by {track['artists'][0]['name']}")
            except Exception as e:
                print(f"Error testing Spotify connection: {e}")
                if hasattr(e, 'response'):
                    print(f"Response status: {e.response.status_code}")
                    print(f"Response text: {e.response.text}")
            
        except Exception as e:
            print(f"\nError initializing Spotify: {e}")
            print("\nPlease ensure:")
            print("1. You have registered your application at https://developer.spotify.com/dashboard")
            print("2. The client ID and secret are correct")
            print("3. http://localhost:8888/callback is added to your application's Redirect URIs")
            print("4. You have Spotify Premium (required for some API features)")
            self.spotify = None
        
    async def update_album_art(self, image_url):
        """Asynchronously update album art"""
        try:
            if image_url in self.spotify_cache:
                return
                
            response = requests.get(image_url)
            if response.status_code == 200:
                img_data = response.content
                img = QImage()
                if img.loadFromData(img_data):
                    scaled = img.scaled(
                        self.album_art.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    pixmap = QPixmap.fromImage(scaled)
                    if not pixmap.isNull():
                        self.spotify_cache[image_url] = pixmap
                        self.album_art.setPixmap(pixmap)
        except Exception as e:
            print(f"Error updating album art: {e}")
    
    def setup_media_controls(self):
        """Set up async event loop for media controls"""
        self.async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.async_thread.start()
    
    def _run_async_loop(self):
        """Run the async event loop in a separate thread"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def update_data(self):
        """Update the widget with current playback information"""
        try:
            # Get current playback state
            current_playback = self.spotify.current_playback() if self.spotify else None
            
            if current_playback and current_playback['item']:
                track = current_playback['item']
                self.current_track = track
                
                # Update track and artist names
                self.track_name.setText(track['name'])
                self.artist_name.setText(", ".join([artist['name'] for artist in track['artists']]))
                
                # Update play/pause button
                self.is_playing = current_playback['is_playing']
                self.play_button.setText("⏸" if self.is_playing else "▶")
                
                # Update progress slider
                progress_ms = current_playback['progress_ms']
                duration_ms = track['duration_ms']
                if duration_ms > 0:
                    progress_percent = (progress_ms / duration_ms) * 100
                    self.progress_slider.setValue(int(progress_percent))
                
                # Update album art if needed
                if track.get('album') and track['album'].get('images'):
                    image_url = track['album']['images'][0]['url']
                    asyncio.run_coroutine_threadsafe(
                        self.update_album_art(image_url),
                        self.loop
                    )
            else:
                # Clear display if no track is playing
                self.track_name.setText("Not Playing")
                self.artist_name.setText("")
                self.album_art.clear()
                self.play_button.setText("▶")
                self.progress_slider.setValue(0)
                self.current_track = None
                
        except Exception as e:
            print(f"Error updating music widget: {e}")
    
    def paintEvent(self, event):
        # Override paintEvent to make background fully transparent
        pass

    def find_spotify_window(self):
        """Find the Spotify window handle"""
        def callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and 'Spotify' in title and title != 'Spotify':
                    hwnds.append(hwnd)
            return True
        
        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds[0] if hwnds else None
    
    def get_chrome_title(self):
        """Get song info from Chrome/Opera GX tabs"""
        def enum_windows_callback(hwnd, result):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    if process.name().lower() in ['chrome.exe', 'opera.exe', 'operagx.exe']:
                        title = win32gui.GetWindowText(hwnd)
                        if ' - YouTube Music' in title:
                            title = title.replace(' - YouTube Music', '')
                            parts = title.rsplit(' - ', 1)
                            if len(parts) == 2:
                                artist, title = parts
                                return {
                                    'title': title.strip(),
                                    'artist': artist.strip(),
                                    'album_art': None,
                                    'source': 'YouTube Music'
                                }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return None
        
        try:
            songs = []
            win32gui.EnumWindows(lambda hwnd, songs: songs.append(enum_windows_callback(hwnd, songs)) or True, songs)
            songs = [s for s in songs if s]
            return songs[0] if songs else None
        except Exception as e:
            print(f"Error getting Chrome title: {e}")
            return None
    
    def get_spotify_title(self):
        """Get song info from Spotify desktop app"""
        spotify_hwnd = self.find_spotify_window()
        if spotify_hwnd:
            try:
                title = win32gui.GetWindowText(spotify_hwnd)
                if title and 'Spotify' in title and title != 'Spotify':
                    song = re.sub(r' - Spotify$', '', title)
                    parts = song.rsplit(' - ', 1)
                    if len(parts) == 2:
                        artist, title = parts
                        return {
                            'title': title.strip(),
                            'artist': artist.strip(),
                            'album_art': None,
                            'source': 'Spotify'
                        }
            except Exception as e:
                print(f"Error getting Spotify title: {e}")
        return None

    def previous_track(self):
        """Handle previous track button click"""
        try:
            # Send previous track media key (VK_MEDIA_PREV_TRACK = 0xB1)
            win32api.keybd_event(0xB1, 0, 0, 0)
            win32api.keybd_event(0xB1, 0, win32con.KEYEVENTF_KEYUP, 0)
            QTimer.singleShot(100, self.update_data)
        except Exception as e:
            print(f"Error handling previous track: {e}")

    def next_track(self):
        """Handle next track button click"""
        try:
            # Send next track media key (VK_MEDIA_NEXT_TRACK = 0xB0)
            win32api.keybd_event(0xB0, 0, 0, 0)
            win32api.keybd_event(0xB0, 0, win32con.KEYEVENTF_KEYUP, 0)
            QTimer.singleShot(100, self.update_data)
        except Exception as e:
            print(f"Error handling next track: {e}")

    def toggle_playback(self):
        try:
            # Send multimedia play/pause key (VK_MEDIA_PLAY_PAUSE = 0xB3)
            win32api.keybd_event(0xB3, 0, 0, 0)
            win32api.keybd_event(0xB3, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            # Update button state after a short delay
            QTimer.singleShot(100, self.update_data)
        except Exception as e:
            print(f"Error toggling play state: {e}")
    
    def animate_track_change(self):
        # Fade out current text
        fade_out = QPropertyAnimation(self.track_container, b"windowOpacity")
        fade_out.setDuration(150)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.start()
        
        # Fade in new text after a short delay
        QTimer.singleShot(150, lambda: self.track_container.setWindowOpacity(1.0))
    
    def get_spotify_album_art(self, artist, title):
        """Get album art URL from Spotify API"""
        if not self.spotify:
            print("Spotify client not initialized")
            return None
            
        cache_key = f"{artist} - {title}"
        if cache_key in self.spotify_cache:
            print(f"Using cached album art for {cache_key}")
            return self.spotify_cache[cache_key]
            
        try:
            print(f"Searching Spotify for: {artist} - {title}")
            
            # First try to get currently playing track
            current = self.spotify.current_playback()
            if current and current.get('item'):
                track = current['item']
                if track['name'].lower() == title.lower() and any(a['name'].lower() == artist.lower() for a in track['artists']):
                    if track['album']['images']:
                        image_url = track['album']['images'][0]['url']
                        print(f"Found album art from current playback")
                        self.spotify_cache[cache_key] = image_url
                        return image_url
            
            # If not found in current playback, search for the track
            query = f"track:{title} artist:{artist}"
            results = self.spotify.search(q=query, type='track', limit=1)
            
            if results and results['tracks']['items']:
                track = results['tracks']['items'][0]
                # Verify the match
                track_name = track['name'].lower()
                track_artists = [a['name'].lower() for a in track['artists']]
                
                if (track_name == title.lower() or track_name in title.lower() or title.lower() in track_name) and \
                   (artist.lower() in track_artists or any(a in artist.lower() for a in track_artists)):
                    
                    if track['album']['images']:
                        image_url = track['album']['images'][0]['url']
                        print(f"Found album art from search")
                        self.spotify_cache[cache_key] = image_url
                        return image_url
                    else:
                        print("Track found but no album art available")
                else:
                    print(f"Search result didn't match closely enough: {track_name} by {', '.join(track_artists)}")
            else:
                print("No search results found")
                
        except Exception as e:
            print(f"Error getting Spotify album art: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response status: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
        return None
        
    def update_spotify_album_art(self, artist, title):
        """Update album art using Spotify API"""
        if not self.spotify:
            return False
            
        try:
            # First try to get currently playing track
            current = self.spotify.current_playback()
            if current and current.get('item'):
                track = current['item']
                if track['album']['images']:
                    image_url = track['album']['images'][0]['url']
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        img_data = response.content
                        img = QImage()
                        if img.loadFromData(img_data):
                            scaled = img.scaled(
                                self.album_art.size(),
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation
                            )
                            pixmap = QPixmap.fromImage(scaled)
                            if not pixmap.isNull():
                                self.album_art.setPixmap(pixmap)
                                return True
            
            # If not found in current playback, search for the track
            query = f"track:{title} artist:{artist}"
            results = self.spotify.search(q=query, type='track', limit=1)
            
            if results and results['tracks']['items']:
                track = results['tracks']['items'][0]
                if track['album']['images']:
                    image_url = track['album']['images'][0]['url']
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        img_data = response.content
                        img = QImage()
                        if img.loadFromData(img_data):
                            scaled = img.scaled(
                                self.album_art.size(),
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation
                            )
                            pixmap = QPixmap.fromImage(scaled)
                            if not pixmap.isNull():
                                self.album_art.setPixmap(pixmap)
                                return True
        except Exception as e:
            print(f"Error updating Spotify album art: {e}")
        
        return False

    def seek(self, position):
        """Handle progress slider movement"""
        try:
            if self.spotify and self.current_track:
                # Convert slider position (0-100) to track position in milliseconds
                duration_ms = self.current_track['duration_ms']
                target_position_ms = int((position / 100) * duration_ms)
                
                # Seek to position
                self.spotify.seek_track(target_position_ms)
                
                # Update the UI immediately
                self.progress_slider.setValue(position)
                
                # Force a data update after a short delay
                QTimer.singleShot(100, self.update_data)
        except Exception as e:
            print(f"Error seeking track position: {e}")
            # Revert slider position on error
            if self.current_track:
                current_playback = self.spotify.current_playback()
                if current_playback:
                    progress_ms = current_playback['progress_ms']
                    duration_ms = self.current_track['duration_ms']
                    progress_percent = (progress_ms / duration_ms) * 100
                    self.progress_slider.setValue(int(progress_percent)) 
