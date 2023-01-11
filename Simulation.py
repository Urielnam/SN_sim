import simpy
import random

import numpy as np
from collections import defaultdict
from datetime import datetime
import os
import csv
from BackendClasses import clockanddatacalc_func

import tkinter as tk

# -------------------------
# DEV NOTES
# -------------------------

# Next up - showing the different visual cues at the top of the screen to show the logic is working well.

# -------------------------  ll
# CONFIGURATION
# -------------------------

data_age = defaultdict(lambda : [])
data_age_by_type = defaultdict(lambda : [])
successful_operations = []
successful_operations_total = defaultdict(lambda : [])
number_of_sensors = defaultdict(lambda : [])
agent_flow_rates_by_type = defaultdict(lambda : [])
agent_flow_rates_by_type["Array"] = defaultdict(lambda : [])
agent_flow_rates_by_type["Analysis Station"] = defaultdict(lambda : [])
agent_flow_rates_by_type["Action Station"] = defaultdict(lambda : [])
total_resource = defaultdict(lambda : [])
self_organization_measure = defaultdict(lambda : [])
max_resource = 15
end_time = 1000

# -------------------------
# ANALYTICAL GLOBALS
# -------------------------

# Bits queue
sensor_array_queue = []
array_analysis_queue = []
analysis_array_queue = []
array_action_queue = []
action_array_queue = []
array_sensor_queue = []
analysis_sublist = []
sensor_list = []
# array that will save the time from data creation to data use at the analysis station.
analysis_data_usage_time = []
# array to save the time from data analysis to data useage.
action_data_usage_time = []

graph_list = [sensor_array_queue, analysis_array_queue, action_array_queue,
              array_analysis_queue, array_action_queue,
              array_sensor_queue]

start_nodes = {
    "sensor to array": sensor_array_queue,
    "analysis to array": analysis_array_queue,
    "action to array": action_array_queue
}

end_nodes = {
    "array to analysis": array_analysis_queue,
    "array to action": array_action_queue,
    "array to sensor": array_sensor_queue
}

connecting_graph = {
    "action to array": {
        "intel": "array to analysis",
        "feedback": "array to analysis",
        "target": "array to analysis"
    },
    "analysis to array": {
        "intel": "array to action",
        "feedback": "array to sensor",
        "target": "array to action"
    },
    "sensor to array": {
        "intel": "array to analysis",
        "feedback": "array to analysis",
        "target": "array to analysis"
    }
}

# -------------------------
# UI/ANIMATION
# -------------------------
#
# main = tk.Tk()
# main.title("ISR Simulation")
# main.config(bg="#fff")
# logo = tk.PhotoImage(file = "images/250px-Masha.png")
# top_frame = tk.Frame(main)
# top_frame.pack(side=tk.TOP, expand = False)
# tk.Label(top_frame, image = logo, bg = "#000007", height = 65, width = 1300).pack(side=tk.LEFT, expand = False)
# canvas = tk.Canvas(main, width = 1300, height = 350, bg = "white")
# canvas.pack(side=tk.TOP, expand = False)
#
#
image_map2 = {
    "intel": tk.PhotoImage(file = "images/folder_resize.png"),
    "feedback": tk.PhotoImage(file = "images/Utilities-Feedback-Assistant-icon_resize.png"),
    "target": tk.PhotoImage(file = "images/Target-Audience-icon_resize.png")
}

for key in image_map2.keys():
    data_age_by_type[key] = defaultdict(lambda: [])

# f = plt.Figure(figsize=(2, 2), dpi=72)
# a3 = f.add_subplot(121)
# a3.plot()
# a1 = f.add_subplot(222)
# a1.plot()
# a2 = f.add_subplot(224)
# a2.plot()
# data_plot = FigureCanvasTkAgg(f, master=main)
# data_plot.get_tk_widget().config(height = 400)
# data_plot.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

