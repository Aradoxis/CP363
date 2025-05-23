# Important details
This is a program made for a university course assignment. It refers to a database that is not publicly accessible. This repository was made solely to allow the professor to download the program.
# Installation instructions
Download the zip file. Extract and place wherever in the directory you prefer. 
You must have an installation of [Python](https://www.python.org/downloads/) with the following libraries installed: 
- [mysql connector](https://dev.mysql.com/doc/connector-python/en/connector-python-installation.html)
- [PyQT5](https://pypi.org/project/PyQt5/)
- [requests](https://pypi.org/project/requests/)

Once they are installed, you must open the file named main.py and change the following lines:
- 18 to your username
- 19 to your password
- 20 to your own database’s address.
 
Once that is done, you simply have to navigate to the folder containing the `main.py` file in command prompt and enter: `python main.py`
# Operation instructions
The application is a very simple recreation of Spotify with bare minimum functionality. 

Upon opening the program, enter the email of the account you wish to sign in as.
Upon signing in, the program will launch with the currently listening to or last listened to song of the user. 
On the left side, you can navigate through the user’s library between their saved albums, their owned, shared or saved playlists and their followed podcasts. 
On the bar at the top, the user can search for songs, artists, albums, playlists and podcasts. 
Upon clicking on a track in an album/playlist the user will stop listening to their current song, empty their queue, begin listening to the clicked song and their queue will fill up with random other songs from the currently viewed album/playlist (audio does not play for sake of not committing an act of piracy). 
To exit the app, click the ‘X’ button in the top right corner.
