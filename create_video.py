from save_path import plot_curve
import os
import cv2

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 1
FONT_COLOR = (0,0,0)
THICKNESS = 2
FPS = 60


def create_frame(objects, path, heading, des_heading, img_path):
    tmp_path = "tmp_img.jpg"
    plot_curve(objects, path, name=tmp_path)
    img = cv2.imread("tmp_img.jpg")
    cv2.putText(img, f"heading: {heading}", (40, 30), FONT, FONT_SCALE, FONT_COLOR, THICKNESS)
    cv2.putText(img, f"des_heading: {des_heading}", (40,70), FONT, FONT_SCALE, FONT_COLOR, THICKNESS)
    cv2.imwrite(img_path, img)


def create_video(name):
    img_path = "./images/"
    video_path = "./videos/"
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    with open(name, "r") as f:
        next_line = f.readline()
        parity = 0
        time = None
        objects = None
        path = None
        cnt = 0
        prev_time = -1
        while next_line:
            if parity == 0:
                time = next_line[:-1]
                prev_time = int(time)
            elif parity == 1:
                # objects = eval(next_line)
                objects = list(map(lambda x: eval(x+")"), next_line[1:-4].split(") ")))
            elif parity == 2:
                # path = eval(next _line)
                path = list(map(lambda x: eval(x+")"), next_line[1:-4].split(") ")))

                # TEMPORARY BECAUSE I RECORDED DATA BAD
                for ind in range(len(path)):
                    path[ind] = (path[ind][1], path[ind][0])
            elif parity == 3:
                print(f"Fuck {cnt}")
            elif parity == 4:
                print(next_line[1:-3].split())
                data = list(map(float, next_line[1:-3].split()))
                heading = data[7]
                des_heading = 0
                try:
                    if (int(time) - prev_time) / 10e9 >= 0.1:
                        create_frame(objects, path, heading, des_heading, f"{img_path}{time}.jpg")
                except TypeError:
                    break
                cnt += 1
                parity = -1
            parity += 1
            next_line = f.readline()

    files = list(os.listdir(img_path))
    files.sort(key=lambda x: int(x[:-4]))

    first_image = cv2.imread(img_path+files[0])
    frame_size = first_image.shape[:2]
    output = cv2.VideoWriter(f"{video_path}/{files[0][:-4]}.avi", cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), FPS, frame_size[::-1])

    for ind in range(len(files)-1):
        cur_time = float(files[ind][:-4])
        next_time = float(files[ind+1][:-4])
        duration = (next_time - cur_time) / 10e9
        num_frames = int(duration * FPS)
        cur_img = cv2.imread(img_path + files[ind])
        for _ in range(num_frames):
            output.write(cur_img)
    output.release()

create_video("1639491665230541524.txt")

