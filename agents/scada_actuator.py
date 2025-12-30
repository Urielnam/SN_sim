from agents.data_packet import DataPacket

# scada actuator acts when there is correct datapack in the pipeline
class SCADAActuator(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.env = ctx.env
        self.action = self.env.process(self.run())
        self.flow_rate = 1

    def run(self):
        while True:

            # 1. WAIT
            # Sleep until the Bus delivers a 'Target' packet
            target_packet = yield self.ctx.bus_scada_queue.get()

            # Record metrics (Latency calculation)
            self.ctx.scada_data_usage_time.append(self.env.now - target_packet.time)

            # 2. Actuate
            yield self.env.timeout(1 / self.flow_rate)

            # 3. FEEDBACK GENERATION
            # Determine if the operation was a success based on the packet's truth value
            is_success = target_packet.status

            if is_success:
                # Log success for statistics
                self.ctx.successful_operations.append(self.env.now)

            # Create the feedback packet
            feedback_packet = DataPacket(
                status = is_success,
                time = self.env.now,
                type='feedback',
                creator=target_packet.creator
            )

            yield self.ctx.send_to_bus(feedback_packet)
