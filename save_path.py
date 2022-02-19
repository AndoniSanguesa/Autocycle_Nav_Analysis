from matplotlib import pyplot as plt
import matplotlib.patches as patches
from scipy import interpolate as interp
import time
import numpy as np

from scipy import interpolate as interp

tck = []
full_len = 0

def get_dervs(x, acc=0.000001):
    """Calculates the derivatives of the curve"""
    full_len = (sum(interp.splint(0, 1, tck, full_output=0))) * 2
    u = x / full_len
    subs = lambda x: interp.splev(x, tck)
    this_val = subs(u)
    next_val = subs(u + acc)
    prev_val = subs(u - acc)
    return (((next_val[0] - 2 * this_val[0] + prev_val[0]) / (acc ** 2),
             (next_val[1] - 2 * this_val[1] + prev_val[1]) / (acc ** 2)),
            ((this_val[0] - next_val[0]) / acc,
             (this_val[1] - next_val[1]) / acc))


def get_delta(i, vel):
    """Calculates steering angle"""
    global step
    ## Calls the data getter to give us the latest roll
    dervs = get_dervs(i)

    wheel_base = 1
    radius_of_turn = ((dervs[1][0] ** 2 + dervs[1][1] ** 2) ** (3 / 2)) / (
                (dervs[1][0] * dervs[0][1]) - (dervs[1][1] * dervs[0][0]))
    g = 32.2
    load_front_ax = 1
    load_rear_ax = 1
    corn_stiff_front = 1
    corn_stiff_rear = 1

    return wheel_base / radius_of_turn + ((load_front_ax / corn_stiff_front) - (load_rear_ax / corn_stiff_rear)) * (
                (vel ** 2) / (g * radius_of_turn))


def calculate_deltas(data):
    global tck, full_len
    xs = list(data.path_x)
    ys = list(data.path_y)
    xs.insert(0, 0)
    ys.insert(0, 0)
    tck = interp.splprep([xs, ys], s=0.5)[0]
    full_len = interp.splint(0, 1, tck)
    return []


def delta(data):
    return get_delta(data.x, data.roll) if tck else -1

# Size of plot
width = 20
height = 10

# Size of each node
node_size = 0.5

# The dimensions of the graph (how many nodes in each direction)
x_dim = int(width / node_size)
y_dim = int(height / node_size)

# The nodes that have been deemed blocked by an object
blocked_nodes = set()
center_blocked_nodes = set()

# The path being taken
path = []

# Interpolated path
interpolated_path = None

