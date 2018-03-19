# Author: Flomeister
# Best analysis in the entire universe
import sys
import numpy as np
import json


def open_file(path):
    content = []
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
# capsule_limit will change depending on how many checks/second the MRI player will do - in turn this depends on the number of slices
def period_start_times(periods, movie_positions):
    # iterate through each period to make capsules of 1000ms that contain all the movie points within that second
    for period in periods:

        capsules = []
        capsule_limit = 10
        number = 0
        capsule_finished = False

        # absolute_time keeps track of up until where we have to go for each capsule
        absolute_time = [int(period['start_sec']), int(period['start_ms'])]

        # iterate until we find the matching time point
        for i, position in enumerate(movie_positions[1:-10]):

            start_capsule = False
            start_point = [int(position['seconds']), int(position['ms'])]
            # print absolute_time[0], ' ', start_point[0]

            # check the starting second
            if start_point[0] == absolute_time[0]:

                capsule = []

                # we start adding capsules in 2 cases:
                # 1st case - the distance is less to 1000 than the trigger
                # 2nd case - the point will be less than that time

                if 1000 - start_point[1] < 1000 - absolute_time[1]:
                    start_capsule = True
                elif start_point[1] < absolute_time[1]:
                    start_capsule = True

                if start_capsule == True:
                    # we know according to how many slices we've got how many checks per second there will be
                    for j in range(capsule_limit):

                        # first see whether it's within the first half of the second
                        if movie_positions[i + j]['seconds'] == absolute_time[0]:

                            if 1000 - movie_positions[i + j]['ms'] < 1000 - absolute_time[1]:
                                capsule.append([movie_positions[i + j]['ms'], movie_positions[i + j]['movie point']])

                            elif movie_positions[i + j]['ms'] < absolute_time[1]:
                                capsule.append([movie_positions[i + j]['ms'], movie_positions[i + j]['movie point']])

                        # or the other half of the second
                        elif movie_positions[i + j]['seconds'] == absolute_time[0] + 1:

                            if 1000 - movie_positions[i + j]['ms'] > 1000 - absolute_time[1]:
                                capsule.append([movie_positions[i + j]['ms'], movie_positions[i + j]['movie point']])

                    capsules.append({'capsule': number, 'content': capsule})
                    number += 1
                    capsule_finished = True

            if capsule_finished == True:
                absolute_time[0] += 1
                capsule_finished = False

        period['content'] = capsules
        print len(capsules)

    return periods


# returns movie positions in a nice readable format
# the numbers returned are strings so will have to be converted into ints and floats
def movie_positions(current_time):
    movie_positions = []

    for point in current_time:
        movie_positions.append(
            {'movie point': point.split('=')[1], 'seconds': int(point[:10]), 'ms': int(point[10:13])})

    return movie_positions


# returns periods, their duration and details to later add timepoints to them
def construct_periods(landmarks):
    periods = []
    c = 1

    for i, timepoint in enumerate(landmarks):

        # the line with a starting time point will always end in a t
        # take the difference in seconds from the next pause till this starting point
        # update the difference with the ms and put everything in ms

        if timepoint[-1] == 't':
            seconds = int(landmarks[i + 1][:10]) - int(timepoint[:10])

            # print 'period: %d' % c
            # print 'seconds: %d' % seconds
            # print '-------------'

            full_duration = seconds * 1000 - (1000 - int(timepoint[10:13])) + int(landmarks[i + 1][10:13])

            periods.append(
                {'period': c, 'duration': full_duration, 'start_sec': int(timepoint[:10]), 'start_ms': timepoint[10:13],
                 'stop_sec': int(landmarks[i + 1][:10]), 'stop_ms': int(landmarks[i + 1][10:13]), 'content': []})
            c += 1

    print 'Final periods--------------------------'

    for period in periods:
        print 'period: %d' % period['period']
        print 'duration in ms: %d' % period['duration']
        print '--------------'

    return periods


periods = construct_periods(landmarks)

movie_points = movie_positions(current_time)

# adds the capsules to each period
p = period_start_times(periods, movie_points)

with open('capsules.json', 'w') as j:
    json.dump(p, j)

# TO DO
# ----
# Put all the periods in a JSON that will be accessed by a different script
# check with multiple participants to see what times it gives me
# check all the periods for the start and the end
# wrap it up into a main function and add arguments for the files

print 'Period: ', p[1]['period']
print 'Duration in ms: ', p[1]['duration']
print 'First second: ', p[1]['content'][0]
print 'Second second: ', p[1]['content'][-1]
