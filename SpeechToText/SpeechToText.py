import collections
import contextlib
import io
import pysrt
import json
import os
import sys
import wave
import webrtcvad

from google.cloud import speech
from google.cloud import datastore
from google.cloud.speech import enums
from google.cloud.speech import types
from pydub import AudioSegment


# reads the audio file and check that it has the required number of audio channels, sample width, and sample rate
# returns the sample rate
# wtf is pcm data
def read_wave(path):
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        assert num_channels == 1
        sample_width = wf.getsampwidth()
        assert sample_width == 2
        sample_rate = wf.getframerate()
        assert sample_rate in (8000, 16000, 32000)
        pcm_data = wf.readframes(wf.getnframes())
        return pcm_data, sample_rate


# outputs an audio file
# sets channels, sample width and sample rate
def write_wave(path, audio, sample_rate):
    with contextlib.closing(wave.open(path, 'wb')) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)


# the frame has timestamp, duration and bytes
class Frame(object):
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


# generates Frames to be checked if they have speech
def frame_generator(frame_duration_ms, audio, sample_rate):
    # converting from sample rate into s
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    # duration in seconds
    duration = (float(n) / sample_rate) / 2.0
    # print len(audio)
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n


# here one sets the sample rate(10, 20, or 30), the frame duration in ms

frame_stamps = []


def vad_collector(sample_rate, frame_duration_ms,
                  padding_duration_ms, vad, frames):

    num_padding_frames = int(padding_duration_ms / frame_duration_ms)

    # buffer to store a max number previous frames?
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    triggered = False
    voiced_frames = []

    for frame in frames:

        # print to the Python console
        sys.stdout.write(
            # checks if the frame is speech and returns 1 if so
            '1' if vad.is_speech(frame.bytes, sample_rate) else '0')

        # checks if it's been triggered by speech
        if not triggered:
            ring_buffer.append(frame)
            # how many voiced frames are in the buffer
            num_voiced = len([f for f in ring_buffer
                              if vad.is_speech(f.bytes, sample_rate)])
            # if the number of voiced frames is greater than 90% of the maximum length of the buffer
            # this is to see if there really is speech there
            if num_voiced > 0.9 * ring_buffer.maxlen:
                sys.stdout.write('+(%s)' % (ring_buffer[0].timestamp,))
                frame_stamps.append(float(ring_buffer[0].timestamp))
                triggered = True

                # adds the buffer to the voiced frames
                voiced_frames.extend(ring_buffer)
                ring_buffer.clear()
        # if it was triggered already
        else:
            voiced_frames.append(frame)
            ring_buffer.append(frame)

            # does similar check for unvoiced frames
            num_unvoiced = len([f for f in ring_buffer
                                if not vad.is_speech(f.bytes, sample_rate)])

            # if there's a reliable number of unvoiced frames
            if num_unvoiced > 0.9 * ring_buffer.maxlen:
                sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
                triggered = False

                # here it will return (yield) the joined bytes that make the voiced frames
                yield b''.join([f.bytes for f in voiced_frames])
                # resets the buffer and the voiced frames
                ring_buffer.clear()
                voiced_frames = []

            # if the trigger to record voice was activated

    if triggered:
        sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))

    sys.stdout.write('\n')

    if voiced_frames:
        yield b''.join([f.bytes for f in voiced_frames])

#sends files to the Google Cloud Speech API
def transcribe(which_file, json_to_describe):
    # The name of the audio file to transcribe
    file_name = 'chunk-%s.flac' % str(which_file)

    #    Loads the audio into memory
    with io.open(file_name, 'rb') as audio_file:
        content = audio_file.read()

    audio = types.RecognitionAudio(content=content)

    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=16000,
        language_code='en-US')

    # Detects speech in the audio file
    response = client.recognize(config, audio)

    # appends to our future-to-be json file the start and content
    for result in response.results:
        json_to_describe['transcript'].append(
            {'start': which_file, 'content': format(result.alternatives[0].transcript)})
        # print format(result.alternatives[0].transcript)


def main(args):
    if len(args) != 2:
        sys.stderr.write(
            'Usage: example.py <aggressiveness> <path to wav file>\n')
        sys.exit(1)

    #   the future to be json file
    json_for_export = {}
    json_for_export['transcript'] = []

    # getting the audio (pcm_data) and establishing sample rate
    audio, sample_rate = read_wave(args[1])

    # makes a VAD object and sets its aggressiveness mode
    vad = webrtcvad.Vad(int(args[0]))

    # generates the frames and puts in a list
    frames = frame_generator(20, audio, sample_rate)
    frames = list(frames)

    # puts the frames in segments of speech
    segments = vad_collector(sample_rate, 20, 200, vad, frames)

    # goes through each segment to write a wav file

#   the main loop that will go through each segment, make the files, send them to the Speech API and write the JSON
    for i, segment in enumerate(segments):
        times = str(frame_stamps[i])
        path = 'chunk-%s.wav' % (times)
        print(frame_stamps[i])
        print(' Writing %s' % (path,))
        write_wave(path, segment, sample_rate)

        song = AudioSegment.from_wav('chunk-%s.wav' % (times))
        song.export('chunk-%s.flac' % times, format="flac")

        transcribe(frame_stamps[i], json_for_export)

    # write out the json file containing the
    with open('data.txt', 'w') as outfile:
        json.dump(json_for_export, outfile)

    #here we'll import the new json file and compare it with the subtitles
    #need to write that function
    with open('data.txt') as json_file:
        data = json.load(json_file)

    subtitles = pysrt.open('500days_sub.srt')


if __name__ == '__main__':

    # Instantiates a client for Google cloud
    client = speech.SpeechClient()

    main(sys.argv[1:])
