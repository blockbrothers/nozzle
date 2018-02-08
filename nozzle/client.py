from itertools import cycle
import json
import logging
from socket import SOL_SOCKET, SO_KEEPALIVE

import certifi
from urllib3.connection import HTTPSConnection
from urllib3.connectionpool import connection_from_url
from urllib3.exceptions import TimeoutError, MaxRetryError, ClosedPoolError
from urllib3.response import HTTPResponse
from urllib3.util.retry import Retry
from urllib3.util.timeout import Timeout


logger = logging.getLogger(__name__)


METHOD_WHITELIST = Retry.DEFAULT_METHOD_WHITELIST.union({'POST'})
STATUS_FORCELIST = frozenset({408, 444, 499, 500, 502, 503, 504, 520, 521, 522, 523, 524, 527})
DEFAULT_RETRY_OPTS = {
    'connect': 5,
    'read': 0,
    'redirect': 5,
    'status': 3,
    'method_whitelist': METHOD_WHITELIST,
    'status_forcelist': STATUS_FORCELIST,
    'backoff_factor': 0.1,
    'raise_on_redirect': True,
    'raise_on_status': True
}


class RPCClient(object):

    def __init__(self, nodes, **kwargs):
        if 'retries' in kwargs:
            # We need to make sure these are set the way we want.
            retry = kwargs['retries']
            retry_params = {
                'method_whitelist': set(retry.method_whitelist).add('POST'),
                'raise_on_redirect': True,
                'raise_on_status': True,
            }
            kwargs['retries'] = retry.new(**retry_params)

        self.connection_options = {
            'maxsize': 5,
            'timeout': Timeout(total=5.0),
            'retries': Retry(**DEFAULT_RETRY_OPTS),
            'cert_reqs': 'CERT_REQUIRED',
            'ca_certs': certifi.where(),
            'headers': {
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
            },
            'socket_options': HTTPSConnection.default_socket_options + [(SOL_SOCKET, SO_KEEPALIVE, 1)]
        }
        self.connection_options.update(kwargs)
        self._connection = None

        self.failover_limit = len(nodes)

        self._nodes = cycle(nodes)
        self.connect()

    def __del__(self):
        self.disconnect()

    @property
    def nodes(self):
        return frozenset(self._nodes)

    def next_node(self):
        return self.connect(next(self._nodes))

    def connect(self, node=None):
        node_url = node or next(self._nodes)
        self.disconnect()
        self._connection = connection_from_url(node_url, **self.connection_options)
        logger.info("Current node changed to `{}`".format(self._connection.host))

        return node_url

    def disconnect(self):
        if self._connection:
            try:
                self._connection.close()
            except AttributeError:
                # This is a temporary workaround for https://github.com/shazow/urllib3/pull/1279
                pass

    def exec(self, name, *args, **kwargs):
        """Merely here for backwards-compatibility
        """
        return self.call(name, *args, **kwargs)

    def call(self, proc, *args, **kwargs):
        failover_limit = self.failover_limit if kwargs.pop('enable_failover', True) else 0
        failovers = 0
        response = None
        while True:
            try:
                response = self._call(proc, *args, **kwargs)
            except ClosedPoolError:
                logger.exception("Trying to make a call, but the connection pool is closed. Trying to reconnect.")
                self.connect()
            except MaxRetryError as e:
                logger.exception(e.reason)
                if failovers < failover_limit:
                    failovers += 1
                    self.next_node()
                else:
                    break
            else:
                if isinstance(response, HTTPResponse):
                    break

        decoded_response = {}
        try:
            decoded_response = json.loads(response.data.decode('utf-8'))
        except (UnicodeError, json.JSONDecodeError):
            logger.exception("Unable to decode response.")
        else:
            if not isinstance(decoded_response, dict):
                logger.critical("Invalid response received.")
                decoded_response = {}

        if 'error' in decoded_response:
            logger.critical(decoded_response['error'].get('message', 'Unknown RPC error occurred.'))

        return decoded_response.get('result', None)

    def _call(self, proc, *args, **kwargs):
        """This method should either return a valid response, or raise an exception.
        """
        body = {
            'jsonrpc': '2.0',
            'id': kwargs.pop('call_id', 0),
            'method': 'call',
        }
        api = kwargs.pop('api', None)
        if kwargs:
            body['params'] = [api, proc, kwargs]
        elif api:
            body['params'] = [api, proc, args]
        else:
            body.update({
                'method': proc,
                'params': args,
            })

        body = json.dumps(body, ensure_ascii=False, default=str, separators=(',', ':')).encode('utf-8')
        return self._connection.request('POST', '/', body=body)
