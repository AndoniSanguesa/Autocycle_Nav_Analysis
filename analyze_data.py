import matplotlib.pyplot as plt
from global_path import plot, find_closest_value_binary, euc_dist
import pygame as pg
import os
import numpy as np
import googlemaps
from googlemaps.maps import *
import datetime
import time

gmaps = googlemaps.Client(key='AIzaSyCtMBSCiR9NlYr_9mOXzVeTMwVI45aAnKs')

pg.init()
display_width = 800
display_height = 600

display = pg.display.set_mode((display_width, display_height))

slider_pos = 0
slider_currently_pressed = False

is_play = False

current_page = "home"
gmaps_map_created = False

time_text = "0:0:0"

def calculate_distance_from_path(data):
    objects, path, des_head, bike_pos, tel_data = data
    ys, xs = zip(*path)
    return find_closest_value_binary([(xs[i], ys[i]) for i in range(len(xs))], bike_pos)

def get_reduced_path(bike_positions):
    new_bike_positions = []
    max_dist = 0.00001
    for pos in bike_positions:
        if not new_bike_positions:
            new_bike_positions.append(pos)
        elif pos != new_bike_positions[-1]:
            new_bike_positions.append(pos)
    return new_bike_positions


def get_google_maps_plot(data):
    sorted_keys = sorted(data.keys())
    bike_positions = []
    for key in sorted_keys:
        objects, path, des_head, bike_pos, tel_data = data[key]
        bike_positions.append((tel_data[9], tel_data[10]))


    bike_positions = get_reduced_path(bike_positions)
    path = StaticMapPath(bike_positions)
    start_marker = StaticMapMarker(bike_positions[0], color="green", label="S")
    end_marker = StaticMapMarker(bike_positions[-1], color="red", label="E")
    markers = [start_marker, end_marker]
    for pos in bike_positions:
        markers.append(StaticMapMarker(pos, "tiny", color="blue"))
    center = [bike_positions[0][0], bike_positions[0][1]]
    zoom = 22
    res = static_map(gmaps, (800, 600), path=path, center=center, zoom=zoom, markers=markers, format='png', maptype="satellite")
    with open('images/map.png', 'wb') as f:
        for i in res:
            f.write(i)


def get_path_plot(data):
    sorted_keys = sorted(data.keys())
    bike_positions = []
    for key in sorted_keys:
        objects, path, des_head, bike_pos, tel_data = data[key]
        bike_positions.append(bike_pos[::-1])

    xs, ys = zip(*bike_positions)
    plt.xlim(min(xs), max(xs))
    plt.ylim(min(ys), max(ys))
    plt.axis('square')
    plt.plot(xs, ys, c='r', linewidth=2)
    plt.savefig("images/path.png", dpi=300)
    plt.cla()


def draw_time_text():
    """Draws a rectangle, then text `time_text` under cursor"""
    mouse_pos = pg.mouse.get_pos()
    box = pg.draw.rect(display, (0, 0, 0), (mouse_pos[0]-5, mouse_pos[1]+10, 100, 20))
    font = pg.font.SysFont("Arial", 15)
    text = font.render(time_text, True, (255, 255, 255))
    text_rect = text.get_rect()
    text_rect.center = box.center
    display.blit(text, text_rect)


