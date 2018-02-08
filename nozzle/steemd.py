from time import monotonic, sleep

from .client import RPCClient
from .utils import blockid_to_blocknumber


class SteemdClient(RPCClient):

    def get_block(self, block_number=None):
        if block_number is None:
            block_number = self.head_block_number

        return self.call('get_block', block_number, api='database_api')

    def get_blocks(self, start_block_number, end_block_number=None):
        if end_block_number is None:
            end_block_number = self.head_block_number

        for block_number in range(start_block_number, end_block_number + 1):
            block = self.get_block(block_number)
            if block is not None:
                yield block

    def stream_blocks(self, irreversible=True):
        previous_block_nr = self.last_irreversible_block_number if irreversible else self.head_block_number
        block_interval = self.block_interval
        prev_time = monotonic()
        while True:
            end_block_nr = self.last_irreversible_block_number if irreversible else self.head_block_number
            for block in self.get_blocks(start_block_number=previous_block_nr + 1, end_block_number=end_block_nr):
                yield block
                previous_block_nr = blockid_to_blocknumber(block['block_id'])

            curr_time = monotonic()
            sleep_time = max((block_interval - (curr_time - prev_time)), 0)
            prev_time = curr_time
            sleep(sleep_time)

    @property
    def dynamic_global_properties(self):
        return self.call('get_dynamic_global_properties', api='database_api')

    @property
    def chain_properties(self):
        return self.call('get_chain_properties', api='database_api')

    @property
    def config(self):
        return self.call('get_config', api='database_api')

    @property
    def last_irreversible_block_number(self):
        return self.dynamic_global_properties.get('last_irreversible_block_num')

    @property
    def head_block_number(self):
        return self.dynamic_global_properties.get('head_block_number')

    @property
    def block_interval(self):
        # We cache this
        if not hasattr(self, '_block_interval'):
            self._block_interval = self.config.get('STEEMIT_BLOCK_INTERVAL')

        return self._block_interval
