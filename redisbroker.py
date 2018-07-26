import json
import redis
import pprint
import requests

REQUEST_TIMEOUT     = 10
CONNECTION_SETTINGS = {'host': 'localhost'}

class RedisBroker(object):

  redis_key     = 'pendingEvents'
  redis_key_tmp = 'pendingEventsProcessing'

  def __init__(self):
    self.redis_connection = redis.Redis(**CONNECTION_SETTINGS)

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
    Batches are grouped at the project level
    
    Explanation:
    - The `visitor` data from an individual event payload is copied/appended to the `visitors` Array sent within the batch payload
    - The events cannot be consolidated by `snapshots` because `attributes` live at the visitor level. If for some reason a visitor 
      had different attributes for two events within the same decision, it would be problematic to send only multiple `snapshots` 
      because visitor attributes live immediately under the `visitor` object which is a level above snapshots.
    """
    groupings = {}
    for event in events:
        event_metadata = json.loads(event)
        if event_metadata.get('grouping') not in groupings:
            groupings[event_metadata.get('grouping')] = event_metadata
        else:
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
    return batches     

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Emit events enqueued in Redis')
  parser.add_argument('--emit', '-emit', dest='emit', help='Emit all redis-enqueued events to Optimizely events endpoint, and then flush them from redis.', action='store_true', required=True)
  args = parser.parse_args()  
  # emit enqueued events
  if args.emit:
    rs = RedisBroker()
    sent_batches = rs.emitEvents()
    # count total events dispatched
    total_events = 0
    for batch in sent_batches:
      total_events = total_events + len(batch.get('params', {}).get('visitors', []))      
    print("Dispatched {} events.".format(total_events))