start_row = 95
regular_height = 30
#
# class IsrElement:
#     text_height = 30
#     icon_top_margin = -8
#
#     def __init__(self, element_name, canvas, x_top, y_top, length, height):
#         self.element_name = element_name
#         self.x_top = x_top
#         self.y_top = y_top
#         self.length = length
#         self.canvas = canvas
#
#         canvas.create_rectangle(x_top, y_top, x_top + length, y_top + height)
#         canvas.create_text(x_top + 10, y_top + 7, anchor = tk.NW, text = f"{element_name}")
#         self.canvas.update()
#
#
#
# class QueueGraphics:
#     text_height = 30
#     icon_top_margin = -8
#
#     def __init__(self, data_container, icon_height,  data_name, canvas, x_top, y_top):
#         # self.icon_file = icon_file
#         self.icon_height = icon_height
#         self.queue_name = data_name
#         self.canvas = canvas
#         self.x_top = x_top
#         self.y_top = y_top
#
#         # self.image = tk.PhotoImage(file = self.icon_file)
#         self.icons = []
#         self.data_contained = data_container
#         canvas.create_text(x_top, y_top, anchor = tk.NW, text = f"{data_name}")
#         self.canvas.update()
#
#     def paint_queue(self):
#         # delete all current representations
#         for i in self.icons:
#             to_del = self.icons.pop()
#             self.canvas.delete(to_del)
#             self.canvas.update()
#         # redraw for all current items contained
#         x = self.x_top + 15
#         y = self.y_top + 45
#
#         for i in self.data_contained:
#             self.icons.append(
#                 self.canvas.create_image(x, y, anchor = tk.NW, image = image_map2[i.type])
#             )
#             self.icons.append(self.canvas.create_text(x - 10, y + 30, anchor = tk.NW, text = i.id))
#             y = y + self.icon_height + 45
#         self.canvas.update()


# the queue graphics manage the location and order of painting stuff but the icon needs to come for the data piece
# itself whether it's intel, analysis etc.
# a different type of object painted needs to be created. it's a set function to paint data piece in space.
# the queue will call that function with a specific location.
# Info is FIFO, so the function will need to delete the specific object and repaint. might need a loop.

if (ui):
    create_graphics(sensor_array_queue)

sensor_list_visual = []

#
# def paint_sensors():
#     for i in sensor_list_visual:
#         to_del = sensor_list_visual.pop()
#         canvas.delete(to_del)
#         canvas.update()
#
#     n = 1
#
#     for x in sensor_list:
#
#         element_name = x.name
#         x_top = 5
#         y_top = start_row + (regular_height+10)*(n-1)
#         n = n + 1
#         length = 60
#         height = regular_height
#
#         sensor_list_visual.append(canvas.create_rectangle(x_top, y_top,
#                                                           x_top + length,
#                                                           y_top + height))
#         sensor_list_visual.append(canvas.create_text(x_top + 10, y_top + 7,
#                                                      anchor = tk.NW,
#                                                      text = f"{element_name}"))
#         canvas.update()
#

def calc_self_org(dt):
    changes_by_key = []

    for key_n in agent_flow_rates_by_type.keys():
        change_count = 0
        relevant_list_of_timesteps_keys = [x for x in agent_flow_rates_by_type[key_n].keys() if x > (env.now - dt)]
        for x in range(len(relevant_list_of_timesteps_keys) - 1):
            if agent_flow_rates_by_type[key_n][relevant_list_of_timesteps_keys[x]] != \
                    agent_flow_rates_by_type[key_n][relevant_list_of_timesteps_keys[x + 1]]:
                change_count += 1
        changes_by_key.append(change_count)

    change_count = 0
    relevant_list_of_timesteps = [x for x in number_of_sensors.keys() if x > (env.now - dt)]
    for x in range(len(relevant_list_of_timesteps) - 1):
        if number_of_sensors[relevant_list_of_timesteps[x]] != \
                number_of_sensors[relevant_list_of_timesteps[x + 1]]:
            change_count += 1
    changes_by_key.append(change_count)

    return np.sum(changes_by_key)

