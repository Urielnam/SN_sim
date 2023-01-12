import simpy
import random

import numpy as np
from collections import defaultdict
from datetime import datetime
import os
import csv
import tkinter as tk

from BackendClasses import clockanddatacalc_func
import UIClasses
# -------------------------
# DEV NOTES
# -------------------------

# Next up - showing the different visual cues at the top of the screen to show the logic is working well.

# -------------------------
# CONFIGURATION
# -------------------------

data_age = defaultdict(lambda: [])
data_age_by_type = defaultdict(lambda: [])
successful_operations = []
successful_operations_total = defaultdict(lambda: [])
number_of_sensors = defaultdict(lambda: [])
agent_flow_rates_by_type = defaultdict(lambda: [])
agent_flow_rates_by_type["Array"] = defaultdict(lambda: [])
agent_flow_rates_by_type["Analysis Station"] = defaultdict(lambda: [])
agent_flow_rates_by_type["Action Station"] = defaultdict(lambda: [])
total_resource = defaultdict(lambda: [])
self_organization_measure = defaultdict(lambda: [])
max_resource = 15
end_time = 20

# TODO: replace this
ui = True
UI_obj = {}
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
# array to save the time from data analysis to data usage.
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

static_image_map_keys = ["intel", "feedback", "target"]

# used for backend classes calculation
for key in static_image_map_keys:
    data_age_by_type[key] = defaultdict(lambda: [])


image_map2 = {
    "intel": tk.PhotoImage(file="images/folder.png"),
    "feedback": tk.PhotoImage(file="images/feedback.png"),
    "target": tk.PhotoImage(file="images/target.png")
}


for key in image_map2.keys():
    data_age_by_type[key] = defaultdict(lambda: [])


start_row = 95
regular_height = 30

# the queue graphics manage the location and order of painting stuff but the icon needs to come for the data piece
# itself whether it's intel, analysis etc.
# a different type of object painted needs to be created. it's a set function to paint data piece in space.
# the queue will call that function with a specific location.
# Info is FIFO, so the function will need to delete the specific object and repaint. might need a loop.


if ui:
    UI_obj = UIClasses.PaintGrapic(
            sensor_array_queue,
            array_sensor_queue,
            array_analysis_queue,
            analysis_sublist,
            analysis_array_queue,
            array_action_queue,
            action_array_queue)


# sensor_list_visual = []

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

# def calc_self_org(dt):
#     changes_by_key = []
#
#     for key_n in agent_flow_rates_by_type.keys():
#         change_count = 0
#         relevant_list_of_timesteps_keys = [x for x in agent_flow_rates_by_type[key_n].keys() if x > (env.now - dt)]
#         for x in range(len(relevant_list_of_timesteps_keys) - 1):
#             if agent_flow_rates_by_type[key_n][relevant_list_of_timesteps_keys[x]] != \
#                     agent_flow_rates_by_type[key_n][relevant_list_of_timesteps_keys[x + 1]]:
#                 change_count += 1
#         changes_by_key.append(change_count)
#
#     change_count = 0
#     relevant_list_of_timesteps = [x for x in number_of_sensors.keys() if x > (env.now - dt)]
#     for x in range(len(relevant_list_of_timesteps) - 1):
#         if number_of_sensors[relevant_list_of_timesteps[x]] != \
#                 number_of_sensors[relevant_list_of_timesteps[x + 1]]:
#             change_count += 1
#     changes_by_key.append(change_count)
#
#     return np.sum(changes_by_key)



clock = UIClasses.ClockAndDataDraw(1100, 260, 1290, 340, 0, sensor_list, data_age, data_age_by_type,
                                   successful_operations_total, number_of_sensors, agent_flow_rates_by_type,
                                   total_resource, self_organization_measure)


#
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

        if ui:
            clock.tick(env.now)
            UI_obj.tick()



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
    def __init__(self, correctness_probability, order):
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
    def __init__(self):
        self.env = env
        self.action = env.process(self.run())

        self.flow_rate = 1

        if ui:
            self.arr = UIClasses.ArrayDraw()

    def move_item(self, queue_from, queue_to):
        moved_item = queue_from[0]
        queue_from.pop(0)
        # # draw inside box
        if ui:
            self.arr.arr_move_item(moved_item)

        yield env.timeout(1/self.flow_rate)

        if ui:
            self.arr.arr_clear_item()
            
        queue_to.append(moved_item)

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


def check_queue():
    return len(sensor_array_queue) + len(analysis_array_queue) + len(action_array_queue)


# need to create analysis station, then action station and then start messing with accuricy.
# if one of the intel is true, the intel is correct and the boogie is found. if both are false, the attack failes.
# I need to change it so it ingests one intel article per cycle.
class AnalysisStation(object):
    def __init__(self):
        self.env = env
        self.action = env.process(self.run())

        self.flow_rate = 1
        if ui:
            self.draw = UIClasses.AnalysisStationDraw()

    def run(self):

        while True:
            # first, check for feedback in first cell, if there isn't any feedback, proceed to analyze the data.

            bank_size = 2

            if len(array_analysis_queue) == 0:
                yield env.timeout(1)

            else:
                moved_item = array_analysis_queue[0]
                array_analysis_queue.pop(0)
                analysis_data_usage_time.append(env.now - moved_item.time)

                if ui:
                    self.draw.run_draw(moved_item)

                yield env.timeout(1/self.flow_rate)

                if ui:
                    self.draw.run_delete()

                if moved_item.type == 'feedback':
                    analysis_array_queue.append(moved_item)

                # if data type is info, save it for digestion
                else:
                    # add data to data bank.
                    analysis_sublist.append(moved_item)

                    # if bank size is equal to bank_size, delete bank and create new data
                    if len(analysis_sublist) == bank_size:

                        analysis_array_queue.append(Data(analysis_sublist[0].status or analysis_sublist[1].status,
                                                         env.now, 'target', random.choice(analysis_sublist).creator))
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
                    sensor_list.append(Sensor(a, sensor_number))
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
                    sensor_list.append(Sensor(a, sensor_number))
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


env = simpy.rt.RealtimeEnvironment(factor = 0.1, strict = False)


env.process(create_clock(env))

# env = simpy.Environment()
action_station = ActionStation(env)
analysis_station = AnalysisStation()

array = Array()
sensor_list.append(Sensor(0.5, 1))
env.process(sensor_maker(env))
env.process(array_upgrade(env, array))
env.process(analysis_upgrade(env, analysis_station))
env.process(action_upgrade(env, action_station))
env.process(UIClasses.save_graph(env, end_time))

env.run(until=end_time)

UIClasses.main.mainloop()









