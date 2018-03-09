# Author: Flomeister
import sys
import numpy as np


def open_file(path):

    content=[]
    with open(path, 'r') as open_file:
        for i, line in enumerate(open_file):
            content.append(line.strip())

    return content


current_time = open_file('/Users/florin/Desktop/Analysis/current_time_real.txt')
current_time = current_time[1:]
landmarks = open_file('/Users/florin/Desktop/Analysis/03-03-18mov001.txt')
# the landmarks are times when the movie stopped and played
landmarks = landmarks[1:]

# gives us 'capsules' that contain all time time points in the movie presented in that second, down to the 100ms accuracy 
# also matches the first TTL pulse and the stops to see when periods started and which capsules it contained
def construct_movie_times(movie_positions, periods):

    # the capsule construction part
    # -----------------------------
    second_x = []
    capsule = [[float(movie_positions[0]['movie point']), int(movie_positions[0]['ms'])]]
    
    # need to initialise started to something

    for i in range(1, len(movie_positions)):

        temp = movie_positions[i-1]['seconds']

        if movie_positions[i]['seconds'] == temp:
            
            capsule.append([float(movie_positions[i]['movie point']), int(movie_positions[i]['ms'])])

            if started == False:
                sec = temp
                started = True

        else:
            sec = movie_positions[i-1]['seconds']
            second_x.append({'second': sec, 'points': capsule})
            capsule = [[float(movie_positions[i]['movie point']), int(movie_positions[i]['ms'])]]
            started = False

    # the matching part - checks against the pause time for that period and gives all movie times until then, with ms from the last second
    # these are all aligned according to the seconds from epoch, not the actual time
    # -----------------

    # TO DO
    # take from the timepoint when the first TTL pulse was shot and from where the movie was played, 1000ms to cover a second and see what fits in the capsule
    # in other words, make the capsules according to absolute time, not epoch time

    for j in range(len(periods)-1):

        for i in range(len(second_x)):

            if periods[j]['start_sec'] == int(second_x[i]['second']):
                
                c = int(periods[j]['start_sec'])
                it = 0
                # print periods[j+1]['start_sec']
                # print periods[j]['stop_sec']
                
                while c <= periods[j]['stop_sec'] and i + it < len(second_x):
                    periods[j]['content'].append(second_x[i+it]['points'])
                    c+=1
                    it+=1

    # return the capsules and the periods with the capsules in them
    return second_x, periods

# returns movie positions in a nice readable format
def movie_positions(current_time):

    movie_positions = []

    for point in current_time:
        movie_positions.append({'movie point': point.split('=')[1], 'seconds': point[:10], 'ms': point[10:13]})

    return movie_positions

# returns periods, their duration and details to later add timepoints to them
def construct_periods(landmarks):

    periods = []
    c=1

    for i, timepoint in enumerate(landmarks):

        # the line with a starting time point will always end in a t
        # take the difference in seconds from the next pause till this starting point
        # update the difference with the ms and put everything in ms

        if timepoint[-1] =='t':

            seconds = int(landmarks[i+1][:10]) - int(timepoint[:10])

           # print 'period: %d' % c
           # print 'seconds: %d' % seconds
           # print '-------------'

            full_duration = seconds *1000 - (1000-int(timepoint[10:13])) + int(landmarks[i+1][10:13])

            periods.append({'period': c, 'duration': full_duration, 'start_sec': int(timepoint[:10]), 'start_ms': timepoint[10:13], 'stop_sec': int(landmarks[i+1][:10]),'content': []})
            c+=1

    print 'Final periods--------------------------'

    for period in periods:
        print 'period: %d' % period['period']
        print 'duration in ms: %d' % period['duration']
        print '--------------'

    return periods

# will somehow query the content for a specific time to then get from the movie 
#def query_me():

periods = construct_periods(landmarks)

movie_points = movie_positions(current_time)

sec_x, p  = construct_movie_times(movie_points, periods)

print 'Period: ', p[0]['period']
print 'Duration in ms: ', p[0]['duration']
print 'First second: ', p[0]['content'][0]
print 'Last second: ', p[0]['content'][-1]

