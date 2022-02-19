import matplotlib.pyplot as plt
import functools
import math
import numpy as np
import cv2

FPS = 60
VIDEO_SIZE = (640, 480)
D_T = 1 / FPS


def get_velocity(speed, heading):
    """
    Outputs velocity vector based on speed and heading

    :param speed: (float) magnitude of the velocity vector
    :param heading:  (float) heading of bike in radians
    :return: (ndarray) size 2 array describing bike velocity in two dimensions
    """

    return speed * np.array([math.cos(heading), math.sin(heading)])


def generate_sinusoid(t, set_point, amplitude, freq):
    """
    Provides a sinusoid function with respect to time.

    :param t: (float) Time in seconds to get speed for
    :param set_point: (float) Desired speed
    :param amplitude: (float) Amplitude of sinusoid
    :param freq: (float) Frequency for sinusoid (in radians!)
    :return: (float) The speed at time `t`
    """

    return math.sin(math.pi*(1/freq)*t)*amplitude + set_point


def update_bike_pos(speed, heading, prev_pos, d_time):
    """
    Updates bike position based on reported speed and heading

    :param speed: (float) speed reported in meters per second
    :param heading: (float) heading of bike reported in radians
    :param prev_pos: (tuple) Previous position of the bicycle
    :param d_time: (float) change in time since last update
    :return: (tuple) Updated position based on sensor inputs
    """

    velocity = get_velocity(speed, heading)
    return prev_pos + (d_time * velocity)


def add_frame_to_video(video, bike_pos, speed, heading, real_objects):
    """
    Adds plotted figure to the video.

    :param video: (VideoWriter) cv2 VideoWriter object
    :param bike_pos: (tuple) position of bike
    :param speed: (float) speed of bike
    :param heading: (float) heading of bike in radians
    :param real_objects: (float) absolute position of objects
    :param pred_objects: (float) predicted position of objects based on sensor inputs
    :return: None
    """

    plt.plot(bike_pos[0], bike_pos[1], 'ro')
    for ind in range(len(real_objects)):
        plt.plot(real_objects[ind][2:], real_objects[ind][:2], c='g')
    plt.quiver(bike_pos[0], bike_pos[1], speed*math.cos(heading), speed*math.sin(heading), color='r')
    plt.savefig('frame.png')
    plt.clf()
    frame = cv2.imread('frame.png')
    video.write(frame)


def main(objects):
    test_duration = 10
    bike_pos = np.array([0, 0])
    speed_fun = functools.partial(generate_sinusoid, set_point=1, amplitude=0.5, freq=5)
    heading_fun = functools.partial(generate_sinusoid, set_point=0, amplitude=0.25 * math.pi, freq=test_duration / 2)

    time = 0

    video = cv2.VideoWriter('global_pos_simulation.mp4', cv2.VideoWriter_fourcc(*'mp4v'), FPS, VIDEO_SIZE)
    add_frame_to_video(video, bike_pos, speed_fun(time), heading_fun(time), objects)

    while time < test_duration:
        speed = speed_fun(time)
        heading = heading_fun(time)
        bike_pos = update_bike_pos(speed, heading, bike_pos, D_T)
        add_frame_to_video(video, bike_pos, speed, heading, objects)
        time += D_T
    video.release()


