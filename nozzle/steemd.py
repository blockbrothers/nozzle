from time import monotonic, sleep

from .client import RPCClient
from .exceptions import HungNodeError
from .utils import blockid_to_blocknumber, get_first_or_none


class SteemdClient(RPCClient):

    def get_block(self, block_number=None):
        if block_number is None:
            block_number = self.head_block_number

        return self.call('get_block', block_number, api='database_api')

    def get_blocks(self, start_block_number, end_block_number=None):
        if end_block_number is None:
            end_block_number = self.head_block_number

        for block_number in range(start_block_number, end_block_number + 1):
            yield self.get_block(block_number)

    def stream_blocks(self, irreversible=True, interval=None, max_blocks_catchup=None, node_hung_treshold=9):
        previous_block_nr = self.last_irreversible_block_number if irreversible else self.head_block_number
        if interval is None:
            interval = self.block_interval
        same_block_count = 0
        while True:
            t_start = monotonic()
            end_block_nr = self.last_irreversible_block_number if irreversible else self.head_block_number
            if end_block_nr == previous_block_nr:
                same_block_count += 1
                if same_block_count > node_hung_treshold:
                    raise HungNodeError
            if max_blocks_catchup is not None:
                previous_block_nr = max(previous_block_nr, (end_block_nr - max_blocks_catchup))
            for block in self.get_blocks(start_block_number=previous_block_nr + 1, end_block_number=end_block_nr):
                yield block
                if block is not None:
                    previous_block_nr = blockid_to_blocknumber(block['block_id'])

            sleep_time = max((interval - (monotonic() - t_start)), 0.1)
            sleep(sleep_time)

    def get_account(self, account):
        return get_first_or_none(self.get_accounts(account))

    def get_accounts(self, accounts):
        if isinstance(accounts, str):
            accounts = [accounts]

        return self.call('get_accounts', accounts, api='database_api')

    def get_account_reputation(self, account):
        reputation = get_first_or_none(self.call('get_account_reputations', account, 1, api='follow_api'))
        try:
            reputation = int(reputation['reputation'])
        except (TypeError, KeyError, ValueError):
            reputation = None

        return reputation

    def get_account_reputations(self, accounts):
        return [self.get_account_reputation(account) for account in accounts]

    def get_witnesses_by_id(self, ids):
        if isinstance(ids, str):
            ids = [ids]

        return self.call('get_witnesses', ids, api='database_api')

    def get_witnesses_by_account(self, accounts):
        if isinstance(accounts, str):
            accounts = [accounts]

        witnesses = []
        for account in accounts:
            witnesses.append(self.call('get_witness_by_account', account, api='database_api'))

        return witnesses

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
            self._block_interval = self.config.get('STEEM_BLOCK_INTERVAL', 3)

        return self._block_interval