#
# class ClockAndData:
#     def __init__(self, canvas, x1, y1, x2, y2, time):
#         # Draw the inital state of the clock and data on the canvas
#         self.x1 = x1
#         self.y1 = y1
#         self.x2 = x2
#         self.y2 = y2
#         self.canvas = canvas
#         self.train = canvas.create_rectangle(self.x1, self.y1, self.x2, self.y2, fill="#fff")
#         self.time = canvas.create_text(self.x1 + 10, self.y1 + 10, text="Time = " + str(round(time, 1)) + "m",
#                                        anchor=tk.NW)
#         # Code to show the seller wait time at queue.
#         #self.seller_wait = canvas.create_text(self.x1 + 10, self.y1 + 40,
#         #                                      text="Avg. Seller Wait  = " + str(avg_wait(seller_waits)), anchor=tk.NW)
#         # Code to show the scanner wait time at queue.
#         #self.scan_wait = canvas.create_text(self.x1 + 10, self.y1 + 70,
#         #                                    text="Avg. Scanner Wait = " + str(avg_wait(scan_waits)), anchor=tk.NW)
#         self.canvas.update()
#
#     def tick(self, time):
#         dt = 5
#
#
#         # re-draw the clock and data fields on the canvas. Also update the matplotlib charts
#         self.canvas.delete(self.time)
#
#         # Delete previous data.
#         #self.canvas.delete(self.seller_wait)
#         #self.canvas.delete(self.scan_wait)
#
#         self.time = canvas.create_text(self.x1 + 10, self.y1 + 10, text="Time = " + str(round(time, 1)) + "m",
#                                        anchor=tk.NW)
#         # set new data.
#         #self.seller_wait = canvas.create_text(self.x1 + 10, self.y1 + 30,
#         #                                      text="Avg. Seller Wait  = " + str(avg_wait(seller_waits)) + "m",
#         #                                      anchor=tk.NW)
#         #self.scan_wait = canvas.create_text(self.x1 + 10, self.y1 + 50,
#         #                                    text="Avg. Scanner Wait = " + str(avg_wait(scan_waits)) + "m", anchor=tk.NW)
#
#         paint_sensors()
#
#         a1.cla()
#         a1.set_xlabel("Time")
#         a1.set_ylabel("Average Data Age")
#         # code to calculate step function.
#         # ages = [env.now - a.time for a in (sensor_array_queue + array_analysis_queue + analysis_array_queue +
#         #                                     array_action_queue + action_array_queue + array_sensor_queue)]
#         # data_age[float(env.now)].append(ages)
#
#         # for key in image_map2.keys():
#         #     data_age_by_type[key][float(env.now)].append(
#         #         [env.now - a.time for a in [
#         #             i for i in (sensor_array_queue + array_analysis_queue + analysis_array_queue +
#         #                         array_action_queue + action_array_queue + array_sensor_queue) if i.type == key]])
#
#         a1.plot([t for (t, age) in data_age.items()], [np.mean(age) for (t, age) in data_age.items()], label="all")
#
#         for key in image_map2.keys():
#             a1.plot([t for (t, age) in data_age_by_type[key].items()],
#                     [np.mean(age) for (t, age) in data_age_by_type[key].items()], label = key)
#         a1.legend(loc="upper left")
#
#         # dt = 5
#
#         a2.cla()
#         a2.set_xlabel("Time")
#         a2.set_ylabel("Accumulated Success")
#         # code to calculate step function.
#         # successful_operations_total[float(env.now)].append(len([x for x in successful_operations if x > env.now - dt]))
#         a2.plot([t for (t, success) in successful_operations_total.items()],
#                 [success for (t, success) in successful_operations_total.items()],
#                 label = "Average success over last " + str(dt) + " timesteps")
#
#
#         a3.cla()
#         a3.set_xlabel("Time")
#         a3.set_ylabel("System Cost")
#         # code to calculate step function.
#         # number_of_sensors[float(env.now)].append(len(sensor_list))
#         # agent_flow_rates_by_type["Array"][float(env.now)].append(array.flow_rate)
#         # agent_flow_rates_by_type["Analysis Station"][float(env.now)].append(
#         #     analysis_station.flow_rate)
#         # agent_flow_rates_by_type["Action Station"][float(env.now)].append(
#         #     action_station.flow_rate)
#         # total_resource[float(env.now)].append(len(sensor_list)+array.flow_rate +
#         #                                       analysis_station.flow_rate +
#         #                                       action_station.flow_rate)
#
#
#
#         a3.plot([t for (t, a) in number_of_sensors.items()],
#                 [a for (t, a) in number_of_sensors.items()],
#                 label="Sensors")
#
#         for key in agent_flow_rates_by_type.keys():
#             a3.plot([t for (t, a) in agent_flow_rates_by_type[key].items()],
#                     [a for (t, a) in agent_flow_rates_by_type[key].items()],
#                     label=key)
#         a3.plot([t for (t,a) in total_resource.items()],
#                 [a for (t,a) in total_resource.items()],
#                 label="Total")
#
#         a3.legend(loc="upper left")
#
#         # to calculate self-org, check how much the system has been
#         # "in motion" for the last X timesteps.
#         # sum of number of times the resources were re-allocated.
#
#         # dt = 5
#
#         # self_organization_measure[float(env.now)].append(calc_self_org(dt))
#         a2.plot([t for (t,a) in self_organization_measure.items()],
#                 [a for (t,a) in self_organization_measure.items()],
#                 label = "Self-organization effort over last " + str(dt) + " timesteps")
#
#         a2.legend(loc="upper left")
#
#
#         data_plot.draw()
#         self.canvas.update()

