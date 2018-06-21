## Python SDK Demo App Using Redis For Event Queueing & Batching

This Demo App shows how you can override the default Optimizely `Event Dispatcher`, and instead enqueue events within Redis and dispatch them at a later time as a large batch request, rather than many single event tracking requests. This helps minimize the number of outbound network requests from your application server.

---

### Installation and Setup

This Demo App is based on [this repository](https://github.com/optimizely/python-sdk-demo-app). Follow the installation and setup instructions prior to advancing to the Redis configuration outlined below.

---

### Connecting to Redis

This app uses [Redis-Py](https://github.com/andymccurdy/redis-py) to connect to Redis. This dependency lives within the `requirements.txt` file, and will be installed automatically when following installation instructions.

The Redis connection settings live within the [redisbroker.py](https://github.com/cooperreid-optimizely/py-fullstack-redis-queue/blob/master/redisbroker.py#L7) file. Adapt the connection settings to reflect the location of your running redis instance.

### Overriding Optimizely's default dispatch with `Redis Deferred Dispatcher`

When instantiating the Optimizely client, pass the argument `event_dispatcher=RedisDeferredDispatcher()` as shown below:
```
from optimizely import optimizely
from redisdeferreddispatcher import RedisDeferredDispatcher

client = optimizely.Optimizely(datafile, event_dispatcher=RedisDeferredDispatcher())
```
> It's important an instance is passed into the constructor, not the class itself


### Using the `Redis Broker` to emit the enqueued events to Optimizely

At some scheduled interval, run the command that will dispatch the queued events to Optimizely and purge them from the local Redis store.
```
$ python redisbroker.py --emit
```
