# nozzle
A minimal Python library for the Steem Blockchain.

## Requirements
Nozzle requires Python >= 3.5

## Dependencies
Nozzle depends on the following external packages:
- urllib3
- certifi

## Installation
```bash
pip install --upgrade pip setuptools
pip install steem-nozzle
```

## Usage
```python
from nozzle import Steem

steem = Steem(nodes=[
    'https://api.steemit.com',
    'https://steemd.minnowsupportproject.org',
    'https://steemd.privex.io',
    'https://steemd.pevo.science',
    'https://rpc.steemliberator.com',
    'https://gtg.steem.house:8090',
])

print(steem.dynamic_global_properties)
print(steem.call('get_accounts', ['blockbrothers']))
```

`nozzle.Steem` (`nozzle.steemd.SteemdClient`) is a subclass of `nozzle.client.RPCClient` with more high-level functions to interact with _steemd_ (more to be added in the future).

Use `RPCClient` as a low-level interface to _steemd_. You can make API requests by utilizing the `call()` method on an instance:
```python
print(client.call('get_accounts', ['blockbrothers']))
```

If you'd like fine-grained control over the retry configuration, pass an instance of [urllib3.util.retry.Retry](http://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html?highlight=Retry#urllib3.util.retry.Retry) when creating an instance of `RPCClient`:
```python
from urllib3.util.retry import Retry
from nozzle.client import DEFAULT_RETRY_OPTS
retries=Retry(**DEFAULT_RETRY_OPTS)
```
Please note that for correct failover behaviour, `raise_on_redirect` and `raise_on_status` need to be set to `True`. Also, `POST` is required to be in the `method_whitelist`. If you omit these or supply different values, it will be overridden by _nozzle_ to ensure proper functioning.

For convenience, you can access the default Retry() settings from `nozzle.client.DEFAULT_RETRY_OPTS`:
```python
METHOD_WHITELIST = Retry.DEFAULT_METHOD_WHITELIST.union({'POST'})
STATUS_FORCELIST = {408, 444, 499, 500, 502, 503, 504, 520, 521, 522, 523, 524, 527}

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
```

The timeouts can be controlled by providing an [urllib3.util.timeout.Timeout](http://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#urllib3.util.timeout.Timeout) instance:
```python
from urllib3.util.timeout import Timeout
from nozzle.client import RPCClient

client = RPCClient(nodes=['https://api.steemit.com'], timeout=Timeout(connect=2.0, read=7.0))
```

Extend `nozzle.client.RPCClient` or `nozzle.steemd.SteemdClient` to support more operations.
