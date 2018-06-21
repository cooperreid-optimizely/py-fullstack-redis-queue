import requests
from optimizely import optimizely
from optimizely.logger import SimpleLogger
from redisdeferreddispatcher import RedisDeferredDispatcher

class OptimizelyConfigManager(object):
  obj = None

  def __init__(self, project_id):
    self.project_id = project_id

  def get_obj(self):
    if not self.obj:
      self.set_obj()
    return self.obj

  def set_obj(self, url=None):
    if not url:
      url = 'https://cdn.optimizely.com/json/{0}.json'.format(self.project_id)

    datafile = self.retrieve_datafile(url)
    self.obj = optimizely.Optimizely(datafile, logger=SimpleLogger(), event_dispatcher=RedisDeferredDispatcher())

  def retrieve_datafile(self, url):
    datafile = requests.get(url).text
    return datafile
