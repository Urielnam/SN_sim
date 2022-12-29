class ClockAndDataDraw:
    def __init__(self, canvas, x1, y1, x2, y2, time):
        # Draw the inital state of the clock and data on the canvas
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.canvas = canvas
        self.train = canvas.create_rectangle(self.x1, self.y1, self.x2, self.y2, fill="#fff")
        self.time = canvas.create_text(self.x1 + 10, self.y1 + 10, text="Time = " + str(round(time, 1)) + "m",
                                       anchor=tk.NW)
        # Code to show the seller wait time at queue.
        #self.seller_wait = canvas.create_text(self.x1 + 10, self.y1 + 40,
        #                                      text="Avg. Seller Wait  = " + str(avg_wait(seller_waits)), anchor=tk.NW)
        # Code to show the scanner wait time at queue.
        #self.scan_wait = canvas.create_text(self.x1 + 10, self.y1 + 70,
        #                                    text="Avg. Scanner Wait = " + str(avg_wait(scan_waits)), anchor=tk.NW)
        self.canvas.update()

    def tick(self, time):
        # re-draw the clock and data fields on the canvas. Also update the matplotlib charts
        self.canvas.delete(self.time)

        # Delete previous data.
        #self.canvas.delete(self.seller_wait)
        #self.canvas.delete(self.scan_wait)

        self.time = canvas.create_text(self.x1 + 10, self.y1 + 10, text="Time = " + str(round(time, 1)) + "m",
                                       anchor=tk.NW)
        # set new data.
        #self.seller_wait = canvas.create_text(self.x1 + 10, self.y1 + 30,
        #                                      text="Avg. Seller Wait  = " + str(avg_wait(seller_waits)) + "m",
        #                                      anchor=tk.NW)
        #self.scan_wait = canvas.create_text(self.x1 + 10, self.y1 + 50,
        #                                    text="Avg. Scanner Wait = " + str(avg_wait(scan_waits)) + "m", anchor=tk.NW)

        paint_sensors()

        a1.cla()
        a1.set_xlabel("Time")
        a1.set_ylabel("Average Data Age")
        # code to calculate step function.
        ages = [env.now - a.time for a in (sensor_array_queue + array_analysis_queue + analysis_array_queue +
                                            array_action_queue + action_array_queue + array_sensor_queue)]
        data_age[float(env.now)].append(ages)

        for key in image_map2.keys():
            data_age_by_type[key][float(env.now)].append(
                [env.now - a.time for a in [
                    i for i in (sensor_array_queue + array_analysis_queue + analysis_array_queue +
                                array_action_queue + action_array_queue + array_sensor_queue) if i.type == key]])

        a1.plot([t for (t, age) in data_age.items()], [np.mean(age) for (t, age) in data_age.items()], label="all")

        for key in image_map2.keys():
            a1.plot([t for (t, age) in data_age_by_type[key].items()],
                    [np.mean(age) for (t, age) in data_age_by_type[key].items()], label = key)
        a1.legend(loc="upper left")

        dt = 5

        a2.cla()
        a2.set_xlabel("Time")
        a2.set_ylabel("Accumulated Success")
        # code to calculate step function.
        successful_operations_total[float(env.now)].append(len([x for x in successful_operations if x > env.now - dt]))
        a2.plot([t for (t, success) in successful_operations_total.items()],
                [success for (t, success) in successful_operations_total.items()],
                label = "Average success over last " + str(dt) + " timesteps")


        a3.cla()
        a3.set_xlabel("Time")
        a3.set_ylabel("System Cost")
        # code to calculate step function.
        number_of_sensors[float(env.now)].append(len(sensor_list))
        agent_flow_rates_by_type["Array"][float(env.now)].append(array.flow_rate)
        agent_flow_rates_by_type["Analysis Station"][float(env.now)].append(
            analysis_station.flow_rate)
        agent_flow_rates_by_type["Action Station"][float(env.now)].append(
            action_station.flow_rate)
        total_resource[float(env.now)].append(len(sensor_list)+array.flow_rate +
                                              analysis_station.flow_rate +
                                              action_station.flow_rate)



        a3.plot([t for (t, a) in number_of_sensors.items()],
                [a for (t, a) in number_of_sensors.items()],
                label="Sensors")

        for key in agent_flow_rates_by_type.keys():
            a3.plot([t for (t, a) in agent_flow_rates_by_type[key].items()],
                    [a for (t, a) in agent_flow_rates_by_type[key].items()],
                    label=key)
        a3.plot([t for (t,a) in total_resource.items()],
                [a for (t,a) in total_resource.items()],
                label="Total")

        a3.legend(loc="upper left")

        # to calculate self-org, check how much the system has been
        # "in motion" for the last X timesteps.
        # sum of number of times the resources were re-allocated.

        dt = 5

        self_organization_measure[float(env.now)].append(calc_self_org(dt))
        a2.plot([t for (t,a) in self_organization_measure.items()],
                [a for (t,a) in self_organization_measure.items()],
                label = "Self-organization effort over last " + str(dt) + " timesteps")

        a2.legend(loc="upper left")


        data_plot.draw()
        self.canvas.update()