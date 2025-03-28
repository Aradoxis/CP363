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
#==================================================================
# constants
_user = 'root'
_password = 'MySQLLui1$'
_host = '127.0.0.1'
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

# event handling functions



#==================================================================
# class definitions

class MainWindow(QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, *kwargs)
        self.setWindowTitle("Spotify")

        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        
        self.setCentralWidget(label)
        
        

class SignInDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        self.email = None
        
        self.setWindowTitle("Sign In")
        
        QBtn = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        
        self.layout = QVBoxLayout()
        self.message = QLabel("Enter email to sign in:")
        self.line_edit = QLineEdit()
        self.layout.addWidget(self.message)
        self.layout.addWidget(self.line_edit)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
    
    def getID(self):
        query = f"SELECT UserID FROM user_email WHERE Email='{self.email}'"
        rows = execute_query(query)
        if len(rows) > 0:
            return rows[0][0]
        else:
            return None
    
    def done(self, arg__1):
        self.email = self.line_edit.text()
        self.user_id = self.getID()
        if self.user_id is not None:
            super().done(arg__1)
            query = f"SELECT Name FROM user WHERE UserID='{self.user_id}'"
            rows = execute_query(query)
            self.username = rows[0][0]
        else:
            self.message.text = "Enter email to sign in:\nEmail is not registered. Try again."
            self.setLayout(self.layout)
        
class SearchWidget(QWidget):
    
    def __init__(self, parent=None):
        super(SearchWidget, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.search_bar = QLineEdit()
        self.results_list = QListWidget()

        self.search_bar.setPlaceholderText("What do you want to play?")
        self.search_bar.textChanged.connect(self.update_query_string)

        self.layout.addWidget(self.search_bar)
        self.layout.addWidget(self.results_list)
        self.setLayout(self.layout)

        # Timer for delayed execution so not to overload SQL
        self.timer = QTimer()
        self.timer.setInterval(500)  # Delay of 500ms
        self.timer.timeout.connect(self.execute_queries)
        self.timer.setSingleShot(True)  # Ensure the query runs only once per timer

        #store queries for tracks then album then artist
        self.track_query = ""
        self.album_query = ""
        self.artist_query = ""

    def update_query_string(self, text):
        """Updates the query string dynamically as the user types."""
        self.timer.stop()
        self.track_query = f"SELECT Name FROM track WHERE Name LIKE '%{text}%' LIMIT 10"
        self.album_query = f"SELECT Name FROM album WHERE Name LIKE '%{text}%' LIMIT 10"
        self.artist_query = f"SELECT Name FROM artist WHERE Name LIKE '%{text}%' LIMIT 10"

        # for testing to makes sure queries are correct
        print(self.track_query)
        print(self.album_query)
        print(self.artist_query)

    
        self.timer.start()  # Restart the timer

    def execute_queries(self):
        """Execute all stored query strings and display results with breaks between categories."""
        self.timer.stop()  # Stop the timer to prevent duplicate execution

        self.results_list.clear()  # Clear previous results

        # Execute track query
        if self.track_query.strip():
            track_rows = execute_query(self.track_query)
            if track_rows:
                self.results_list.addItem("------ Tracks ------")  # Add a header for tracks
                for row in track_rows:
                    self.results_list.addItem(f"{row[0]}")

        # Execute album query
        if self.album_query.strip():
            album_rows = execute_query(self.album_query)
            if album_rows:
                self.results_list.addItem("")  # Add an empty row as a visual gap
                self.results_list.addItem("------ Albums ------")  # Add a header for albums
                for row in album_rows:
                    self.results_list.addItem(f"{row[0]}")

        # Execute artist query
        if self.artist_query.strip():
            artist_rows = execute_query(self.artist_query)
            if artist_rows:
                self.results_list.addItem("")  # Add an empty row as a visual gap
                self.results_list.addItem("------ Artists ------")  # Add a header for artists
                for row in artist_rows:
                    self.results_list.addItem(f"{row[0]}")

#==================================================================
# global variables

disclaimer = "Disclaimer:\nThis program is made with little to no error checking due to time constraints.\nPlease be informed that any correctly written/valid queries will work fine but\nan incorrectly written/invalid query will cause the program to exit with an error\n(e.g if a user specifies that a foreign key references a nonexistent table or\ntries to drop a table with foreign keys referencing it)."

query = None
rows = None
sign_in_type = None
email = None

user_id = None
username = None
current_listen_type = None
current_track_id = None
current_track_name = None
current_episode_id = None
current_episode_name = None
current_show_name = None
library = []

conn = make_connection()

if conn and conn.is_connected():


    app = QApplication(sys.argv) # create application

    #sign_in = SignInDialog()
    #sign_in.exec()

    window = MainWindow() # create main UI window
    window.setCentralWidget(SearchWidget())

    window.show()
    app.exec_()

    print(f"========================================\nSigned in as: {username}")


#==================================================================
# the no longer

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
        
    elif sign_in_type == 1:
        
        # fetching currently playing
        query = f"SELECT Item_Type, TrackID, EpisodeID FROM queued_item q WHERE PlayerID = '{user_id}'"
        rows = execute_query(query)
        if len(rows) > 0:
            current_listen_type = rows[0][0]
            current_track_id = rows[0][1]
            current_episode_id = rows[0][2]
        if current_listen_type: #track
            query = f"SELECT t.Name, a.Name FROM track t JOIN credited c ON t.TrackID = c.TrackID JOIN artist a ON c.ArtistID = a.ArtistID WHERE t.TrackID = '{current_track_id}'"
            rows = execute_query(query)
            current_track_name = rows[0][0]
            current_artist_names = []
            for row in rows:
                current_artist_names.append(row[1])
                current_artist_names_string = ', '.join(current_artist_names)
            print(f"Current song: {current_track_name} by {current_artist_names_string}")
        else: #episode
            query = f"SELECT e.Name, s.Name FROM episode e JOIN shows s ON e.ShowID = s.ShowID WHERE EpisodeID = '{current_episode_id}'"
            rows = execute_query(query)
            if len(rows) > 0:
                current_episode_name = rows[0][0]
                current_show_name = rows[0][1]
                print(f"Current episode: {current_episode_name} from {current_show_name}")
        # end of fetching currently playing
        
        print("========================================\nYour library:")
        
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
        
        # print library
        for i, collection in enumerate(library):
            print(f"{i}: {collection[2]} - {collection[0]}")
        
        print("========================================")
                
        
        
        
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
        