# -------------------------
# SIMULATION
# -------------------------


def create_clock(env):
    # This generator is meant to be used as a SimPy event to update the clock and the data in the UI

    while True:
        yield env.timeout(0.1)
        dt = 5
        clockanddatacalc_func(image_map2, data_age_by_type, env, sensor_array_queue, array_analysis_queue,
                              analysis_array_queue, array_action_queue, action_array_queue, array_sensor_queue,
                              data_age, self_organization_measure, dt, agent_flow_rates_by_type, number_of_sensors,
                              successful_operations_total, successful_operations, sensor_list, array, analysis_station,
                              action_station, total_resource)
        if (ui):
            ui_refresh(env.now)


# Intel object. Has a real/wrong status and time created
# data types: "intel", "feedback"
class Data:
    def __init__(self, status, time, type, creator):
        self.status = status
        self.time = time
        # data types - intel, feedback
        self.type = type
        self.creator = creator
        # adds an image so that we can paint it later
        self.id = self.type + " from " + self.creator + "\n at time " + str(self.time)


# Every time step the sensors create new information bit.
# Info has real/wrong status
# Intel generated is randomly selected to be true or false with a certain precentage.

class Sensor(object):
    def __init__(self, env, correctness_probability, order):
        self.env = env
        self.action = env.process(self.run())
        self.correctness_probability = correctness_probability
        self.order = order
        self.name = "Sensor " + str(order)
        self.is_alive = True

    def run(self):
        while self.is_alive:

            # print('Create new info bit at time %d' % env.now)
            yield env.timeout(1)
            sensor_array_queue.append(Data(random.random() < self.correctness_probability,
                                           env.now, 'intel', self.name))


# The array moves data between different queues. It can move only one object per lane.
class Array(object):
    def __init__(self, env):
        self.env = env
        self.action = env.process(self.run())
        self.move_counter = 0
        self.x = 5
        self.y = 20
        self.presentation = IsrElement("Array", canvas, self.x, self.y, 1290, start_row-30)
        self.item_presentation =[]
        self.canvas = canvas
        self.flow_rate = 1

    def move_item(self, queue_from, queue_to):
        a = queue_from[0]
        queue_from.pop(0)
        # draw inside box
        self.item_presentation.append(
            self.canvas.create_image(self.x + 100, self.y, anchor=tk.NW, image=image_map2[a.type])
        )
        self.item_presentation.append(self.canvas.create_text(self.x + 100, self.y + 30, anchor=tk.NW, text=a.id))

        self.canvas.update()
        yield env.timeout(1/self.flow_rate)

        for i in self.item_presentation:
            to_del = self.item_presentation.pop()
            self.canvas.delete(to_del)
            self.canvas.update()
        queue_to.append(a)
        # visualize_all()

    def run(self):

        while True:

            # for each lane, move one data unit per time
            for i in range(self.flow_rate):
                if check_queue() == 0:
                    yield env.timeout(1)
                    break
                selected_array = random.choice([x for x in start_nodes.keys() if len(start_nodes[x]) > 0])
                second_array = connecting_graph[selected_array][start_nodes[selected_array][0].type]
                yield self.env.process(self.move_item(start_nodes[selected_array], end_nodes[second_array]))

            #else:
            #    if len(action_array_queue) > 0:
            #        yield self.env.process(self.move_item(action_array_queue, array_analysis_queue))

            #    else:
            #        if len(analysis_array_queue) > 0:
            #            if analysis_array_queue[0].type == 'feedback':
            #                yield self.env.process(self.move_item(analysis_array_queue, array_sensor_queue))

            #            else:
            #                yield self.env.process(self.move_item(analysis_array_queue, array_action_queue))

            #        else:
            #            if len(sensor_array_queue) > 0:
            #                yield self.env.process(self.move_item(sensor_array_queue, array_analysis_queue))


