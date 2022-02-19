import numpy as np
import matplotlib.pyplot as plt
import heapq
from scipy import interpolate as interp

# Size of a node in the graph
node_size = 1

# Calculate Padding
padding = 1
padding_num = max(int(padding // node_size), 1)

# Center blocked nodes
center_blocked_nodes = set()

# Blocked nodes
blocked_nodes = set()

# Maximum distance allowed from path (in meters)
max_distance = 3

# Maximum allowed desired angle for a given path generation
max_angle = np.pi / 4

# Current end node
current_end_node = None

# Previous Path
prev_path = []

# Loaded Graph Size
loaded_graph_size = 20

int_xs, int_ys = [], []
full_len = 0
tck = 0

def get_interp(xs, ys):
    global full_len, tck
    tck = interp.splprep([xs, ys], s=0.5)[0]
    full_len = (sum(interp.splint(0, 1, tck, full_output=0))) * 2
    print(full_len)
    return tck

def get_dervs(x, acc=0.000001):
    """Calculates the derivatives of the curve"""
    if not full_len:
        return 0
    u = x/full_len
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

    return wheel_base/radius_of_turn + ((load_front_ax/corn_stiff_front)-(load_rear_ax/corn_stiff_rear))*((vel**2)/(g*radius_of_turn))

def get_node_from_point(point):
    """Takes cartesian point and returns the corresponding node"""
    x, y = point
    return (
        int(x // node_size),
        int(y // node_size)
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

    vert = (x2 - x1 == 0)

    if not vert:
        m = (y2 - y1) / (x2 - x1)
        delta_x = node_size/((1+(m**2))**0.5)
    else:
        tmp_max = max(y1, y2)
        tmp_min = min(y1, y2)
        y1 = tmp_min
        y2 = tmp_max

    cur_point = [x1, y1]
    blocked = set()

    while (cur_point[0] < x2) if not vert else (cur_point[1] < y2):

        node = get_node_from_point(cur_point)
        if node not in center_blocked_nodes:
            cur_blocked = [(node[0]+x, node[1]+y) for y in range(-padding_num, padding_num+1) for x in range(-padding_num, padding_num+1)]
            blocked.update(cur_blocked)
            center_blocked_nodes.add(node)
            #[print(f"({node[0] + x}, {node[1] + y})") for y in range(-padding_num, padding_num + 1) for x in
             #range(-padding_num, padding_num + 1)]


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
        #[print(f"({node[0] + x}, {node[1] + y})") for y in range(-padding_num, padding_num + 1) for x in
         #range(-padding_num, padding_num + 1)]
    return blocked


def get_end_node(bike_pos, desired_heading):
    diff_vec = np.array([np.cos(desired_heading)*loaded_graph_size, np.sin(desired_heading)*loaded_graph_size])
    return get_node_from_point(bike_pos + diff_vec)


def plot(bike_pos, start_node, end_node, objects, xs, ys, cur_heading):
    x_low = -10
    x_high = 10
    y_low = -20
    y_high = 10
    for i in range(x_low, x_high):
        plt.plot([i, i], [y_low, y_high], c="black", linewidth=0.5)

    for j in range(y_low, y_high):
        plt.plot([x_low, x_high], [j, j], c="black", linewidth=0.5)
    plt.plot(bike_pos[0] / node_size, bike_pos[1] / node_size, "o", c="orange", label="Bike Position")
    plt.plot(start_node[0], start_node[1], "o", c="green", label="Start Node")
    plt.plot(end_node[0], end_node[1], "o", c="red", label="End Node")

    for obj in objects:
        obj = list(map(lambda x: x / node_size, obj))
        plt.plot(obj[:2], obj[2:], c="blue", label="Object")

    plt.xlim(x_low, x_high)
    plt.ylim(y_low, y_high)
    plt.quiver(bike_pos[0], bike_pos[1], np.cos(cur_heading), np.sin(cur_heading), color="red")
    plt.gca().set_aspect('equal', adjustable='box')
    tck = get_interp(xs[1:], ys[1:])
    u = np.linspace(0, 1, 25)
    i = interp.splev(u, tck)
    plt.plot(xs, ys, c="purple", label="Path")
    plt.plot(i[0], i[1], c="pink", label="Path")
    #plt.plot(int_xs, int_ys, c="purple", label="Path")
    #for i in u:
        #x, y = interp.splev(i, tck)
        #delta = get_delta(x, 4)
        #plt.quiver(x, y, np.cos(delta), np.sin(delta), color="purple")


def get_start_point(bike_pos, cur_heading):
    new_point_dist = 2 * node_size

    # Calculates point 1 meter from bike_pos in the direction of cur_heading
    point = np.array([np.cos(cur_heading)*new_point_dist + bike_pos[0], np.sin(cur_heading)*new_point_dist + bike_pos[1]])

    # Gets node closest to point
    node = get_node_from_point(point)
    return node


def euc_dist(a, b):
    return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)


def bfs_path(blocked_nodes, start_node, end_node, bike_pos):
    priority_queue = []
    heapq.heappush(priority_queue, (0, start_node, ([bike_pos[0]/node_size, start_node[0]], [bike_pos[1]/node_size, start_node[1]])))

    node_queue = {start_node}

    best_node = ([bike_pos[0]/node_size, start_node[0]], [bike_pos[1]/node_size, start_node[1]])
    best_dist = euc_dist(start_node, end_node)
    visited = set()

    while priority_queue:
        cur_dist, cur_node, path = heapq.heappop(priority_queue)
        xs, ys = path
        node_queue.remove(cur_node)
        #print(cur_node)

        if cur_node == end_node:
            return xs, ys

        if cur_node in visited:
            continue

        visited.add(cur_node)

        if cur_node[0] > path[0][-2]:
            diff_x = 1
        elif cur_node[0] < path[0][-2]:
            diff_x = -1
        else:
            diff_x = 0

        if cur_node[1] > path[1][-2]:
            diff_y = 1
        elif cur_node[1] < path[1][-2]:
            diff_y = -1
        else:
            diff_y = 0

        if diff_x != 0 and diff_y != 0:
            neighbors = [(cur_node[0] + diff_x, cur_node[1]), (cur_node[0], cur_node[1] + diff_y), (cur_node[0] + diff_x, cur_node[1] + diff_y)]
        elif diff_x != 0:
            neighbors = [(cur_node[0] + diff_x, cur_node[1] + y) for y in range(-1, 2)]
        else:
            neighbors = [(cur_node[0] + x, cur_node[1] + diff_y) for x in range(-1, 2)]

        for x, y in neighbors:
            if (x, y) in blocked_nodes:
                continue

            if (x, y) in visited:
                continue

            if (x, y) in node_queue:
                continue

            if abs(x - start_node[0]) > loaded_graph_size or abs(y - start_node[1]) > loaded_graph_size:
                continue

            if euc_dist((x, y), end_node) < best_dist:
                best_dist = euc_dist((x, y), end_node)
                best_node = (xs + [x], ys + [y])

            if x != cur_node[0] and y != cur_node[1]:
                extra_dist = np.sqrt(2)
            else:
                extra_dist = 1

            value = cur_dist + 1.0*extra_dist + 1.2*euc_dist((x, y), end_node)

            node_queue.add((x, y))
            heapq.heappush(priority_queue, (value, (x, y), (xs + [x], ys + [y])))

    if euc_dist((best_node[0][-1], best_node[1][-1]), bike_pos) < max_distance:
        print("BIKE MUST BE STOPPED")
        exit()


    return best_node[0], best_node[1]


def adjust_path_for_interp(xs, ys, cur_heading):
    new_xs = []
    new_ys = []

    for i in range(len(xs)):
        new_xs.append(xs[i] - xs[0])
        new_ys.append(ys[i] - ys[0])

    print(cur_heading)

    angle_mat = np.array([[np.cos(-cur_heading), -np.sin(-cur_heading)],[np.sin(-cur_heading), np.cos(-cur_heading)]])

    for i in range(len(xs)):
        new_x, new_y = angle_mat @ np.array([new_xs[i], new_ys[i]])
        new_xs[i] = new_x
        new_ys[i] = new_y
    return new_xs, new_ys


def find_closest_value_binary(values, target):
    low = 0
    high = len(values) - 1

    while low <= high:
        mid = (low + high) // 2
        if values[mid] == target:
            return mid
        elif values[mid] < target:
            low = mid + 1
        else:
            high = mid - 1

    return low


def calculate_distance_from_path(bike_pos):
    xs, ys = prev_path
    ind = find_closest_value_binary(xs, bike_pos[0])
    dist = euc_dist((xs[ind], ys[ind]), bike_pos)
    return dist


def calculate_distance_from_end_node(bike_pos):
    return euc_dist(bike_pos, (current_end_node[0] * node_size, current_end_node[1] * node_size))


def check_for_objects_in_path(path):
    xs, ys = path

    for i in range(len(xs)):
        node = get_node_from_point((xs[i] / node_size, ys[i] / node_size))
        if node in blocked_nodes:
            return True
    return False


def should_new_path_be_generated(bike_pos):
    if not prev_path:
        return True

    if check_for_objects_in_path(prev_path):
        return True

    if calculate_distance_from_path(bike_pos) > max_distance:
        return True

    if calculate_distance_from_end_node(bike_pos) < max_distance:
        return True

    return False


def get_direct_heading_path(bike_pos, cur_heading, desired_heading):
    new_point_dist = 2 * node_size

    # Calculates point 1 meter from bike_pos in the direction of cur_heading
    point = [np.cos(cur_heading) * new_point_dist + bike_pos[0], np.sin(cur_heading) * new_point_dist + bike_pos[1]]

    end_point = [np.cos(desired_heading) * 30 + bike_pos[0], np.sin(desired_heading) * 30 + bike_pos[1]]
    #end_point = [2, 18]
    # New angle
    new_angle = np.arctan2(end_point[1] - point[1], end_point[0] - point[0])

    path = [[bike_pos[0], point[0]], [bike_pos[1], point[1]]]

    while euc_dist(point, end_point) > node_size:
        point = [point[0] + np.cos(new_angle) * node_size, point[1] + np.sin(new_angle) * node_size]
        path[0].append(point[0])
        path[1].append(point[1])

    path[0].append(end_point[0])
    path[1].append(end_point[1])

    return path


def create_path(objects, bike_pos, cur_heading, desired_heading):
    global prev_path, current_end_node, int_xs, int_ys

    cur_heading = -cur_heading + np.pi / 2

    for obj in objects:
        blocked_nodes.update(get_blocked_nodes(obj))

    used_desired_heading = desired_heading
    if abs(desired_heading - cur_heading) > max_angle:
        used_desired_heading = (desired_heading / desired_heading) * max_angle

    direct_path = get_direct_heading_path(bike_pos, cur_heading, used_desired_heading)

    use_direct_path = False

    if should_new_path_be_generated(bike_pos) or use_direct_path:
        print("Generating new path")

        if use_direct_path:
            xs, ys = direct_path
            start_node = get_node_from_point((xs[0], ys[0]))
            current_end_node = get_node_from_point([2, 17])
        else:
            start_node = get_start_point(bike_pos, cur_heading)
            #current_end_node = get_end_node(bike_pos, used_desired_heading)
            current_end_node = get_node_from_point([17, 2])

            xs, ys = bfs_path(blocked_nodes, start_node, current_end_node, bike_pos)

            for i in range(len(xs)):
                xs[i] = xs[i] * node_size
                ys[i] = ys[i] * node_size

            xs.insert(0, bike_pos[0])
            ys.insert(0, bike_pos[1])

        prev_path = [xs, ys]
        int_xs, int_ys = adjust_path_for_interp(xs, ys, cur_heading)

        plot(bike_pos, start_node, current_end_node, objects, xs, ys, cur_heading)

        return int_xs, int_ys
    return [], []