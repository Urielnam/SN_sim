import UIClasses, random
from agents.data_packet import DataPacket

# need to create edge processor station, then scada actuator and then start messing with accuracy.
# if one of the intel is true, the intel is correct and the boogie is found. if both are false, the attack failes.
# I need to change it so it ingests one intel article per cycle.
class Edge_Processor(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.env = ctx.env
        self.action = ctx.env.process(self.run())
        self.ui_flag = ctx.config.ui
        self.flow_rate = 1
        if self.ui_flag:
            self.draw = UIClasses.EdgeStationDraw()

    def run(self):

        while True:
            # first, check for feedback in first cell, if there isn't any feedback, proceed to analyze the data.

            bank_size = 2

            if len(self.ctx.bus_edge_queue) == 0:
                yield self.env.timeout(1)

            else:
                moved_item = self.ctx.bus_edge_queue[0]
                self.ctx.bus_edge_queue.pop(0)
                self.ctx.edge_data_usage_time.append(self.env.now - moved_item.time)

                if self.ui_flag:
                    self.draw.run_draw(moved_item)

                yield self.env.timeout(1 / self.flow_rate)

                if self.ui_flag:
                    self.draw.run_delete()

                if moved_item.type == 'feedback':
                    self.ctx.edge_bus_queue.append(moved_item)

                # if data type is info, save it for digestion
                else:
                    # add data to data bank.
                    self.ctx.edge_sublist.append(moved_item)

                    # if bank size is equal to bank_size, delete bank and create new data
                    if len(self.ctx.edge_sublist) == bank_size:
                        self.ctx.edge_bus_queue.append(DataPacket(self.ctx.edge_sublist[0].status or self.ctx.edge_sublist[1].status,
                                                         self.env.now, 'target',
                                                         random.choice(self.ctx.edge_sublist).creator))
                        self.ctx.edge_sublist.pop(0)
                        self.ctx.edge_sublist.pop(0)
