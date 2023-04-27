from enum import Enum
from typing import Callable
from bottle import request
from webexteamssdk import WebexTeamsAPI, Message, Person, AttachmentAction, ApiError
from re import Pattern, search, match
from logging import Logger, getLogger, INFO

from .util import is_bot

__all__ = []

class WebhookEvent(Enum):
   ALL = 'all'
   CREATED = 'created'
   UPDATED = 'updated'
   DELETED = 'deleted'

class WebhookResource(Enum):
   ALL = 'all'
   MEMBERSHIPS = 'memberships'
   ROOMS = 'rooms'
   ATTACHMENT_ACTIONS = 'attachmentActions'

class Hook():
  fn:Callable
  resource:str
  event:str
  regex:list[Pattern]
  name:str
  description:str
  log:Logger

  def __init__(self, fn:Callable, resource:str = None, event:str = None, regex:str|list[str] = None, name:str = None, description:str = '', log:Logger = None) -> None:
    self.fn = fn 
    self.resource = resource
    self.event = event
    regex = [regex] if not isinstance(regex, list) else regex
    self.regex = [compile(re) for re in regex if re is not None] # list[str|Pattern] -> list[Pattern]
    self.name = name or '/'.join([re.pattern for re in self.regex])
    self.description = description
    self.log = log or getLogger()

  def matches(self, api:WebexTeamsAPI, data:dict = None):
    resource = data['resource'] if 'resource' in data else ''
    event = data['event'] if 'event' in data else ''
    extra = {}
    # card interaction
    if self.resource == resource:
      if resource == 'attachmentActions':
        self.log.info(f"hook {self.name}: attachmentActions")
        action:AttachmentAction = api.attachment_actions.get(data['data']['id'])
        return action, extra
    # hears message
    if resource == 'messages':
      try:
        message:Message = api.messages.get(data['data']['id'])
        person:Person = api.people.get(message.personId)
        if not is_bot(person) and any([not reg is None and search(reg, message.text) for reg in self.regex]):
          self.log.info(f"hook {self.name}: message '{message.text}' matches")
          extra = { 'groups': [] }
          for reg in self.regex:
            res = match(reg, message.text)
            if res:
              extra['groups'].append(res.groups())
          return message, extra
      except ApiError as e:
        return None, None
    # other
    if self.resource is not None and resource == self.resource and (self.event is None or self.event == event):
      self.log.info(f"hook {self.name}: resource={resource} event={event}")
      return request.json['data'], extra
    return None, None