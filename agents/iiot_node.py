# Every time step the sensors create new information bit.
    # Info has real/wrong status
    # Intel generated is randomly selected to be true or false with a certain precentage.

from agents.data_packet import DataPacket
import random

class IIoT_Node(object):
    def __init__(self, ctx, correctness_probability, order):
        self.ctx = ctx
        self.env = ctx.env
        self.action = self.env.process(self.run())
        self.correctness_probability = correctness_probability
        self.order = order
        self.name = "IIoT " + str(order)
        self.is_alive = True

    def run(self):
        while self.is_alive:
            # print('Create new info bit at time %d' % env.now)
            yield self.env.timeout(1)
            self.ctx.iiot_bus_queue.append(DataPacket(random.random() < self.correctness_probability,
                                           self.env.now, 'intel', self.name))