def create_ui():
    # Double triangle fast backward button
    fast_back_1 = pg.draw.polygon(display, (0, 0, 0), [(310, 100),
                                                       (330, 80),
                                                       (330, 120)])
    fast_back_2 = pg.draw.polygon(display, (0, 0, 0), [(325, 100),
                                                       (345, 80),
                                                       (345, 120)])
    fast_back = fast_back_1.union(fast_back_2)

    back = pg.draw.polygon(display, (0, 0, 0), [(370, 100),
                                                (390, 80),
                                                (390, 120)])

    forward = pg.draw.polygon(display, (0, 0, 0), [(420, 120),
                                                   (440, 100),
                                                   (420, 80)])

    fast_forward_1 = pg.draw.polygon(display, (0, 0, 0), [(465, 120),
                                                          (485, 100),
                                                          (465, 80)])

    fast_forward_2 = pg.draw.polygon(display, (0, 0, 0), [(480, 120),
                                                          (500, 100),
                                                          (480, 80)])

    fast_forward = fast_forward_1.union(fast_forward_2)

    # play button
    play = pg.draw.polygon(display, (50, 255, 50), [(620, 120),
                                                (640, 100),
                                                (620, 80)])

    # play button outline
    pg.draw.polygon(display, (0, 0, 0), [(620, 120),
                                             (640, 100),
                                             (620, 80)], 3)

    # pause button
    pause_part_1 = pg.draw.rect(display, (255, 50, 50), (660, 80, 10, 40))
    pause_part_2 = pg.draw.rect(display, (255, 50, 50), (680, 80, 10, 40))
    pg.draw.rect(display, (0, 0, 0), (660, 80, 10, 40), 3)
    pg.draw.rect(display, (0, 0, 0), (680, 80, 10, 40), 3)

    pause = pause_part_1.union(pause_part_2)

    # Slide bar
    pg.draw.line(display, (0, 0, 0), (210, 30), (610, 30), 3)

    # Slider
    slider = pg.draw.circle(display, (0, 0, 0), (210+slider_pos, 30), 10)

    map_button = pg.draw.rect(display, (0, 0, 0), (210, 500, 150, 50))
    map_button_text = pg.font.SysFont("Arial", 20).render("Map", True, (255, 255, 255))
    map_button_text_rect = map_button_text.get_rect()
    map_button_text_rect.center = (map_button.centerx, map_button.centery)
    display.blit(map_button_text, map_button_text_rect)

    path_button = pg.draw.rect(display, (0, 0, 0), (460, 500, 150, 50))
    path_button_text = pg.font.SysFont("Arial", 20).render("Path", True, (255, 255, 255))
    path_button_text_rect = path_button_text.get_rect()
    path_button_text_rect.center = (path_button.centerx, path_button.centery)
    display.blit(path_button_text, path_button_text_rect)

    # Display time text above graph
    text = pg.font.SysFont("Arial", 20).render(time_text, True, (0, 0, 0))
    text_rect = text.get_rect()
    text_rect.center = (530, 135)
    display.blit(text, text_rect)
    
    return fast_back, back, forward, fast_forward, slider, map_button, path_button, play, pause


