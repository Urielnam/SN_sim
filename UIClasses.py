import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


f = plt.Figure(figsize=(2, 2), dpi=72)
a3 = f.add_subplot(121)
a3.plot()
a1 = f.add_subplot(222)
a1.plot()
a2 = f.add_subplot(224)
a2.plot()


class IsrElement:
    text_height = 30
    icon_top_margin = -8

    def __init__(self, element_name, canvas, x_top, y_top, length, height):
        self.element_name = element_name
        self.x_top = x_top
        self.y_top = y_top
        self.length = length
        self.canvas = canvas

        canvas.create_rectangle(x_top, y_top, x_top + length, y_top + height)
        canvas.create_text(x_top + 10, y_top + 7, anchor = tk.NW, text = f"{element_name}")
        self.canvas.update()



class QueueGraphics:
    text_height = 30
    icon_top_margin = -8

    def __init__(self, data_container, icon_height,  data_name, canvas, x_top, y_top):
        # self.icon_file = icon_file
        self.icon_height = icon_height
        self.queue_name = data_name
        self.canvas = canvas
        self.x_top = x_top
        self.y_top = y_top

        # self.image = tk.PhotoImage(file = self.icon_file)
        self.icons = []
        self.data_contained = data_container
        canvas.create_text(x_top, y_top, anchor = tk.NW, text = f"{data_name}")
        self.canvas.update()

    def paint_queue(self):
        # delete all current representations
        for i in self.icons:
            to_del = self.icons.pop()
            self.canvas.delete(to_del)
            self.canvas.update()
        # redraw for all current items contained
        x = self.x_top + 15
        y = self.y_top + 45

        for i in self.data_contained:
            self.icons.append(
                self.canvas.create_image(x, y, anchor = tk.NW, image = image_map2[i.type])
            )
            self.icons.append(self.canvas.create_text(x - 10, y + 30, anchor = tk.NW, text = i.id))
            y = y + self.icon_height + 45
        self.canvas.update()

class PaintGrapic:

    def __init__(
            self, canvas, start_row,
            sensor_array_queue,
            array_sensor_queue,
            array_analysis_queue,
            analysis_sublist,
            analysis_array_queue,
            array_action_queue,
            action_array_queue
            ):
        self.sensor_array = QueueGraphics(sensor_array_queue, 25, "Sensor to \n Array", canvas, 100, start_row)
        self.array_sensor = QueueGraphics(array_sensor_queue, 25, "Array to \n Sensor", canvas,
                                     200, start_row)
        self.array_analysis = QueueGraphics(array_analysis_queue, 25, "Array to \n Analysis", canvas, 300, start_row)
        self.analysis_sublist_visual = QueueGraphics(analysis_sublist, 25, "Analysis Station \n Bank", canvas, 600,
                                                start_row)
        self.analysis_array = QueueGraphics(analysis_array_queue, 25, "Analysis to \n Array", canvas, 700, start_row)
        self.array_action = QueueGraphics(array_action_queue, 25, "Array to \n Action", canvas, 800, start_row)
        self.action_array = QueueGraphics(action_array_queue, 25, "Action to \n Array", canvas, 900, start_row)


    def tick(self):
        self.sensor_array.paint_queue()
        self.array_sensor.paint_queue()
        self.array_analysis.paint_queue()
        self.analysis_array.paint_queue()
        self.array_action.paint_queue()
        self.action_array.paint_queue()
        self.analysis_sublist_visual.paint_queue()


class ClockAndDataDraw:

    def __init__(self, canvas, x1, y1, x2, y2, time, main):
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
        self.data_plot = FigureCanvasTkAgg(f, master=main)
        self.data_plot.get_tk_widget().config(height=400)
        self.data_plot.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def paint_sensors():
        for i in sensor_list_visual:
            to_del = sensor_list_visual.pop()
            canvas.delete(to_del)
            canvas.update()

        n = 1

        for x in sensor_list:
            element_name = x.name
            x_top = 5
            y_top = start_row + (regular_height + 10) * (n - 1)
            n = n + 1
            length = 60
            height = regular_height

            sensor_list_visual.append(canvas.create_rectangle(x_top, y_top,
                                                              x_top + length,
                                                              y_top + height))
            sensor_list_visual.append(canvas.create_text(x_top + 10, y_top + 7,
                                                         anchor=tk.NW,
                                                         text=f"{element_name}"))
            canvas.update()


    def tick(self, time, canvas):
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

        self.paint_sensors()

        a1.cla()
        a1.set_xlabel("Time")
        a1.set_ylabel("Average Data Age")
        # # code to calculate step function.
        # ages = [env.now - a.time for a in (sensor_array_queue + array_analysis_queue + analysis_array_queue +
        #                                     array_action_queue + action_array_queue + array_sensor_queue)]
        # data_age[float(env.now)].append(ages)
        #
        # for key in image_map2.keys():
        #     data_age_by_type[key][float(env.now)].append(
        #         [env.now - a.time for a in [
        #             i for i in (sensor_array_queue + array_analysis_queue + analysis_array_queue +
        #                         array_action_queue + action_array_queue + array_sensor_queue) if i.type == key]])

        a1.plot([t for (t, age) in  .items()], [np.mean(age) for (t, age) in data_age.items()], label="all")

        for key in image_map2.keys():
            a1.plot([t for (t, age) in data_age_by_type[key].items()],
                    [np.mean(age) for (t, age) in data_age_by_type[key].items()], label = key)
        a1.legend(loc="upper left")

        dt = 5

        a2.cla()
        a2.set_xlabel("Time")
        a2.set_ylabel("Accumulated Success")
        # code to calculate step function.
        # successful_operations_total[float(env.now)].append(len([x for x in successful_operations if x > env.now - dt]))
        a2.plot([t for (t, success) in successful_operations_total.items()],
                [success for (t, success) in successful_operations_total.items()],
                label = "Average success over last " + str(dt) + " timesteps")


        a3.cla()
        a3.set_xlabel("Time")
        a3.set_ylabel("System Cost")
        # # code to calculate step function.
        # number_of_sensors[float(env.now)].append(len(sensor_list))
        # agent_flow_rates_by_type["Array"][float(env.now)].append(array.flow_rate)
        # agent_flow_rates_by_type["Analysis Station"][float(env.now)].append(
        #     analysis_station.flow_rate)
        # agent_flow_rates_by_type["Action Station"][float(env.now)].append(
        #     action_station.flow_rate)
        # total_resource[float(env.now)].append(len(sensor_list)+array.flow_rate +
        #                                       analysis_station.flow_rate +
        #                                       action_station.flow_rate)



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

        # self_organization_measure[float(env.now)].append(calc_self_org(dt))
        a2.plot([t for (t,a) in self_organization_measure.items()],
                [a for (t,a) in self_organization_measure.items()],
                label = "Self-organization effort over last " + str(dt) + " timesteps")

        a2.legend(loc="upper left")


        self.data_plot.draw()
        self.canvas.update()