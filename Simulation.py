import simpy
import random
import pandas as pd
from datetime import datetime

import os

from collections import defaultdict

import tkinter as tk

import BackendClasses
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

# done: replace this to an external function
# ui = False
# UI_obj = {}
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

data_type_keys = ["intel", "feedback", "target"]

for key in data_type_keys:
    data_age_by_type[key] = defaultdict(lambda: [])


start_row = 95
regular_height = 30
now = datetime.now().ctime()
now = now.replace(":", "_")

# the queue graphics manage the location and order of painting stuff but the icon needs to come for the data piece
# itself whether it's intel, analysis etc.
# a different type of object painted needs to be created. it's a set function to paint data piece in space.
# the queue will call that function with a specific location.
# Info is FIFO, so the function will need to delete the specific object and repaint. might need a loop.


# if ui:
#     UI_obj = UIClasses.PaintGrapic(
#             sensor_array_queue,
#             array_sensor_queue,
#             array_analysis_queue,
#             analysis_sublist,
#             analysis_array_queue,
#             array_action_queue,
#             action_array_queue)
#
#     clock = UIClasses.ClockAndDataDraw(1100, 260, 1290, 340, 0, sensor_list, data_age, data_age_by_type,
#                                        successful_operations_total, number_of_sensors, agent_flow_rates_by_type,
#                                        total_resource, self_organization_measure)


#
# -------------------------
# SIMULATION
# -------------------------


def create_clock(env, array, analysis_station, action_station, ui, clock, UI_obj):
    # This generator is meant to be used as a SimPy event to update the clock and the data in the UI

    while True:
        yield env.timeout(0.1)
        dt = 5
        clockanddatacalc_func(data_type_keys, data_age_by_type, env, sensor_array_queue, array_analysis_queue,
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
    def __init__(self, correctness_probability, order, external_environemnt):
        self.env = external_environemnt
        self.action = self.env.process(self.run())
        self.correctness_probability = correctness_probability
        self.order = order
        self.name = "Sensor " + str(order)
        self.is_alive = True

    def run(self):
        while self.is_alive:

            # print('Create new info bit at time %d' % env.now)
            yield self.env.timeout(1)
            sensor_array_queue.append(Data(random.random() < self.correctness_probability,
                                           self.env.now, 'intel', self.name))


# The array moves data between different queues. It can move only one object per lane.
class Array(object):
    def __init__(self, external_environemnt, ui_flag):
        self.env = external_environemnt
        self.action = self.env.process(self.run())
        self.ui_flag = ui_flag

        self.flow_rate = 1

        if ui_flag:
            self.arr = UIClasses.ArrayDraw()

    def move_item(self, queue_from, queue_to):
        moved_item = queue_from[0]
        queue_from.pop(0)
        # # draw inside box
        if self.ui_flag:
            self.arr.arr_move_item(moved_item)

        yield self.env.timeout(1/self.flow_rate)

        if self.ui_flag:
            self.arr.arr_clear_item()
            
        queue_to.append(moved_item)

    def run(self):

        while True:

            # for each lane, move one data unit per time
            for i in range(self.flow_rate):
                if check_queue() == 0:
                    yield self.env.timeout(1)
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
    def __init__(self, external_environemnt, ui_flag):
        self.env = external_environemnt
        self.action = external_environemnt.process(self.run())
        self.ui_flag = ui_flag
        self.flow_rate = 1
        if ui_flag:
            self.draw = UIClasses.AnalysisStationDraw()

    def run(self):

        while True:
            # first, check for feedback in first cell, if there isn't any feedback, proceed to analyze the data.

            bank_size = 2

            if len(array_analysis_queue) == 0:
                yield self.env.timeout(1)

            else:
                moved_item = array_analysis_queue[0]
                array_analysis_queue.pop(0)
                analysis_data_usage_time.append(self.env.now - moved_item.time)

                if self.ui_flag:
                    self.draw.run_draw(moved_item)

                yield self.env.timeout(1/self.flow_rate)

                if self.ui_flag:
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
                                                         self.env.now, 'target',
                                                         random.choice(analysis_sublist).creator))
                        analysis_sublist.pop(0)
                        analysis_sublist.pop(0)


# action_station acts when there is intel in the pipeline
class ActionStation(object):
    def __init__(self, external_environemnt):
        self.env = external_environemnt
        self.action = self.env.process(self.run())
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
                    action_array_queue.append(Data(True, self.env.now,
                                                   'feedback', a.creator))
                    successful_operations.append(self.env.now)
                if not a.status:
                    print("Attack failed")
                    # send back negative feedback
                    action_array_queue.append(Data(False, self.env.now,
                                                   'feedback', a.creator))

            else:
                yield self.env.timeout(1)