def display_data(data):
    objects, path, des_head, bike_pos, tel_data = data

    data_string = ["state", "phi", "del", "dphi", "ddel", "vel", "torque", "heading", "dheading", "lat", "lon", "met", "accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z"]

    for i in range(len(data_string)):
        text = pg.font.SysFont("Arial", 20).render(f"{data_string[i]}: {tel_data[i]}", True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (20, 100 + i * 25)
        text_rect.right = 160
        display.blit(text, text_rect)


def save_plot(data):
    objects, path, des_head, bike_pos, tel_data = data

    xs = []
    ys = []
    for i in range(len(path)):
        xs.append(path[i][1])
        ys.append(path[i][0])

    for i in range(len(objects)):
        objects[i] = list(map(lambda x: x/1000, objects[i]))
    start_node = (xs[1], ys[1])
    end_node = (xs[-1], ys[-1])
    plot(bike_pos, start_node, end_node, objects, xs, ys, tel_data[7])
    plt.savefig("images/tmp.png", dpi=300)
    plt.cla()


def parse_data(data_file):
    parity = 0
    data = {}
    with open(data_file, 'r') as f:
        for line in f:
            if parity == 0:
                time = float(line)/1e9
            elif parity == 1:
                objects = eval(line)
            elif parity == 2:
                path = eval(line)
            elif parity == 3:
                des_head = float(line)
            elif parity == 4:
                bike_pos = eval(line)
            elif parity == 5:
                tel_data = eval(line)
                if path:
                    data[time] = [objects, path, des_head, bike_pos, tel_data]
            parity = (parity + 1) % 6
    return data


def get_event():
    events = pg.event.get()

    if pg.QUIT in map(lambda x: x.type, events):
        return pg.QUIT

    for event in events:
        return event.type
    return None


def display_img():
    """Displays half size image on centered of display"""
    if current_page == "home":
        if not os.path.exists("images/tmp.png"):
            return
        img = pg.image.load("images/tmp.png")
    elif current_page == "map":
        if not os.path.exists("images/map.png"):
            return
        img = pg.image.load("images/map.png")
    else:
        img = pg.image.load("images/path.png")
    img = pg.transform.scale(img, (int(display_width / 1.5), int(display_height / 1.5)))
    img_rect = img.get_rect()
    img_rect.center = (display_width / 2, display_height / 2)
    display.blit(img, img_rect)


def update_time_text(start, end):
    global time_text
    end_time = datetime.datetime.fromtimestamp(float(end))
    start_time = datetime.datetime.fromtimestamp(float(start))
    diff = end_time - start_time
    minutes = int(diff.seconds / 60)
    seconds = int(diff.seconds % 60)
    microseconds = int(diff.microseconds / 10000)
    time_text = f"{minutes}:{seconds}:{microseconds}"

def main():
    global is_play, slider_pos, slider_currently_pressed, current_page, gmaps_map_created, time_text
    done = False
    
    #data_file = input("Enter data file name: ")
    data_file = "data/2022-3-6/13-19-7.txt"
    data = parse_data(data_file)
    times = list(data.keys())
    cur_data_index = 0
    save_plot(data[times[cur_data_index]])
    new_time = time.time()

    clock = pg.time.Clock()

    while not done:
        display.fill((255, 255, 255))
        event = get_event()
        display_img()

        if current_page == "home":
            display_data(data[times[cur_data_index]])
            fast_back, back, forward, fast_forward, slider, map_button, path_button, play, pause = create_ui()

        # checks if mouse down
        if slider_currently_pressed:
            draw_time_text()
            slider_x, slider_y = pg.mouse.get_pos()
            if slider_x < 210:
                slider_pos = 0
                cur_data_index = 0
            elif slider_x > 610:
                slider_pos = 400
                cur_data_index = len(data) - 1
            else:
                slider_pos = slider_x - 210
                cur_data_index = int((slider_x - 210) / (610 - 210) * (len(data) - 1))

        if is_play and time.time() - new_time > 0.1:
            if cur_data_index < len(data) - 1:
                new_time = time.time()
                save_plot(data[times[cur_data_index]])
                slider_pos = int((cur_data_index / (len(data) - 1)) * 400)
                update_time_text(times[cur_data_index - 1], times[cur_data_index])
                cur_data_index += min(len(data) - cur_data_index - 1, 3)
            else:
                is_play = False

        if event == pg.QUIT:
            done = True
        elif event == pg.MOUSEBUTTONDOWN and current_page == "home":
            if fast_back.collidepoint(pg.mouse.get_pos()):
                cur_data_index = 0
                save_plot(data[times[cur_data_index]])
                slider_pos = 0
            elif back.collidepoint(pg.mouse.get_pos()):
                cur_data_index = max(cur_data_index - 1, 0)
                save_plot(data[times[cur_data_index]])
                slider_pos = int((cur_data_index / (len(data) - 1)) * 400)
                print(times[cur_data_index], calculate_distance_from_path(data[times[cur_data_index]]))
            elif forward.collidepoint(pg.mouse.get_pos()):
                cur_data_index = min(cur_data_index + 1, len(data) - 1)
                save_plot(data[times[cur_data_index]])
                slider_pos = int((cur_data_index / (len(data) - 1)) * 400)
                print(times[cur_data_index], calculate_distance_from_path(data[times[cur_data_index]]))
            elif fast_forward.collidepoint(pg.mouse.get_pos()):
                cur_data_index = len(data) - 1
                save_plot(data[times[cur_data_index]])
                slider_pos = 400
            elif slider.collidepoint(pg.mouse.get_pos()):
                slider_currently_pressed = True
                is_play = False
            elif map_button.collidepoint(pg.mouse.get_pos()):
                if not gmaps_map_created:
                    get_google_maps_plot(data)
                    gmaps_map_created = True
                current_page = "map"
            elif path_button.collidepoint(pg.mouse.get_pos()):
                get_path_plot(data)
                current_page = "path"
            elif play.collidepoint(pg.mouse.get_pos()):
                is_play = True
            elif pause.collidepoint(pg.mouse.get_pos()):
                is_play = False
        elif event == pg.MOUSEBUTTONUP and slider_currently_pressed:
            slider_currently_pressed = False
            save_plot(data[times[cur_data_index]])
        elif event == pg.KEYDOWN:
            current_page = "home"
        update_time_text(times[0], times[cur_data_index])
        pg.display.update()
        clock.tick(60)

    pg.quit()

main()