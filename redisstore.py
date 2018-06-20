import json
import redis
import pprint
import requests

REQUEST_TIMEOUT = 10

class RedisStore(object):

  redis_key     = 'pendingEvents'
  redis_key_tmp = 'pendingEventsProcessing'

  def __init__(self):
    self.redis_connection = redis.Redis(host='localhost')

  def store_event(self, event):
    """
    Store event in Redis
    """    
    event_metadata = {
      'grouping': '{}:{}'.format(event.params.get('project_id'), event.params.get('account_id')),
      'url': event.url,
      'http_verb': event.http_verb,
      'params': event.params,
      'headers': event.headers,
    }    
    self.redis_connection.lpush(self.redis_key, json.dumps(event_metadata))

  def purge(self, redis_key):
    self.redis_connection.delete(redis_key)

  def get_all_data(self, redis_key):
    return self.redis_connection.lrange(redis_key, 0, -1)

  def copy_purge(self, from_redis_key, to_redis_key):    
    self.purge(self.redis_key_tmp)
    try:
      self.redis_connection.rename(from_redis_key, to_redis_key)
      return self.get_all_data(to_redis_key) 
    except:
      return []

  def batchedEvents(self, events):
    """
    Batches are account-project level
    Each event's `visitor` data is copied into a large batch
    These cannot be consolidated by `snapshots` because `attributes` live at the visitor level
    """
    groupings = {}
    for event in events:
        event_metadata = json.loads(event)
        if event_metadata.get('grouping') not in groupings:
            groupings[event_metadata.get('grouping')] = event_metadata
            continue
        visitor_batch = groupings[event_metadata.get('grouping')]['params']['visitors']
        event_visitor = event_metadata.get('params', {}).get('visitors')
        groupings[event_metadata.get('grouping')]['params']['visitors'] = visitor_batch + event_visitor
    return groupings

  def emitEvents(self):
    tmp_batches = self.copy_purge(self.redis_key, self.redis_key_tmp)
    batches     = self.batchedEvents(tmp_batches).values()
    for batch in batches:
        session         = requests.Session()
        request_url     = batch.get('url')
        request_headers = batch.get('headers')
        http_verb       = batch.get('http_verb', 'POST')
        request = requests.Request(
                    http_verb, 
                    request_url, 
                    json=batch.get('params'), 
                    headers=request_headers,
                  )
        prepped  = session.prepare_request(request)
        response = session.send(prepped, timeout=REQUEST_TIMEOUT)        

if __name__ == '__main__':
    rs = RedisStore()
    rs.emitEvents()