def check_queue():
    return len(sensor_array_queue) + len(analysis_array_queue) + len(action_array_queue)

#    def move_between(self, sender, reciver):
#
#       # a check to see how many hand changes were made.
#        # self.move_counter = self.move_counter + 1
#        # print(self.move_counter)
#
#        if len(sender) > 0:
#            a=sender[0]
#            sender.pop(0)

#            reciver.append(a)

#            visualize_all()


# need to create analysis station, then action station and then start messing with accuricy.
# if one of the intel is true, the intel is correct and the boogie is found. if both are false, the attack failes.
# I need to change it so it ingests one intel article per cycle.
class AnalysisStation(object):
    def __init__(self, env):
        self.env = env
        self.action = env.process(self.run())
        self.x = 405
        self.y = start_row
        self.flow_rate = 1

        self.station_item_presentation = []

    def run(self):

        while True:
            # print(array_analysis_queue)
            # first, check for feedback in first cell, if there isn't any feedback, proceed to analyze the data.

            bank_size = 2

            if len(array_analysis_queue) == 0:
                yield env.timeout(1)

            else:
                a = array_analysis_queue[0]
                array_analysis_queue.pop(0)
                analysis_data_usage_time.append(env.now - a.time)

                self.station_item_presentation.append(
                    canvas.create_image(self.x, self.y + 45, anchor=tk.NW, image=image_map2[a.type])
                )
                self.station_item_presentation.append(canvas.create_text(self.x, self.y + 75, anchor=tk.NW, text=a.id))

                canvas.update()
                yield env.timeout(1/self.flow_rate)

                for i in self.station_item_presentation:
                    to_del = self.station_item_presentation.pop()
                    canvas.delete(to_del)
                    canvas.update()

                if a.type == 'feedback':
                    analysis_array_queue.append(a)

                # if data type is info, save it for digestion
                else:
                    # add data to data bank.
                    analysis_sublist.append(a)

                    # if bank size is equal to bank_size, delete bank and create new data
                    if len(analysis_sublist) == bank_size:

                        analysis_array_queue.append(Data(analysis_sublist[0].status or analysis_sublist[1].status, env.now, 'target',
                                                         random.choice(analysis_sublist).creator))
                        analysis_sublist.pop(0)
                        analysis_sublist.pop(0)


# action_station acts when there is intel in the pipeline
class ActionStation(object):
    def __init__(self, env):
        self.env = env
        self.action = env.process(self.run())
        self.flow_rate = 1

    def run(self):
        while True:

            if len(array_action_queue) > 0:
                a = array_action_queue[0]
                array_action_queue.pop(0)
                action_data_usage_time.append(self.env.now - a.time)
                yield self.env.timeout(1/self.flow_rate)
                # print(array_action_queue[0].status)
                if a.status:
                    print("Attack successful!")
                    # send back positive feedback
                    action_array_queue.append(Data(True, env.now,
                                                   'feedback', a.creator))
                    successful_operations.append(self.env.now)
                if not a.status:
                    print("Attack failed")
                    # send back negative feedback
                    action_array_queue.append(Data(False, env.now,
                                                   'feedback', a.creator))

            else:
                yield self.env.timeout(1)


# function to visualize the data
def visualize_data(name, array):
    print('%s is %d long' % (name, len(array)))


# def visualize_all():
#    visualize_data('sensor_array_queue', sensor_array_queue)
#    visualize_data('array_analysis_queue', array_analysis_queue)
#    visualize_data('analysis_array_queue', analysis_array_queue)
#    visualize_data('array_action_queue', array_action_queue)
#    visualize_data('action_array_queue', action_array_queue)
#    visualize_data('array_sensor_queue', array_sensor_queue)
#    print(feedback_data_usage_time)
#    print(analysis_data_usage_time)
#    print(action_data_usage_time)
#    print("end cycle %d" % env.now)

