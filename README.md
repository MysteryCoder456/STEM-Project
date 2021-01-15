# Car Safety App
An app made to solve children getting stuck in cars. This project was made for a STEM Challenge.

## Prerequisites
You must have Python 3 and the modules listed in `requirements.txt` installed. If you get errors while installing `pyaudio` then:<br>
**Windows:** Do `pip install pipwin` then `pipwin install pyaudio` in Command Prompt<br>
**MacOS:** Install Homebrew, then do `brew install portaudio` in Terminal. After that install pyaudio normally.

## How to run the app
1. Download this project.
2. Open a Terminal or Command Prompt session in the folder where you downloaded this project.
3. Type `cd STEM-Project/client` and press enter.
4. Type `python3 main.py` and press enter.

## How to run the server
Steps are same as running the app except you do `cd STEM-Project/server` instead in step 3.
However there are also different options you can use to enable or disable different functionalities:
1. `--camera-preview` will show you a preview of what the camera sees.
2. `--disable-mic` will disable the microphone functionality.
