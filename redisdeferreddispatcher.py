from redisbroker import RedisBroker

class RedisDeferredDispatcher(object):

  def __init__(self):
    self.redis_client = RedisBroker()

  def dispatch_event(self, event):
    """
    Store event in Redis
    """
    self.redis_client.store_event(event)
  