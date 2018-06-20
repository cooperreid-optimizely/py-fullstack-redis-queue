from redisstore import RedisStore

class RedisEnqueuer(object):

  def __init__(self):
    self.redis_store = RedisStore()

  def dispatch_event(self, event):
    """
    Store event in Redis
    """
    self.redis_store.store_event(event)
  