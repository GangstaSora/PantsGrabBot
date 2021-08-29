# PantsGrabBot
A Twitch bot that creates a point system for creating pyramids and partakes in a variety of TFT community memes.
Contact GangstaSora#2657 on discord to add the bot to your channel. 

## Contributing
Contributions are welcome. There are no strict guidelines, pull requests that meet the bar of exisiting code will be accepted. PantGrabBot should be fun, make any teasing lighthearted, and should not do anything to get banned. Feel free to reach out on discord (GangstaSora#2657) to discuss features and whether or not they would be acceptable. 

## Installation/Setup for development
Designed to be run in a Linux environment. There's nothing obvious should prevent running in Windows or MacOS, but this is untested and mileage may vary.

Prerequisites: Python 3.8, SQLite

1. Clone the repo and `cd` into the root directory. All commands will be run from here.
2. Run `pip install -r requirements.txt` to install python dependencies (Optionally, create a python virtual environment to do this first)
3. Obtain an oath token, client id, and client secret for the twitch account to test/run the bot. This article has good instructions for doing this https://dev.to/ninjabunny9000/let-s-make-a-twitch-bot-with-python-2nd8
4. Copy the "config_example.ini" file to config.ini and input the credentials from step 3. Also put in the channel name of the chat you want to test the bot in. 
5. Running `python pantsgrabbot.py` will run the bot in debug mode on the provided channel. 
