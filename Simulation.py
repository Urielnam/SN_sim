import simpy
import random
import pandas as pd
from datetime import datetime

from collections import defaultdict
from BackendClasses import clockanddatacalc_func
# import UIClasses

# -------------------------
# SIMULATION
# -------------------------
data_type_keys = ["intel", "feedback", "target"]

# Intel object. Has a real/wrong status and time created
# data types: "intel", "feedback"


class Data:
    def __init__(self, status, time, type, creator):
        # status parameter is real/false - it's the notion of if the data is right or wrong.
        self.status = status
        self.time = time
        # data types - intel, feedback
        self.type = type
        self.creator = creator
        # adds an image so that we can paint it later
        self.id = self.type + " from " + self.creator + "\n at time " + str(self.time)


# export data at the end of runtime.
# data to include
# all plotted data - need to check how it's done maybe?

def main_run(ui, print_excel, end_time, max_resource, dt):
    if ui:
        import UIClasses
    # declare all required dictionaries so they can be deleted at the end of the run

    # -------------------------
    # CONFIGURATION
    # -------------------------

    data_age = {}
    data_age_by_type = {}
    successful_operations = []

    timestep_list = []
  
    successful_operations_total = {}
    number_of_sensors = {}
    agent_flow_rates_by_type = {}
    agent_flow_rates_by_type["Array"] = {}
    agent_flow_rates_by_type["Analysis Station"] = {}
    agent_flow_rates_by_type["Action Station"] = {}
    total_resource = {}
    self_organization_measure = {}

    # max_resource = 15
    # end_time = 20

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
        data_age_by_type[key] = {}

    for key in data_type_keys:
        data_age_by_type[key] = {}

    start_row = 95
    regular_height = 30
    now = datetime.now().ctime()
    now = now.replace(":", "_")

    def create_clock(env, array, analysis_station, action_station, ui, clock, UI_obj):
        # This generator is meant to be used as a SimPy event to update the clock and the data in the UI

        while True:
            yield env.timeout(0.1)
            clockanddatacalc_func(data_type_keys, data_age_by_type, env, sensor_array_queue, array_analysis_queue,
                                  analysis_array_queue, array_action_queue, action_array_queue, array_sensor_queue,
                                  data_age, self_organization_measure, dt, agent_flow_rates_by_type, number_of_sensors,
                                  successful_operations_total, successful_operations, sensor_list, array,
                                  analysis_station, action_station, total_resource,timestep_list)

            if ui:
                clock.tick(env.now)
                UI_obj.tick()


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

            yield self.env.timeout(1 / self.flow_rate)

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

                    yield self.env.timeout(1 / self.flow_rate)

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
                    yield self.env.timeout(1 / self.flow_rate)
                    # print(array_action_queue[0].status)
                    if a.status:
                        # print("Attack successful!")
                        # send back positive feedback
                        action_array_queue.append(Data(True, self.env.now,
                                                       'feedback', a.creator))
                        successful_operations.append(self.env.now)
                    if not a.status:
                        # print("Attack failed")
                        # send back negative feedback
                        action_array_queue.append(Data(False, self.env.now,
                                                       'feedback', a.creator))

                else:
                    yield self.env.timeout(1)

    def check_max_resource(array, analysis_station, action_station):
        return (len(sensor_list) + array.flow_rate +
                analysis_station.flow_rate +
                action_station.flow_rate) < max_resource

    def create_new_sensor(sensor_number, external_environemnt):
        # set a random number for the chances of giving good info.
        sensor_chance = random.random()
        # add new sensor
        sensor_list.append(Sensor(sensor_chance, sensor_number, external_environemnt))
        # increase sensor count
        return sensor_number + 1

    def kill_sensor(sensor):
        sensor.is_alive = False
        sensor_list.remove(sensor)

    # we need to select how much we change the number of sensors, and then execute it.
    def sensor_maker(external_environemnt, array, analysis_station, action_station):
        sensor_number = 2

        while True:
            #   LOGIC FOR IMPLEMENTATION - suggestion
            # ---------------------------------------------
            # do not kill a sensor if it is the last one.
            # if we are at max resource, kill sensor.
            # if new feedback is gained:
            #   if good - create new sensor
            #   if bad - kill sensor
            # if none of the above - check self_org.
            #   if lower then threshold - calculate what would increase the self-org and act accordingly.
            #   currently, any change in number of sensors increases self-org.
            #   randomly decide if increasing or decreasing (considering you won't get over max resource or kill
            #   the last sensor

            # CURRENT LOGIC
            # -------------------------------------------
            # while there are any feedback data:
            while len(array_sensor_queue) > 0:

                # if action feedback is good, create new sensor and kill the data.
                # if action is right:
                if array_sensor_queue[0].status:

                    # if there are enough resources - grow the number of sensors. else - do nothing.
                    if check_max_resource(array, analysis_station, action_station):
                        sensor_number = create_new_sensor(sensor_number, external_environemnt)
                    # kill the data, even if you did not create a sensor.
                    array_sensor_queue.pop(0)
                # else, if actions is wrong and failed.
                else:
                    b = array_sensor_queue[0]
                    for sensor in sensor_list.copy():
                        # find the rouge sensor and kill it.
                        if sensor.name == b.creator:
                            kill_sensor(sensor)
                    # if the sensor list is empty, create a new sensor.
                    if len(sensor_list) == 0:
                        sensor_number = create_new_sensor(sensor_number, external_environemnt)
                    array_sensor_queue.pop(0)

            # if we are at max resource, reduce the number of sensors
            if not check_max_resource(array, analysis_station, action_station) and len(sensor_list) > 1:
                selected_sensor = random.choice(sensor_list)
                kill_sensor(selected_sensor)

            yield external_environemnt.timeout(0.1)

    def array_upgrade(env, array, analysis_station, action_station):
        while True:
            if check_queue() < (array.flow_rate - 1) * 5 and array.flow_rate > 1:
                array.flow_rate = array.flow_rate - 1
            if check_max_resource(array, analysis_station, action_station):
                while check_queue() > array.flow_rate * 5:
                    array.flow_rate = array.flow_rate + 1
            yield env.timeout(0.1)

    def analysis_upgrade(env, analysis_station, array, action_station):
        while True:
            if len(array_analysis_queue) < (analysis_station.flow_rate - 1) * 5 and analysis_station.flow_rate > 1:
                analysis_station.flow_rate = analysis_station.flow_rate - 1
            if check_max_resource(array, analysis_station, action_station):
                while len(array_analysis_queue) > analysis_station.flow_rate * 5:
                    analysis_station.flow_rate = analysis_station.flow_rate + 1
            yield env.timeout(0.1)

    def action_upgrade(env, action_station, array, analysis_station):
        while True:
            if len(array_action_queue) < (action_station.flow_rate - 1) * 5 and action_station.flow_rate > 1:
                action_station.flow_rate = action_station.flow_rate - 1
            if check_max_resource(array, analysis_station, action_station):
                while len(array_action_queue) > action_station.flow_rate * 5:
                    action_station.flow_rate = action_station.flow_rate + 1
            yield env.timeout(1.1)

    # original function
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

    if ui:
        env = simpy.rt.RealtimeEnvironment(factor=0.1, strict=False)
    else:
        # do not remove, it's a faster env function:
        env = simpy.Environment()

    array = Array(env, ui)
    action_station = ActionStation(env)
    analysis_station = AnalysisStation(env, ui)
    env.process(create_clock(env, array, analysis_station, action_station, ui, clock, UI_obj))

    sensor_list.append(Sensor(0.5, 1, env))
    env.process(sensor_maker(env, array, analysis_station, action_station))
    env.process(array_upgrade(env, array, analysis_station, action_station))
    env.process(analysis_upgrade(env, analysis_station, array, action_station))
    env.process(action_upgrade(env, action_station, array, analysis_station))
    if ui:
        env.process(UIClasses.save_graph(env, end_time, now))

    env.run(until=end_time)

    if ui:
        UIClasses.main.mainloop()

    local_simulation_collector = {
        "data_age": data_age,
        "data_age_by_type": data_age_by_type,
        "successful_operations_total": successful_operations_total,
        "number_of_sensors": number_of_sensors,
        "agent_flow_rates_by_type": agent_flow_rates_by_type,
        "total_resource": total_resource,
        "self_organization_measure": self_organization_measure,
        "successful_operations": successful_operations,
        "last dt timesteps": timestep_list
    }

    def print_to_file(local_simulation_collector):
        # convert into dataframe
        path = UIClasses.create_folder("excels", now)
        for val in local_simulation_collector:
            df = pd.DataFrame(data=local_simulation_collector[val])
            # df = df.T
            # convert into excel
            excel_name = path + "\\" + val + ".xlsx"
            df.to_excel(excel_name, index=False)


    if print_excel:
        print_to_file(local_simulation_collector)
    return local_simulation_collector







