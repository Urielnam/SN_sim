# The network bus moves data between different queues. It can move only one object per lane.

import UIClasses, random


def check_queue(ctx):
    return len(ctx.iiot_bus_queue) + len(ctx.edge_bus_queue) + len(ctx.scada_bus_queue)

class Network_Bus(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.env = ctx.env
        self.action = self.env.process(self.run())
        self.ui_flag = ctx.config.ui

        self.flow_rate = 1

        if self.ui_flag:
            self.arr = UIClasses.BusDraw()

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
                selected_array = random.choice([x for x in self.ctx.start_nodes.keys() if len(self.ctx.start_nodes[x]) > 0])
                second_array = self.ctx.config.connecting_graph[selected_array][self.ctx.start_nodes[selected_array][0].type]
                yield self.env.process(self.move_item(self.ctx.start_nodes[selected_array], self.ctx.end_nodes[second_array]))