# Starting node
start_node = (y_dim // 2, 0)

# End node
end_node = (y_dim // 2, x_dim-1)

# Heading
desired_heading = 0

# Calculate Padding
padding = 0.5
padding_num = int(padding // node_size)

# Global Angle & Offset
current_heading = 0
off_y = 0
off_x = 0


def get_change(p1, p2):
    """Calculates difference between nodes"""
    return p2[0] - p1[0], p2[1] - p1[1]

def reset_vars():
    """Resets variables between calls"""
    global blocked_nodes, center_blocked_nodes, path, interpolated_path

    # The nodes that have been deemed blocked by an object
    blocked_nodes = set()
    center_blocked_nodes = set()

    # The path being taken
    path = []

    # Interpolated path
    interpolated_path = None


def get_node_from_point(point):
    """Takes cartesian point and returns the corresponding node"""
    x, y = point
    return (
        int(((-y) + (height // 2)) // node_size),
        int(x // node_size)
    )


def get_blocked_nodes(obj):
    """Returns the list of nodes that an object is blocking"""
    x1, x2, y1, y2 = obj
    if x2 < x1:
        tmp = x1
        x1 = x2
        x2 = tmp

        tmp = y1
        y1 = y2
        y2 = tmp

    cur_point = [x1, y1]
    vert = x2 - x1 == 0
    if not vert:
        m = (y2 - y1) / (x2 - x1)
        delta_x = node_size/((1+(m**2))**0.5)
    blocked = set()

    while (cur_point[0] < x2) if not vert else (cur_point[1] < y2):
        node = get_node_from_point(cur_point)
        if node not in center_blocked_nodes:
            cur_blocked = [(node[0]+y, node[1]+x) for y in range(-padding_num, padding_num+1) for x in range(-padding_num, padding_num+1) if 0 <= node[0]+y < y_dim and 0 <= node[1]+x < x_dim]
            blocked.update(cur_blocked)
            center_blocked_nodes.add(node)

        if not vert:
            cur_point = [cur_point[0] + delta_x, cur_point[1] + (m * delta_x)]
        else:
            cur_point[1] += node_size
    node = get_node_from_point([x2, y2])
    if node not in center_blocked_nodes:
        cur_blocked = [(node[0] + y, node[1] + x) for y in range(-padding_num, padding_num + 1) for x in
                       range(-padding_num, padding_num + 1) if (node[0] + y, node[1] + x)]
        blocked.update(cur_blocked)
        center_blocked_nodes.add(node)
    return blocked


def inter_path(path):
    """Creates the interpolated path from the line segments
    generated by the BFS"""

    ys, xs = zip(*path)
    ys = list(ys)
    xs = list(xs)

    xs.insert(0, 0)
    ys.insert(0, 0)
    this_tck, u = interp.splprep([xs, ys], s=0.5)
    return u, this_tck


def plot(obj_lst, path, theta, node_type=0, plot_path=0, save=False, name=""):
    """Plots obstacles, blocked nodes, and curve"""
    fig, ax = plt.subplots()

    # Plots the nodes
    y_diff = np.sin(-desired_heading)*node_size
    x_diff = np.cos(-desired_heading)*node_size
    extra = 5
    for y_ind in range(-extra, y_dim+extra):
        for x_ind in range(x_dim+extra):
            diff_from_angle_x = -np.sin(-desired_heading) * (height / 2)
            diff_from_angle_y = -(height / 2 - extra) + np.cos(-desired_heading) * (height / 2 - extra)
            if node_type == 1:
                # Plots all nodes
                rect = patches.Rectangle((x_ind*x_diff + (y_ind * y_diff) + diff_from_angle_x, (-y_ind*node_size) + (height//2) - node_size + (y_diff * x_ind) + diff_from_angle_y), node_size, node_size, linewidth=1, edgecolor='black', facecolor=("black" if (y_ind, x_ind) in blocked_nodes else "none"), angle=-desired_heading*180/np.pi)
                ax.add_patch(rect)
            elif node_type == 2:
                # Plots only blocked Nodes
                if (y_ind, x_ind) in blocked_nodes:
                    rect = patches.Rectangle((x_ind*x_diff + (y_ind * y_diff) + diff_from_angle_x, (-y_ind*node_size) + (height//2) - node_size + (y_diff * x_ind) + diff_from_angle_y), node_size, node_size, linewidth=1,
                                                edgecolor='black',
                                                facecolor="black")
                    ax.add_patch(rect)

    if plot_path == 1:
        #Plots the path
        f = interpolated_path[1]
        u = np.linspace(0, 1, 1000)
        i = interp.splev(u, f)
        plt.plot(i[0], i[1])
    elif plot_path == 2:
        ys, xs = zip(*path)
        ys = list(ys)
        xs = list(xs)
        xs.insert(0, 0)
        ys.insert(0, 0)
        plt.plot(xs, ys)

    # Plot the obstacles
    for o in obj_lst:
        plt.plot(o[0:2], o[2:], linewidth=3)

    # Plots the current and desired heading
    plt.plot([0, width], [0, 0], "--", c="g")
    des_f = lambda x: [np.tan(-theta)*i for i in x]
    xs = np.linspace(0, width, 100)
    plt.plot(xs, des_f(xs), "--", c="purple")

    glob_f = lambda x: [np.tan(-desired_heading) * i for i in x]
    xs = np.linspace(0, width, 100)
    plt.plot(xs, glob_f(xs), "--", c="red")

    # Sets up and shows plot
    plt.axis("square")
    plt.xlim(0, 100)
    plt.ylim(20, 20)
    if save:
        if name == "":
            print("YOU DIDNT PROVIDE A NAME!!!!!")
            return
        plt.savefig(name)
    plt.close()


def rotate_point(point, theta):
    return point[0] * np.cos(theta) - point[1] * np.sin(theta), \
           point[0] * np.sin(theta) + point[1] * np.cos(theta)

def adjust_blocked():
    global blocked_nodes
    new_set = set()
    for node in blocked_nodes:
        normalized_point = (-(node[0] - (height/2)), node[1])
        new_point = rotate_point(normalized_point[::-1], -current_heading)
        unnormalized_point = (int(-new_point[1] + (height/2)), int(new_point[0]))
        new_set.add(unnormalized_point)
    blocked_nodes = new_set



def adjust_obj(obj):
    rot_1 = rotate_point((obj[0], obj[2]), current_heading)
    rot_2 = rotate_point((obj[1], obj[3]), current_heading)
    tran_1 = (rot_1[0] + off_x, rot_1[1] + off_y)
    tran_2 = (rot_2[0] + off_x, rot_2[1] + off_y)

    return tran_1[0], tran_2[0], tran_1[1], tran_2[1]


def reverse_obj(obj):
    tran_1 = (obj[0] - off_x, obj[2] - off_y)
    tran_2 = (obj[1] - off_x, obj[3] - off_y)
    rot_1 = rotate_point(tran_1, -current_heading)
    rot_2 = rotate_point(tran_2, -current_heading)

    return rot_1[0], rot_2[0], rot_1[1], rot_2[1]


def adjust_path():
    for point_ind in range(len(path)):
        point = path[point_ind]
        tran_point = ((-point[0] + (y_dim / 2)), point[1])

        rot_point = rotate_point(tran_point[::-1], -current_heading)

        path[point_ind] = (-rot_point[1] + (y_dim/2), rot_point[0])


def plot_curve(obj_lst, path, node_type=2, plot_path=1, deltas=False, do_plot=False, name=None):
    """Creates the curve around objects"""
    global blocked_nodes, interpolated_path, off_y, off_x, tck

    blocked_nodes = set()

    theta = desired_heading - current_heading

    obj_lst = list(map(lambda x: (x[2] / 1000, x[3] / 1000, x[0] / 1000, x[1] / 1000), obj_lst))

    for obj_ind in range(len(obj_lst)):
        obj_lst[obj_ind] = adjust_obj(obj_lst[obj_ind])

    for o in obj_lst:
        blocked_nodes = blocked_nodes.union(get_blocked_nodes(o))

    interpolated_path = inter_path(path)

    tck = interpolated_path[1]
    fig, ax = plt.subplots(figsize=(12, 7))
    plt.axis("square")
    plt.xlim(0, width)
    plt.ylim(-(height // 2), (height // 2))

    ## Creates visualization
    if deltas:
        for x in np.arange(0, width+5, 1):
            full_len = (sum(interp.splint(0, 1, tck, full_output=0))) * 2
            u = x / full_len

            pos = (x, interp.splev(u, tck))[1]

            dervs = get_dervs(x)
            print(get_delta(x, 1))
            ax.quiver(pos[0], pos[1], 0, 1, angles=-57.3*get_delta(x, 4.5), width=0.005, headwidth=3)

        plt.show()
    #print(path)
    plot(obj_lst, path, theta, node_type, plot_path, save=True, name=name)
    plt.close()