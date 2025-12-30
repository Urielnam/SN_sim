from agents.data_packet import DataPacket

# scada actuator acts when there is correct datapack in the pipeline
class SCADA_Actuator(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.env = ctx.env
        self.action = self.env.process(self.run())
        self.flow_rate = 1

    def run(self):
        while True:

            if len(self.ctx.bus_scada_queue) > 0:
                a = self.ctx.bus_scada_queue[0]
                self.ctx.bus_scada_queue.pop(0)
                self.ctx.scada_data_usage_time.append(self.env.now - a.time)
                yield self.env.timeout(1 / self.flow_rate)
                # print(bus_scada_queue[0].status)
                if a.status:
                    # print("Attack successful!")
                    # send back positive feedback
                    self.ctx.scada_bus_queue.append(DataPacket(True, self.env.now,
                                                   'feedback', a.creator))
                    self.ctx.successful_operations.append(self.env.now)
                if not a.status:
                    # print("Attack failed")
                    # send back negative feedback
                    self.ctx.scada_bus_queue.append(DataPacket(False, self.env.now,
                                                   'feedback', a.creator))

            else:
                yield self.env.timeout(1)