def check_max_resource():
    return(len(sensor_list)+array.flow_rate +
           analysis_station.flow_rate +
           action_station.flow_rate) < max_resource


def sensor_maker(env):
    sensor_number = 2

    while True:
        while len(array_sensor_queue) > 0:

            # if action feedback is good, create new sensor and kill the data.
            if array_sensor_queue[0].status:
                a = random.random()
                if check_max_resource():
                    sensor_list.append(Sensor(env, a, sensor_number))
                    sensor_number = sensor_number + 1
                array_sensor_queue.pop(0)
            else:
                b = array_sensor_queue[0]
                for sensor in sensor_list.copy():
                    if sensor.name == b.creator:
                        sensor.is_alive = False
                        sensor_list.remove(sensor)
                if len(sensor_list) == 0:
                    a = random.random()
                    sensor_list.append(Sensor(env, a, sensor_number))
                    sensor_number = sensor_number + 1
                array_sensor_queue.pop(0)
        if not check_max_resource() and len(sensor_list) > 1:
            x = random.choice(sensor_list)
            x.is_alive = False
            sensor_list.remove(x)

        yield env.timeout(0.1)


def array_upgrade(env, array):
    while True:
        if check_queue() < (array.flow_rate-1)*5 and array.flow_rate > 1:
            array.flow_rate = array.flow_rate - 1
        if check_max_resource():
            while check_queue() > array.flow_rate*5:
                array.flow_rate = array.flow_rate + 1
        yield env.timeout(0.1)


def analysis_upgrade(env, analysis):
    while True:
        if len(array_analysis_queue) < (analysis.flow_rate-1)*5 and analysis.flow_rate > 1:
            analysis.flow_rate = analysis.flow_rate - 1
        if check_max_resource():
            while len(array_analysis_queue) > analysis.flow_rate*5:
                analysis.flow_rate = analysis.flow_rate + 1
        yield env.timeout(0.1)


def action_upgrade(env, action):
    while True:
        if len(array_action_queue) < (action.flow_rate-1)*5 and action.flow_rate > 1:
            action.flow_rate = action.flow_rate - 1
        if check_max_resource():
                while len(array_action_queue) > action.flow_rate*5:
                    action.flow_rate = action.flow_rate + 1
        yield env.timeout(1.1)


# export data at the end of runtime.
# data to include
# all plotted data - need to check how it's done maybe?


# def save_graph(env):
#     yield env.timeout(end_time-0.1)
#     save_name = "self org plot " + datetime.now().ctime() + " end time " + str(end_time)
#     save_name = save_name.replace(":","_")
#
#     ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
#     DATA_DIR = os.path.join(ROOT_DIR, save_name)
#     os.mkdir(DATA_DIR)
#     CSV_PATH = DATA_DIR + "//data"
#
#     with open(CSV_PATH, 'w', encoding='UTF8') as file:
#         writer = csv.writer(file)
#
#
#         for ax in f.get_axes():
#             writer.writerow([ax.get_xlabel,ax.get_ylabel])
#             for line in a2.lines:
#                 d = line.get_label
#                 writer.writerow([line.get_label])
#                 x = line.get_xdata()
#                 y = line.get_ydata()
#                 for n in range(len(x)):
#                     writer.writerow([x[n],y[n]])
#
#
#     svg_file_name = DATA_DIR + "\\" + save_name + ".svg"
#     f.savefig(svg_file_name)



env = simpy.rt.RealtimeEnvironment(factor = 0.1, strict = False)

env.process(create_clock(env))

# env = simpy.Environment()
action_station = ActionStation(env)
analysis_station = AnalysisStation(env)

array = Array(env)
sensor_list.append(Sensor(env, 0.5, 1))
env.process(sensor_maker(env))
env.process(array_upgrade(env,array))
env.process(analysis_upgrade(env,analysis_station))
env.process(action_upgrade(env, action_station))
env.process(save_graph(env))

env.run(until=end_time)

main.mainloop()









