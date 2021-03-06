# movie

**Video-to-fMRI alignment**
----
Code will use the times recorded while scanning the participant, make periods with their own duration and then add 'capsules' that contain timepoints in the movie within every 1000ms elapsed since the first TTL pulse

Work in progress




**Youtube API calls**
----
You'll have to install the google API python client.

`pip install --upgrade google-api-python-client`


To run the code:
`python YoutubeCall.py NAME OF THE SEARCH`
e.g. Batman Returns scene

**SpeechToText**
----
This will get an audio file, detect speech segments, send them to the Google Cloud Speech API and get a json file back with the content and the start time in seconds.

Functions for splitting the audio into speech segments were adapted from: https://github.com/wiseman/py-webrtcvad (example.py)


Installing ffmpeg: https://github.com/adaptlearning/adapt_authoring/wiki/Installing-FFmpeg  Make sure to install with **ffprobe**

Installing Google Cloud libraries: https://cloud.google.com/sdk/docs/quickstart-mac-os-x

-------------------------------
Input data for SpeechToText.py

We'll need to have .wav files, with 1 audio channel and a sample rate of 8000, 16000 or 32000

Using Terminal to check if our files are alright/convert them:

`ffprobe -v quiet -print_format json -show_format -show_streams 500days1.wav`

`ffmpeg -i 500days1.wav -ac 1 -ab 64000 -ar 16000 500days12.wav`


Make sure to have the input file in the _SpeechToText_ folder

------------------------------------

Make sure to be authenticate with the Google Cloud if planning on transcribing the audio

Comment our the `transcribe` function if not needed

Run SpeechToText.py with aggressivenes as 0, 1, 2 or 3 (the more aggressive, the harsher it will differentiate between speech and non-speech):

`python SpeechToText.py <agressiveness index> <input_file_name>`

----------------------------------------------------------------
Useful commands for processing the video files

To concatenate mp4 files with ffmpeg

`touch files.txt` where you add for each row: file 'path/to/file'

`cat filex.txt` to check files

`ffmpeg -f concat -i files.txt -c copy output_name.mp4`