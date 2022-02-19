from object_simulation import *
import matplotlib.pyplot as plt
import math
import cv2

FPS = 60
VIDEO_SIZE = (640, 480)


def format_plot():
    plt.xlim(-20000, 20000)
    plt.ylim(-10000, 10000)
    plt.grid(True)


def sim_from_tele(tele_file, objects):
    video1 = cv2.VideoWriter("tele_origin_simulation.mp4", cv2.VideoWriter_fourcc(*"mp4v"), FPS, VIDEO_SIZE)
    video2 = cv2.VideoWriter("tele_bike_simulation.mp4", cv2.VideoWriter_fourcc(*"mp4v"), FPS, VIDEO_SIZE)
    bike_pos = (0, 0)
    mod_objects = objects.copy()

    with open(tele_file, 'r') as f:
        lines = f.readlines()
        prev_heading = 0

        ind = 0

        for line in lines:
            if line.startswith("vel"):
                line = "".join(map(lambda x: "" if x.isalpha() else x, lines[ind]))
                speed = float(line)
            elif line.startswith("heading"):
                line = "".join(map(lambda x: "" if x.isalpha() else x, lines[ind]))
                heading = float(line) * math.pi
                mod_objects = predict_object_positions(mod_objects, speed*1000, heading, 0.2, prev_heading)
                bike_pos = update_bike_pos(speed*1000, heading, bike_pos, 0.2)
                pred_objects = reshift_objects(mod_objects, heading, bike_pos)
                prev_heading = heading
                num_frames = 0.2*FPS
                for i in range(int(num_frames)):
                    format_plot()
                    add_frame_to_video(video1, (0, 0), speed, heading, mod_objects, [])
                    format_plot()
                    add_frame_to_video(video2, bike_pos, speed, heading, objects, pred_objects)

            ind += 1
    video1.release()
    video2.release()

objects = [[2000, -2000, 8000, 8000]]
sim_from_tele("stream_log.txt", objects)

