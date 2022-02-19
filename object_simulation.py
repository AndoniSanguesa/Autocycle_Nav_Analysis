import functools
import math
import numpy as np
import matplotlib.pyplot as plt
import cv2

FPS = 60
VIDEO_SIZE = (640, 480)
D_T = 1 / FPS

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


def get_velocity(speed, heading):
    """
    Outputs velocity vector based on speed and heading

    :param speed: (float) magnitude of the velocity vector
    :param heading:  (float) heading of bike in radians
    :return: (ndarray) size 2 array describing bike velocity in two dimensions
    """

    return speed * np.array([math.cos(heading), math.sin(heading)])


def predict_object_positions(objects, speed, heading, d_time, prev_heading):
    """
    Predicts the position of objects based on speed and heading

    :param objects: (list) list of objects to predict position of
    :param speed: (float) speed of bike
    :param heading: (float) heading of bike in radians
    :param d_time: (float) change in time since last update
    :return: (list) list of predicted positions of objects
    """

    # Get velocity vector
    velocity = get_velocity(speed, heading)
    #prev_velocity = get_velocity(prev_speed, prev_heading)

    tran_objs = []

    d_heading = prev_heading - heading

    velocity = np.array([velocity[0] * math.cos(-heading) - velocity[1] * math.sin(-heading),
                velocity[0] * math.sin(-heading) + velocity[1] * math.cos(-heading)])

    #prev_velocity = np.array([prev_velocity[0] * math.cos(-prev_heading) - prev_velocity[1] * math.sin(-prev_heading),
                              #prev_velocity[0] * math.sin(-prev_heading) + prev_velocity[1] * math.cos(-prev_heading)])

    #acceleration = (velocity - prev_velocity) / d_time
    #acceleration = 0.5 * math.pi/5 * math.cos(math.pi/5 * time)

    # Update
    rot_objects = []

    for obj in objects:
        rot_z1 = math.cos(d_heading) * obj[2] - math.sin(d_heading) * obj[0]
        rot_z2 = math.cos(d_heading) * obj[3] - math.sin(d_heading) * obj[1]

        rot_x1 = math.sin(d_heading) * obj[2] + math.cos(d_heading) * obj[0]
        rot_x2 = math.sin(d_heading) * obj[3] + math.cos(d_heading) * obj[1]
        rot_objects.append([rot_x1, rot_x2, rot_z1, rot_z2])



    #diff = -((velocity * d_time) + (acceleration * d_time**2) / 2)
    diff = -velocity * d_time
    update_vec = [diff[1],
                  diff[1],
                  diff[0],
                  diff[0]]

    #print(diff[0])
    for obj in rot_objects:
        tran_objs.append([obj[i] + update_vec[i] for i in range(4)])

    return tran_objs


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


def reshift_objects(objects, heading, bike_pos):
    """
    Reshifts objects to the correct position based on the heading of the bike

    :param objects: (list) list of objects to readjust position for
    :param heading: (float) heading of bike in radians
    :param bike_pos: (tuple) position of the bike
    :return: (list) list of objects with correct position
    """

    rot_objects = []

    for obj in objects:
        rot_z1 = math.cos(heading) * obj[2] - math.sin(heading) * obj[0]
        rot_z2 = math.cos(heading) * obj[3] - math.sin(heading) * obj[1]

        rot_x1 = math.sin(heading) * obj[2] + math.cos(heading) * obj[0]
        rot_x2 = math.sin(heading) * obj[3] + math.cos(heading) * obj[1]
        rot_objects.append([rot_x1, rot_x2, rot_z1, rot_z2])

    tran_objects = []
    diff = [bike_pos[1], bike_pos[1], bike_pos[0], bike_pos[0]]

    for obj in rot_objects:
        tran_objects.append([obj[i] + diff[i] for i in range(4)])

    return tran_objects

def format_plot():
    """
    Formats pyplot output

    :return: None
    """

    plt.xlim(0, 10)
    plt.ylim(-5, 5)
    plt.grid(True)


def add_frame_to_video(video, bike_pos, speed, heading, real_objects, pred_objects):
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
        if pred_objects:
            plt.plot(pred_objects[ind][2:], pred_objects[ind][:2], c='r')
    plt.quiver(bike_pos[0], bike_pos[1], speed*math.cos(heading), speed*math.sin(heading), color='r')
    plt.savefig('frame.png')
    plt.clf()
    frame = cv2.imread('frame.png')
    video.write(frame)


def get_loss(real_objects, pred_objects):
    """
    Calculates the loss of the model

    :param real_objects: (list) list of objects with absolute position
    :param pred_objects: (list) list of objects with predicted position
    :return: (float) loss of the model
    """

    loss = 0
    for ind in range(len(real_objects)):
        loss += np.sum(np.square(np.array(real_objects[ind]) - np.array(pred_objects[ind])))
    return loss


def main():
    test_duration = 10
    update_obj_off = 10
    speed_fun = functools.partial(generate_sinusoid, set_point=1, amplitude=0.5, freq=5)
    heading_fun = functools.partial(generate_sinusoid, set_point=0, amplitude=0.25*math.pi, freq=test_duration/2)

    objects = [[2, -2, 6, 6]]
    predicted_objects = objects.copy()
    reshifted_objects = objects.copy()

    bike_pos = np.array([0, 0])
    time = 0

    video = cv2.VideoWriter('simulation.mp4', cv2.VideoWriter_fourcc(*'mp4v'), FPS, VIDEO_SIZE)
    add_frame_to_video(video, bike_pos, speed_fun(time), heading_fun(time), objects, predicted_objects)

    prev_heading = -1
    prev_speed = -1

    frames = 0
    average_loss = 0

    while time < test_duration:

        speed = speed_fun(time)
        heading = heading_fun(time)
        bike_pos = update_bike_pos(speed, heading, bike_pos, D_T)
        if (round((time/D_T), 1) % update_obj_off) == 0:
            if prev_heading != -1:
                predicted_objects = predict_object_positions(predicted_objects, speed, heading, D_T*update_obj_off, prev_heading, prev_speed, time)
                reshifted_objects = reshift_objects(predicted_objects.copy(), heading, bike_pos)
                average_loss += get_loss(objects, reshifted_objects)
                frames += 1
            prev_heading = heading
            prev_speed = speed
        add_frame_to_video(video, bike_pos, speed, heading, objects, reshifted_objects)
        time += D_T
    video.release()

    return average_loss/frames