def check_max_resource(array, analysis_station, action_station):
    return(len(sensor_list)+array.flow_rate +
           analysis_station.flow_rate +
           action_station.flow_rate) < max_resource


def sensor_maker(external_environemnt, array, analysis_station, action_station):
    sensor_number = 2

    while True:
        while len(array_sensor_queue) > 0:

            # if action feedback is good, create new sensor and kill the data.
            if array_sensor_queue[0].status:
                a = random.random()
                if check_max_resource(array, analysis_station, action_station):
                    sensor_list.append(Sensor(a, sensor_number, external_environemnt))
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
                    sensor_list.append(Sensor(a, sensor_number, external_environemnt))
                    sensor_number = sensor_number + 1
                array_sensor_queue.pop(0)
        if not check_max_resource(array, analysis_station, action_station) and len(sensor_list) > 1:
            x = random.choice(sensor_list)
            x.is_alive = False
            sensor_list.remove(x)

        yield external_environemnt.timeout(0.1)


def array_upgrade(env, array, analysis_station, action_station):
    while True:
        if check_queue() < (array.flow_rate-1)*5 and array.flow_rate > 1:
            array.flow_rate = array.flow_rate - 1
        if check_max_resource(array, analysis_station, action_station):
            while check_queue() > array.flow_rate*5:
                array.flow_rate = array.flow_rate + 1
        yield env.timeout(0.1)


def analysis_upgrade(env, analysis_station, array, action_station):
    while True:
        if len(array_analysis_queue) < (analysis_station.flow_rate-1)*5 and analysis_station.flow_rate > 1:
            analysis_station.flow_rate = analysis_station.flow_rate - 1
        if check_max_resource(array, analysis_station, action_station):
            while len(array_analysis_queue) > analysis_station.flow_rate*5:
                analysis_station.flow_rate = analysis_station.flow_rate + 1
        yield env.timeout(0.1)


def action_upgrade(env, action_station, array, analysis_station):
    while True:
        if len(array_action_queue) < (action_station.flow_rate - 1)*5 and action_station.flow_rate > 1:
            action_station.flow_rate = action_station.flow_rate - 1
        if check_max_resource(array, analysis_station, action_station):
            while len(array_action_queue) > action_station.flow_rate*5:
                action_station.flow_rate = action_station.flow_rate + 1
        yield env.timeout(1.1)


# export data at the end of runtime.
# data to include
# all plotted data - need to check how it's done maybe?

def main_run(ui, print_excel):
    # declare all required dictionaries so they can be deleted at the end of the run

    clock = {}
    UI_obj = {}

    if ui:
        UI_obj = UIClasses.PaintGrapic(
            sensor_array_queue,
            array_sensor_queue,
            array_analysis_queue,
            analysis_sublist,
            analysis_array_queue,
            array_action_queue,
            action_array_queue)

        clock = UIClasses.ClockAndDataDraw(1100, 260, 1290, 340, 0, sensor_list, data_age, data_age_by_type,
                                           successful_operations_total, number_of_sensors, agent_flow_rates_by_type,
                                           total_resource, self_organization_measure)

    env = simpy.rt.RealtimeEnvironment(factor=0.1, strict=False)
    # do not remove, it's a faster env function:
    # env = simpy.Environment()

    array = Array(env, ui)
    action_station = ActionStation(env)
    analysis_station = AnalysisStation(env, ui)
    env.process(create_clock(env, array, analysis_station, action_station, ui, clock, UI_obj))

    sensor_list.append(Sensor(0.5, 1, env))
    env.process(sensor_maker(env, array, analysis_station, action_station))
    env.process(array_upgrade(env, array, analysis_station, action_station))
    env.process(analysis_upgrade(env, analysis_station, array, action_station))
    env.process(action_upgrade(env, action_station, array, analysis_station))
    env.process(UIClasses.save_graph(env, end_time, now))

    env.run(until=end_time)

    if ui:
        UIClasses.main.mainloop()
    simulation_collector = {
        "data_age": data_age,
        "data_age_by_type": data_age_by_type,
        "successful_operations_total": successful_operations_total,
        "number_of_sensors": number_of_sensors,
        "agent_flow_rates_by_type": agent_flow_rates_by_type,
        "total_resource": total_resource,
        "self_organization_measure": self_organization_measure
    }

    if print_excel:
        print_to_file(simulation_collector)
    return simulation_collector


def print_to_file(simulation_collector):
    # convert into dataframe
    path = UIClasses.create_folder("excels", now)
    for val in simulation_collector:
        df = pd.DataFrame(data=simulation_collector[val])
        # df = df.T
        # convert into excel
        excel_name = path + "\\" + val + ".xlsx"
        df.to_excel(excel_name, index=False)





