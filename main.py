'''
===================================================================
Author: Dylan Baker
Date:   2025-03-07
===================================================================
'''
#==================================================================
# imports
import mysql.connector
from mysql.connector import errorcode
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import requests
#==================================================================
# constants
_user = 'rue'
_password = 'password'
_host = '192.168.2.182'
_database = 'spotifydb'
#==================================================================
# sql functions

def make_connection():
    try:
        return mysql.connector.connect(user=_user, password=_password, host=_host, database=_database)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    return None

def execute_query(query):
    with conn.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
    return rows

def column_names(table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [column[0] for column in cursor.description]
    cursor.fetchall()
    cursor.close()
    return columns

#==================================================================
# general functions

def get_library():
    
    library = []
    
    # fetch playlists
    query = f"""SELECT 'Playlist' AS Type, p.PlaylistID, p.Name 
    FROM playlist p 
    LEFT JOIN saves_p s ON p.PlaylistID = s.PlaylistID 
    LEFT JOIN collaborates c ON p.PlaylistID = c.PlaylistID 
    WHERE p.OwnerID = '{user_id}' OR s.UserID = '{user_id}' OR c.UserID = '{user_id}'"""
    rows = execute_query(query)
    if len(rows) > 0:
        for row in rows:
            library.append(row)
    
    # fetch albums
    query = f"""SELECT 'Album' AS Type, a.AlbumID, a.Name
    FROM album a
    JOIN saves_a s ON a.AlbumID = s.AlbumID
    WHERE s.UserID = '{user_id}'"""
    rows = execute_query(query)
    if len(rows) > 0:
        for row in rows:
            library.append(row)
    
    # fetch shows
    query = f"""SELECT 'Podcast' AS Type, s.ShowID, s.Name 
    FROM shows s
    JOIN follows_s f ON s.ShowID = f.ShowID  
    WHERE f.UserID = '{user_id}'"""
    rows = execute_query(query)
    if len(rows) > 0:
        for row in rows:
            library.append(row)
    
    return library

def get_current_playing_state():
    current_listen_type = None
    current_track_id = None
    current_episode_id = None
    current_track_name = None
    current_artist_names = None
    current_episode_name = None
    current_show_name = None
    current_duration = None
    query = f"SELECT Item_Type, TrackID, EpisodeID FROM queued_item q WHERE PlayerID = '{user_id}'"
    rows = execute_query(query)
    if len(rows) > 0:
        current_listen_type = rows[0][0]
        current_track_id = rows[0][1]
        current_episode_id = rows[0][2]
    if current_listen_type == "Track": #track
        query = f"SELECT t.Name, t.Duration, a.Name FROM track t JOIN credited c ON t.TrackID = c.TrackID JOIN artist a ON c.ArtistID = a.ArtistID WHERE t.TrackID = '{current_track_id}'"
        rows = execute_query(query)
        current_track_name = rows[0][0]
        current_duration = rows[0][1]
        current_artist_names = []
        for row in rows:
            current_artist_names.append(row[2])
    elif current_listen_type == "Episode": #episode
        query = f"SELECT e.Name, s.Name FROM episode e JOIN shows s ON e.ShowID = s.ShowID WHERE EpisodeID = '{current_episode_id}'"
        rows = execute_query(query)
        current_episode_name = rows[0][0]
        current_show_name = rows[0][1]
    return current_listen_type, current_track_id, current_episode_id, current_track_name, current_artist_names, current_episode_name, current_show_name, current_duration

def get_player_state():
    query = f"SELECT Collection_Type, AlbumID, PlaylistID, ShowID, Playhead FROM player WHERE PlayerID = '{user_id}'"
    rows = execute_query(query)
    if len(rows) > 0:
        current_collection_type = rows[0][0]
        current_album_id = rows[0][1]
        current_playlist_id = rows[0][2]
        current_show_id = rows[0][3]
        playhead = rows[0][4]
    return current_collection_type, current_album_id, current_playlist_id, current_show_id, playhead

def get_playlist_data(playlist_id):
    playlist_name = None
    playlist_description = None
    playlist_image_link = None
    query = f"SELECT Name, Description, Image_Link FROM playlist WHERE PlaylistID = '{playlist_id}'"
    rows = execute_query(query)
    if len(rows) > 0:
        playlist_name = rows[0][0]
        playlist_description = rows[0][1]
        playlist_image_link = rows[0][2]
    query = f"SELECT t.TrackID, a.Image_Link, t.Name AS Title, a.Name AS Album, u.Name AS Added_By, c.Date_Added, CONCAT(FLOOR(t.duration / 60000), ':', IF (FLOOR(t.duration % 60000 / 1000) < 10, '0', ''), FLOOR(t.duration % 60000 / 1000)) AS Length FROM playlist p INNER JOIN contains_p c ON p.PlaylistID = c.PlaylistID INNER JOIN track t ON c.TrackID = t.TrackID INNER JOIN user u ON c.UserID = u.UserID INNER JOIN album a ON t.AlbumID = a.AlbumID WHERE p.PlayListID = '{playlist_id}'"
    rows = execute_query(query)
    return playlist_name, playlist_description, playlist_image_link, rows

def get_show_data(show_id):
    show_name = None 
    show_about = None
    show_image_link = None
    query = f"SELECT Name, About, Image_Link FROM shows WHERE ShowID = '{show_id}'"
    rows = execute_query(query)
    if len(rows) > 0:
        show_name = rows[0][0]
        show_about = rows[0][1]
        show_image_link = rows[0][2]
    query = f"SELECT EpisodeID, Name, Description, Release_Date, CONCAT(FLOOR(Duration / 60000), ':', IF (FLOOR(Duration % 60000 / 1000) < 10, '0', ''), FLOOR(Duration % 60000 / 1000)) FROM episode WHERE ShowID = '{show_id}'"
    rows = execute_query(query)
    return show_name, show_about, show_image_link, rows

def get_album_data(album_id):
    album_name = None
    album_date = None
    album_type = None
    album_image_link = None
    artist_name = None
    query = f"SELECT al.Name, al.Release_Date, al.Album_Type, al.Image_Link, ar.Name FROM album al JOIN published_a p ON al.AlbumID = p.AlbumID JOIN artist ar ON p.ArtistID = ar.ArtistID WHERE al.AlbumID = '{album_id}'"
    rows = execute_query(query)
    if len(rows) > 0:
        album_name = rows[0][0]
        album_date = rows[0][1]
        album_type = rows[0][2]
        album_image_link = rows[0][3]
        artist_name = rows[0][4]
    query = f"SELECT t.TrackID, t.Name AS Title, sum(l.Count) AS Plays, CONCAT(FLOOR(t.duration / 60000), ':', IF (FLOOR(t.duration % 60000 / 1000) < 10, '0', ''), FLOOR(t.duration % 60000 / 1000)) AS Length FROM album a INNER JOIN track t ON a.AlbumID = t.AlbumID LEFT JOIN listens_to_t l ON t.TrackID = l.TrackID WHERE a.AlbumID = '{album_id}' GROUP BY t.TrackID"
    rows = execute_query(query)
    return album_name, album_date, album_type, album_image_link, artist_name, rows

def set_focused_collection(type, id):
    for i in reversed(range(focusarea_layout.count())): 
        focusarea_layout.itemAt(i).widget().setParent(None)
    
    if type == "Playlist":
        playlist_name, playlist_description, playlist_image_link, rows = get_playlist_data(id)
        
        title_label = QLabel(playlist_name)
        title_label.setFont(titlefont)
        focusarea_layout.addWidget(title_label)
        
        detail_label = QLabel(playlist_description)
        detail_label.setFont(strongfont)
        detail_label.setWordWrap(True)
        focusarea_layout.addWidget(detail_label)
        
        for row in rows:
            tb = TrackButton(f"{row[2]:50} {row[3]:50} {row[4]:20} {row[5]} {row[6]:>10}", row[0])
            focusarea_layout.addWidget(tb)
        
    elif type == "Album":
        album_name, album_date, album_type, album_image_link, artist_name, rows = get_album_data(id)
        
        title_label = QLabel(album_name)
        title_label.setFont(titlefont)
        focusarea_layout.addWidget(title_label)
        
        detail_label = QLabel(f"{artist_name} - {album_date} - {album_type}")
        detail_label.setFont(strongfont)
        focusarea_layout.addWidget(detail_label)
        
        for row in rows:
            if row[2] is not None:
                tb = TrackButton(f"{row[1]:100}     {row[2]:20}     {row[3]:6}", row[0])
            else:
                tb = TrackButton(f"{row[1]:100}                              {row[3]:6}", row[0])
            focusarea_layout.addWidget(tb)
            
    elif type == "Podcast":
        show_name, show_about, show_image_link, rows = get_show_data(id)
        
        title_label = QLabel(show_name)
        title_label.setFont(titlefont)
        focusarea_layout.addWidget(title_label)
        
        detail_label = QLabel(show_about)
        detail_label.setFont(strongfont)
        detail_label.setWordWrap(True)
        focusarea_layout.addWidget(detail_label)
        
        for row in rows:
            eb = EpisodeButton(row[1], row[2], row[3], row[4], row[0])
            focusarea_layout.addWidget(eb)

#==================================================================
# event handling functions

def update_search_query_string(text):
    """Updates the query string dynamically as the user types."""
    search_timer.stop()
    global track_query, album_query, artist_query, playlist_query, show_query
    track_query = f"SELECT Name FROM track WHERE Name LIKE '%{text}%' LIMIT 10"
    album_query = f"SELECT Name FROM album WHERE Name LIKE '%{text}%' LIMIT 10"
    artist_query = f"SELECT Name FROM artist WHERE Name LIKE '%{text}%' LIMIT 10"
    playlist_query = f"SELECT Name FROM playlist WHERE Name LIKE '%{text}%' LIMIT 10"
    show_query = f"SELECT Name FROM shows WHERE Name LIKE '%{text}%' LIMIT 10"

    search_timer.start()  # Restart the timer

def execute_search_queries():
    """Execute all stored query strings and display results with breaks between categories."""
    # clear focusarea
    for i in reversed(range(focusarea_layout.count())): 
        focusarea_layout.itemAt(i).widget().setParent(None)
    
    search_timer.stop()  # Stop the timer to prevent duplicate execution
    
    results_list = QListWidget() # make new list

    # Execute track query
    if track_query.strip():
        track_rows = execute_query(track_query)
        if track_rows:
            results_list.addItem("------ Tracks ------")  # Add a header for tracks
            for row in track_rows:
                results_list.addItem(f"{row[0]}")

    # Execute artist query
    if artist_query.strip():
        artist_rows = execute_query(artist_query)
        if artist_rows:
            results_list.addItem("")  # Add an empty row as a visual gap
            results_list.addItem("------ Artists ------")  # Add a header for artists
            for row in artist_rows:
                results_list.addItem(f"{row[0]}")

    # Execute album query
    if album_query.strip():
        album_rows = execute_query(album_query)
        if album_rows:
            results_list.addItem("")  # Add an empty row as a visual gap
            results_list.addItem("------ Albums ------")  # Add a header for albums
            for row in album_rows:
                results_list.addItem(f"{row[0]}")
                
    # Execute playlist query
    if playlist_query.strip():
        playlist_rows = execute_query(playlist_query)
        if playlist_rows:
            results_list.addItem("")  # Add an empty row as a visual gap
            results_list.addItem("------ Playlists ------")  # Add a header for albums
            for row in playlist_rows:
                results_list.addItem(f"{row[0]}")
    
    # Execute show query
    if show_query.strip():
        show_rows = execute_query(show_query)
        if show_rows:
            results_list.addItem("")  # Add an empty row as a visual gap
            results_list.addItem("------ Shows ------")  # Add a header for albums
            for row in show_rows:
                results_list.addItem(f"{row[0]}")
    
    focusarea_layout.addWidget(results_list)

#==================================================================
# class definitions

class SignInDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        self.email = None
        self.user_id = None
        self.username = None
        self.image_link = None
        
        self.setWindowTitle("Sign In")
        
        QBtn = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        
        self._layout = QVBoxLayout()
        self.message = QLabel("Enter email to sign in:")
        self.line_edit = QLineEdit()
        self._layout.addWidget(self.message)
        self._layout.addWidget(self.line_edit)
        self._layout.addWidget(self.buttonBox)
        self.setLayout(self._layout)
        self.setStyleSheet("SignInDialog { margin: 10ex; }")
    
    def getID(self):
        query = f"SELECT UserID FROM user_email WHERE Email='{self.email}'"
        rows = execute_query(query)
        if len(rows) > 0:
            return rows[0][0]
        else:
            return None
    
    def accept(self):
        self.email = self.line_edit.text()
        self.user_id = self.getID()
        if self.user_id is not None:
            query = f"SELECT Name, Image_Link FROM user WHERE UserID='{self.user_id}'"
            rows = execute_query(query)
            self.username = rows[0][0]
            self.image_link = rows[0][1]
            global user_id, username, user_image_link
            user_id = self.user_id
            username = self.username
            user_image_link = self.image_link
            super().accept()
        else:
            self.message.setText("Enter email to sign in:\nEmail is not registered. Try again.")
            self.setLayout(self._layout)
    
    def reject(self):
        self.close()
        conn.close()
        sys.exit(0)
              
class LibraryButton(QPushButton):
    
    def __init__(self, text, type, id):
        super(QPushButton, self).__init__(text)
        self.type = type
        self.id = id
    
    def click_event(self):
        set_focused_collection(self.type, self.id)

class TrackButton(QPushButton):
    
    def __init__(self, text, id):
        super(QPushButton, self).__init__(text)
        self.id = id
    
    def click_event(self):
        return

class EpisodeButton(QWidget):
    
    def __init__(self, title, desc, date, duration, id):
        super(QWidget, self).__init__()
        self.id = id
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        button = QWidget()
        layout.addWidget(button)
        interior_layout = QVBoxLayout()
        button.setStyleSheet("border: 1px solid black;")
        
        title_label = QLabel(title)
        title_label.setFont(subtitlefont)
        title_label.setStyleSheet("border: 0px;")
        interior_layout.addWidget(title_label)
        
        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("border: 0px;")
        interior_layout.addWidget(desc_label)
        
        detail_label = QLabel(f"Published: {date}   Duration: {duration}")
        detail_label.setFont(boldfont)
        detail_label.setStyleSheet("border: 0px;")
        interior_layout.addWidget(detail_label)
        
        button.setLayout(interior_layout)
        
    def click_event(self):
        return

class ResultButton(QPushButton):
    def __init__(self, text, type, id):
        super(QPushButton, self).__init__(text)
        self.type = type
        self.id = id
    
    def click_event(self):
        if self.type in ["Album", "Playlist", "Podcast"]:
            set_focused_collection(self.type, self.id)
        elif self.type == "Track":
            pass
        elif self.type == "Episode":
            pass
        elif self.type == "User":
            pass
#==================================================================
# global variables

disclaimer = "Disclaimer:\nThis program is made with little to no error checking due to time constraints.\nPlease be informed that any correctly written/valid queries will work fine but\nan incorrectly written/invalid query will cause the program to exit with an error\n(e.g if a user specifies that a foreign key references a nonexistent table or\ntries to drop a table with foreign keys referencing it)."

query = None
rows = None
email = None

user_id = None
username = None
user_image_link = None
current_listen_type = None
current_track_id = None
current_episode_id = None
library = []
viewed_playlist_id = None
viewed_album_id = None
viewed_show_id = None
viewed_artist_id = None

#store queries for tracks then album then artist
track_query = ""
album_query = ""
artist_query = ""
playlist_query = ""
show_query = ""

#==================================================================
# fonts
titlefont = QFont()
titlefont.setPointSize(24)
titlefont.setBold(True)

subtitlefont = QFont()
subtitlefont.setPointSize(16)
subtitlefont.setBold(True)

strongfont = QFont()
strongfont.setPointSize(12)
strongfont.setBold(False)

boldfont = QFont()
boldfont.setBold(True)

#==================================================================
# main executing code

conn = make_connection()

if conn and conn.is_connected():

    app = QApplication(sys.argv) # create application

    sign_in = SignInDialog()
    sign_in.exec()
    
    ##################################################################################
    #                                    OverBar                                     #
    ##################################################################################
    #               #                                                                # \
    #               #                                                                #  |
    #               #                                                                #  |
    #               #                                                                #  |
    #               #                                                                #  |
    #    SideBar    #                            FocusArea                           #   > MainArea
    #               #                                                                #  |
    #               #                                                                #  |
    #               #                                                                #  |
    #               #                                                                #  |
    #               #                                                                #  |
    #               #                                                                # /
    ##################################################################################
    #                                                                                #             
    #                                   UnderBar                                     #
    ##################################################################################
    
    window = QWidget()
    window_layout = QVBoxLayout()
    
    # window pieces
    overbar_layout = QHBoxLayout()
    mainarea_layout = QHBoxLayout()
    underbar_layout = QHBoxLayout()
    overbar = QWidget()
    underbar = QWidget()
    overbar.setLayout(overbar_layout)
    underbar.setLayout(underbar_layout)
    window_layout.addWidget(overbar)
    window_layout.addLayout(mainarea_layout)
    window_layout.addWidget(underbar)
    window.setLayout(window_layout)
    window.setFixedWidth(1280)
    window.setFixedHeight(720)
    window.setWindowTitle("Spotify")
    # window pieces end
    
    # main area pieces
    sidebar_layout = QVBoxLayout()
    focusarea_layout = QVBoxLayout()
    sidebar = QWidget()
    focusarea = QScrollArea()
    sidebar.setLayout(sidebar_layout)
    focusarea.setLayout(focusarea_layout)
    mainarea_layout.addWidget(sidebar)
    mainarea_layout.addWidget(focusarea)
    # main area pieces end
    
    # overbar pieces
    searchbar = QLineEdit()
    searchbar.setPlaceholderText("What do you want to play?")
    searchbar.textChanged.connect(update_search_query_string)
    search_timer = QTimer()
    search_timer.setInterval(500)  # Delay of 500ms
    search_timer.timeout.connect(execute_search_queries)
    search_timer.setSingleShot(True)  # Ensure the query runs only once per timer
    
    pixmap = QPixmap()
    user_image = QLabel()
    if user_image_link is not None:
        pixmap.loadFromData(requests.get(user_image_link)._content)
        pixmap = pixmap.scaledToHeight(40)
        user_image.setPixmap(pixmap)
    username_label = QLabel(username)
    username_label.setFont(subtitlefont)
    overbar_layout.addWidget(searchbar)
    overbar_layout.addWidget(user_image)
    overbar_layout.addWidget(username_label)
    overbar.setFixedHeight(60)
    # overbar pieces end
    
    # sidebar pieces
    sidebar.setStyleSheet("border: 1px solid black;")
    library_label = QLabel("Your Library")
    library_label.setFont(subtitlefont)
    library_label.setFixedHeight(40)
    library_label.setStyleSheet("border: 0;")
    sidebar_layout.addWidget(library_label)
    library = get_library()
    for collection in library:
        lb = LibraryButton(f"{collection[2]} - {collection[0]}", collection[0], collection[1])
        lb.setStyleSheet("padding: 5px;")
        lb.setFont(boldfont)
        lb.clicked.connect(lb.click_event)
        sidebar_layout.addWidget(lb)
    sidebar.setFixedWidth(300)
    
    # sidebar pieces end
    
    # underbar pieces
    current_listen_type, current_track_id, current_episode_id, current_track_name, current_artist_names, current_episode_name, current_show_name, current_duration = get_current_playing_state()
    current_collection_type, current_album_id, current_playlist_id, current_show_id, playhead = get_player_state()
    current_label = QLabel()
    trackbar = QProgressBar()
    if current_listen_type is not None:
        if current_listen_type == "Track":
            current_label.setText(f"{current_track_name} - {', '.join(current_artist_names)}")
        elif current_listen_type == "Episode":
            current_label.setText(f"{current_episode_name} - {current_show_name}")
        trackbar.setMaximum(current_duration)
        trackbar.setValue(playhead)
    
    underbar_layout.addWidget(current_label)
    underbar_layout.addWidget(trackbar)
    underbar.setFixedHeight(100)
    # underbar pieces end
    
    # focusarea pieces
    if current_collection_type is None:
        filler = QLabel("Get Started")
        filler_subtext = QLabel("Search for something to listen to or chose something from your library.")
    elif current_collection_type == "Playlist":
        viewed_playlist_id = current_playlist_id
        set_focused_collection(current_collection_type, viewed_playlist_id)
    elif current_collection_type == "Album":
        viewed_album_id = current_album_id
        set_focused_collection(current_collection_type, viewed_album_id)
    elif current_collection_type == "Podcast":
        viewed_show_id = current_show_id
        set_focused_collection(current_collection_type, viewed_show_id)
        
    
    # focusarea pieces end
    
    
    
    window.show()
    app.exec_()
    

sys.exit(0)
#==================================================================
# the no longer

sign_in_type = None
if conn and conn.is_connected():
    #sign_in_type = int(input("Enter 0 to sign in as Admin, 1 to sign in as a User, 2 to sign in as an Artist: "))
    if sign_in_type == 0:
        
        querying = True
        choice = None
        
        while querying:
            print("========================================\nSpotify Admin\n========================================")
            print("What would you like to do?")
            print("0 - Execute a general query")
            print("1 - Create a table")
            print("2 - Drop a table")
            print("3 - Insert data")
            print("4 - Update data")
            print("5 - Delete data")
            print("q - Quit")
            print("========================================")
            choice = input("Enter: ").lower()
            print("========================================")
            if choice == "q":
                querying = False
            elif choice == "0":
                query = input("Enter query: ")
                rows = execute_query(query)
                if len(rows) > 0:
                    for row in rows:
                        print(row)
                input("Enter to return:")
            elif choice == "1":
                print("Table Creation")
                table_name = input("Enter table name: ")
                columns = []
                adding_columns = True
                while adding_columns:
                    column = ""
                    column_name = input("Enter column name: ")
                    column_datatype = input("Enter column datatype: ")
                    column = column_name + " " + column_datatype
                    if input("Is column the Primary Key? (y/n): ").lower() == "y":
                        column += " PRIMARY KEY"
                    if input("Is column Not Null? (y/n): ").lower() == "y":
                        column += " NOT NULL"
                    if input("Is column Unique? (y/n): ").lower() == "y":
                        column += " UNIQUE"
                    if input("Does column have a default? (y/n): ").lower() == "y":
                        column += " DEFAULT " + input("What is the default value for column? (use single quotes for strings): ")
                    if input("Is column a Foreign Key? (y/n): ").lower() == "y":
                        fk_table = input(f"Enter table that column references: ")
                        fk_column = input(f"Enter the column in {fk_table} that column references: ")
                        column += f" REFERENCES {fk_table}({fk_column})"
                        
                    columns.append(column)
                    if input("Would you like to add more columns? (y/n): ").lower() != "y":
                        adding_columns = False

                columns_string = ", ".join(columns)
                query = f"""CREATE TABLE {table_name} ({columns_string}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"""
                print(f"========================================\nFinalized command:\n{query}\n========================================")
                if input("Confirm table creation (y) or cancel (n): ").lower() == "y":
                    execute_query(query)
                
            elif choice == "2":
                print("Table Deletion")
                table_name = input("Enter table name: ")
                query = f"DROP TABLE {table_name}"
                print(f"========================================\nFinalized command:\n{query}\n========================================")
                if input("Confirm table deletion (y) or cancel (n): ").lower() == "y":
                    execute_query(query)
                    
            elif choice == "3":
                print("Data Insertion")
                table_name = input("Enter table name: ")
                columns = column_names(table_name)
                columns_string = ", ".join(f"`{column}`" for column in columns)
                query = f"INSERT INTO {table_name} ({columns_string}) VALUES ("
                for column in columns:
                    value = input(f"Enter a value for the column `{column}` (use single quotes for strings): ")
                    if column == columns[0]:
                        query += value
                    else:
                        query += ", " + value
                query += ")"
                print(f"========================================\nFinalized command:\n{query}\n========================================")
                if input("Confirm data insertion (y) or cancel (n): ").lower() == "y":
                    execute_query(query)
            
            elif choice == "4":
                print("Data Updating")
                table_name = input("Enter table name: ")
                changed_column = input("Enter column to change: ")
                new_value = input("Enter value to change column to (use single quotes for strings): ")
                condition_column = input("Enter column to check for conditional updating: ")
                condition_value = input("Enter the value to compare the condition column to (use single quotes for strings): ")
                operator = input("Enter the comparison operator (=)(<)(>)(>=)(<=)(<>): ")
                query = f"UPDATE {table_name} SET {changed_column} = {new_value} WHERE {condition_column} {operator} {condition_value}"
                print(f"========================================\nFinalized command:\n{query}\n========================================")
                if input("Confirm data update (y) or cancel (n): ").lower() == "y":
                    execute_query(query)
                
            elif choice == "5":
                print("Data Deletion")
                table_name = input("Enter table name: ")
                condition_column = input("Enter column to check for conditional updating: ")
                condition_value = input("Enter the value to compare the condition column to (use single quotes for strings): ")
                operator = input("Enter the comparison operator (=)(<)(>)(>=)(<=)(<>): ")
                query = f"DELETE FROM {table_name} WHERE {condition_column} {operator} {condition_value}"
                print(f"========================================\nFinalized command:\n{query}\n========================================")
                if input("Confirm data deletion (y) or cancel (n): ").lower() == "y":
                    execute_query(query)
        
    # What Assignment 6 asks for ends here.
    # However I misunderstood at first and started making a CLI version of Spotify down below. It only shows the signed in user's current listening and library
    
    elif sign_in_type == "2":
        
        artist_name = None
        
        while artist_name is None:
            email = input("Enter email: ")
            query = f"SELECT ArtistID, Name FROM artist WHERE Email='{email}'"
            rows = execute_query(query)
            if len(rows) > 0:
                artist_id = rows[0][0]
                artistname = rows[0][1]
            else:
                print("Email is not registered. Try again.")
                email = input("Enter email: ")
        
        print(f"========================================\nSigned in as: {artist_name}")
    
    conn.close()
        
