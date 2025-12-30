import simpy
import random
import pandas as pd
from datetime import datetime

from BackendClasses import clockanddatacalc_func

from sim_context import SimulationContext

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

def main_run(config):

    if config.ui:
        import UIClasses

    now = datetime.now().ctime()
    now = now.replace(":", "_")

    def create_clock(ctx, array, analysis_station, action_station, clock, UI_obj):
        # This generator is meant to be used as a SimPy event to update the clock and the data in the UI

        while True:
            yield ctx.env.timeout(0.1)
            clockanddatacalc_func(ctx, array, analysis_station, action_station)

            if config.ui:
                clock.tick(ctx.env.now)
                UI_obj.tick()


    # Every time step the sensors create new information bit.
    # Info has real/wrong status
    # Intel generated is randomly selected to be true or false with a certain precentage.
    class Sensor(object):
        def __init__(self, ctx, correctness_probability, order):
            self.ctx = ctx
            self.env = ctx.env
            self.action = self.env.process(self.run())
            self.correctness_probability = correctness_probability
            self.order = order
            self.name = "Sensor " + str(order)
            self.is_alive = True

        def run(self):
            while self.is_alive:
                # print('Create new info bit at time %d' % env.now)
                yield self.env.timeout(1)
                self.ctx.sensor_array_queue.append(Data(random.random() < self.correctness_probability,
                                               self.env.now, 'intel', self.name))

    # The array moves data between different queues. It can move only one object per lane.
    class Array(object):
        def __init__(self, ctx):
            self.ctx = ctx
            self.env = ctx.env
            self.action = self.env.process(self.run())
            self.ui_flag = ctx.config.ui

            self.flow_rate = 1

            if self.ui_flag:
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
                    if check_queue(self.ctx) == 0:
                        yield self.env.timeout(1)
                        break
                    selected_array = random.choice([x for x in ctx.start_nodes.keys() if len(ctx.start_nodes[x]) > 0])
                    second_array = ctx.config.connecting_graph[selected_array][ctx.start_nodes[selected_array][0].type]
                    yield self.env.process(self.move_item(ctx.start_nodes[selected_array], ctx.end_nodes[second_array]))

    def check_queue(ctx):
        return len(ctx.sensor_array_queue) + len(ctx.analysis_array_queue) + len(ctx.action_array_queue)

    # need to create analysis station, then action station and then start messing with accuracy.
    # if one of the intel is true, the intel is correct and the boogie is found. if both are false, the attack failes.
    # I need to change it so it ingests one intel article per cycle.
    class AnalysisStation(object):
        def __init__(self, ctx):
            self.ctx = ctx
            self.env = ctx.env
            self.action = ctx.env.process(self.run())
            self.ui_flag = ctx.config.ui
            self.flow_rate = 1
            if self.ui_flag:
                self.draw = UIClasses.AnalysisStationDraw()

        def run(self):

            while True:
                # first, check for feedback in first cell, if there isn't any feedback, proceed to analyze the data.

                bank_size = 2

                if len(self.ctx.array_analysis_queue) == 0:
                    yield self.env.timeout(1)

                else:
                    moved_item = self.ctx.array_analysis_queue[0]
                    self.ctx.array_analysis_queue.pop(0)
                    self.ctx.analysis_data_usage_time.append(self.env.now - moved_item.time)

                    if self.ui_flag:
                        self.draw.run_draw(moved_item)

                    yield self.env.timeout(1 / self.flow_rate)

                    if self.ui_flag:
                        self.draw.run_delete()

                    if moved_item.type == 'feedback':
                        self.ctx.analysis_array_queue.append(moved_item)

                    # if data type is info, save it for digestion
                    else:
                        # add data to data bank.
                        self.ctx.analysis_sublist.append(moved_item)

                        # if bank size is equal to bank_size, delete bank and create new data
                        if len(self.ctx.analysis_sublist) == bank_size:
                            self.ctx.analysis_array_queue.append(Data(ctx.analysis_sublist[0].status or self.ctx.analysis_sublist[1].status,
                                                             self.env.now, 'target',
                                                             random.choice(self.ctx.analysis_sublist).creator))
                            self.ctx.analysis_sublist.pop(0)
                            self.ctx.analysis_sublist.pop(0)

    # action_station acts when there is intel in the pipeline
    class ActionStation(object):
        def __init__(self, ctx):
            self.ctx = ctx
            self.env = ctx.env
            self.action = self.env.process(self.run())
            self.flow_rate = 1

        def run(self):
            while True:

                if len(self.ctx.array_action_queue) > 0:
                    a = self.ctx.array_action_queue[0]
                    self.ctx.array_action_queue.pop(0)
                    self.ctx.action_data_usage_time.append(self.env.now - a.time)
                    yield self.env.timeout(1 / self.flow_rate)
                    # print(array_action_queue[0].status)
                    if a.status:
                        # print("Attack successful!")
                        # send back positive feedback
                        self.ctx.action_array_queue.append(Data(True, self.env.now,
                                                       'feedback', a.creator))
                        self.ctx.successful_operations.append(self.env.now)
                    if not a.status:
                        # print("Attack failed")
                        # send back negative feedback
                        self.ctx.action_array_queue.append(Data(False, self.env.now,
                                                       'feedback', a.creator))

                else:
                    yield self.env.timeout(1)

    def check_max_resource(ctx, array, analysis_station, action_station):
        return (len(ctx.sensor_list) + array.flow_rate +
                analysis_station.flow_rate +
                action_station.flow_rate) < ctx.config.max_resource

    def create_new_sensor(sensor_number, ctx):
        # set a random number for the chances of giving good info.
        # sensor accuracy = sensor_acc.
        sensor_chance = config.sensor_acc*random.random()
        # add new sensor
        ctx.sensor_list.append(Sensor(ctx, sensor_chance, sensor_number))
        # increase sensor count
        return sensor_number + 1

    def kill_sensor(ctx, sensor):
        sensor.is_alive = False
        ctx.sensor_list.remove(sensor)

    # we need to select how much we change the number of sensors, and then execute it.


    def sensor_maker(ctx, array, analysis_station, action_station):
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
            while len(ctx.array_sensor_queue) > 0:

                # if action feedback is good, create new sensor and kill the data.
                # if action is right:
                if ctx.array_sensor_queue[0].status:

                    # if there are enough resources - grow the number of sensors. else - do nothing.
                    if check_max_resource(ctx, array, analysis_station, action_station):
                        sensor_number = create_new_sensor(sensor_number, ctx)
                    # kill the data, even if you did not create a sensor.
                    ctx.array_sensor_queue.pop(0)
                # else, if actions is wrong and failed.
                else:
                    b = ctx.array_sensor_queue[0]
                    for sensor in ctx.sensor_list.copy():
                        # find the rouge sensor and kill it.
                        if sensor.name == b.creator:
                            kill_sensor(ctx, sensor)
                    # if the sensor list is empty, create a new sensor.
                    if len(ctx.sensor_list) == 0:
                        sensor_number = create_new_sensor(sensor_number, ctx.env)
                    ctx.array_sensor_queue.pop(0)

            # if we are at max resource, reduce the number of sensors
            if not check_max_resource(ctx, array, analysis_station, action_station) and len(ctx.sensor_list) > 1:
                selected_sensor = random.choice(ctx.sensor_list)
                kill_sensor(ctx, selected_sensor)

            if config.self_org_active:
                """
                main goal - if self-org is less than 10, have every agent type "vibrate".
                check if condition is applied.
                check if self_org is less than 10 (ampiric)
                check if equal to last step.
                try to increase (enough resources?)
                if not enough resources
                try to decrease (enough spare to decrease?)
                if failed - do nothing.
                """
                if len(ctx.self_organization_measure) > 600:
                    if list(ctx.self_organization_measure.values())[-1][0] < ctx.config.self_org_threshold:
                        if len(ctx.sensor_list) == list(ctx.number_of_sensors.values())[-1][0]:
                            if check_max_resource(ctx, array, analysis_station, action_station):
                                sensor_number = create_new_sensor(sensor_number, ctx.env)
                            else:
                                if len(ctx.sensor_list) > 1:
                                    removed_sensor = random.choice(ctx.sensor_list.copy())
                                    kill_sensor(ctx, removed_sensor)

            yield ctx.env.timeout(0.1)

    # same as previous logic, only with general object
    # object could be array, analysis station or action upgrade
    def increase_self_org(ctx, object, object_name):

        if config.self_org_active:
            if len(ctx.self_organization_measure) > 600:
                if list(ctx.self_organization_measure.values())[-1][0] < ctx.config.self_org_threshold:
                    if object.flow_rate == list(ctx.agent_flow_rates_by_type[object_name].values())[-1]:
                        if check_max_resource(ctx, array, analysis_station, action_station):
                            object.flow_rate = object.flow_rate + 1
                        else:
                            if object.flow_rate > 1:
                                object.flow_rate = object.flow_rate - 1

    def array_upgrade(ctx, array, analysis_station, action_station):
        while True:
            if check_queue(ctx) < (array.flow_rate - 1) * 5 and array.flow_rate > 1:
                array.flow_rate = array.flow_rate - 1
            if check_max_resource(ctx, array, analysis_station, action_station):
                while check_queue(ctx) > array.flow_rate * 5:
                    array.flow_rate = array.flow_rate + 1
            increase_self_org(ctx, array, "Array")
            yield ctx.env.timeout(0.1)

    def analysis_upgrade(ctx, analysis_station, array, action_station):
        while True:
            if len(ctx.array_analysis_queue) < (analysis_station.flow_rate - 1) * 5 and analysis_station.flow_rate > 1:
                analysis_station.flow_rate = analysis_station.flow_rate - 1
            if check_max_resource(ctx, array, analysis_station, action_station):
                while len(ctx.array_analysis_queue) > analysis_station.flow_rate * 5:
                    analysis_station.flow_rate = analysis_station.flow_rate + 1
            increase_self_org(ctx, analysis_station, "Analysis Station")
            yield ctx.env.timeout(0.1)

    def action_upgrade(ctx, action_station, array, analysis_station):
        while True:
            if len(ctx.array_action_queue) < (action_station.flow_rate - 1) * 5 and action_station.flow_rate > 1:
                action_station.flow_rate = action_station.flow_rate - 1
            if check_max_resource(ctx, array, analysis_station, action_station):
                while len(ctx.array_action_queue) > action_station.flow_rate * 5:
                    action_station.flow_rate = action_station.flow_rate + 1
            increase_self_org(ctx, action_station, "Action Station")
            yield ctx.env.timeout(1.1)

    # original function
    clock = {}
    UI_obj = {}

    if config.ui:
        env = simpy.rt.RealtimeEnvironment(factor=0.1, strict=False)
        ctx = SimulationContext(env, config)

        UI_obj = UIClasses.PaintGrapic(
            ctx.sensor_array_queue,
            ctx.array_sensor_queue,
            ctx.array_analysis_queue,
            ctx.analysis_sublist,
            ctx.analysis_array_queue,
            ctx.array_action_queue,
            ctx.action_array_queue)

        clock = UIClasses.ClockAndDataDraw(ctx,1100, 260, 1290, 340, 0)

    else:
        # do not remove, it's a faster env function:
        env = simpy.Environment()
        ctx = SimulationContext(env, config)



    array = Array(ctx)
    action_station = ActionStation(ctx)
    analysis_station = AnalysisStation(ctx)
    env.process(create_clock(ctx, array, analysis_station, action_station, clock, UI_obj))

    ctx.sensor_list.append(Sensor(ctx,0.5, 1))
    env.process(sensor_maker(ctx, array, analysis_station, action_station))
    env.process(array_upgrade(ctx, array, analysis_station, action_station))
    env.process(analysis_upgrade(ctx, analysis_station, array, action_station))
    env.process(action_upgrade(ctx, action_station, array, analysis_station))

    if config.ui:
        env.process(UIClasses.save_graph(ctx, now))

    env.run(until=config.end_time)

    if config.ui:
        UIClasses.main.mainloop()

    local_simulation_collector = {
        "data_age": ctx.data_age,
        "data_age_by_type": ctx.data_age_by_type,
        "successful_operations_total": ctx.successful_operations_total,
        "number_of_sensors": ctx.number_of_sensors,
        "agent_flow_rates_by_type": ctx.agent_flow_rates_by_type,
        "total_resource": ctx.total_resource,
        "self_organization_measure": ctx.self_organization_measure,
        "successful_operations": ctx.successful_operations,
        "last dt timesteps": ctx.timestep_list
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


    if config.print_excel:
        print_to_file(local_simulation_collector)
    return local_simulation_collector







