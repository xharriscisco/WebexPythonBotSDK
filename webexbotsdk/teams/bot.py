from bottle import Bottle, request
from webexteamssdk import WebexTeamsAPI, Webhook, Message, Person, Membership
from webexteamssdk.models.cards import AdaptiveCard
from pyngrok import ngrok
from typing import Literal, overload
from re import Pattern
from tinydb import TinyDB
from tinydb.storages import JSONStorage
import tinydb_encrypted_jsonstorage as tae
from os.path import dirname, join
from logging import Logger, basicConfig, getLogger, INFO
import json

from .util import get_config_value
from .hook import WebhookEvent, WebhookResource, Hook

__all__ = ["Bot"]

class Bot():
  app: Bottle
  config: dict
  api: WebexTeamsAPI
  webhook: Webhook
  hooks: list[Hook]
  db: TinyDB
  log: Logger

  def __init__(self, config:dict = {}) -> None:
    self.app = Bottle()
    self.config = config
    self.hooks = []
    self.db = None
    self.log = None

  def table(self, name:str):
    if self.db is not None:
      return self.db.table(name)

  @overload
  def setup(self, config:str = None): pass
  @overload
  def setup(self, config:dict = None): pass
  def setup(self, config:str|dict = None, withDb = True):
    '''
### Default config
```
config = {
  "port": 8080,
  "ngrokAuthToken": "",
  "botAccessToken": "",
  "botDbKey": "ciscobotkey",
  "botName": "mywebexbot",
  "encryptDb": false
}
```
- `ngrokAuthToken` not recommended
    '''
    if isinstance(config, str):
      with open(join(dirname(__file__), 'config.json')) as f:
        config = json.loads(f.read())
        return self.setup(config)
      
    if config:
      self.config.update(config)
    botAccessToken:str|None = get_config_value(self.config, 'botAccessToken')
    ngrokAuthToken:str|Literal[False] = get_config_value(self.config, 'ngrokAuthToken', False)
    botName = get_config_value(self.config, 'botName', 'mywebexbot')
    if ngrokAuthToken and len(ngrokAuthToken) > 5:
      ngrok.set_auth_token(ngrokAuthToken)
    self.api = WebexTeamsAPI(botAccessToken)    
    # Set up logging 
    basicConfig(filename=f"{botName}.log",
      format='%(asctime)s %(message)s',
      filemode='w')
    self.log = getLogger(__name__)
    self.log.setLevel(INFO)
    print(f"Output written to {botName}.log")
    # Init db
    disaleDb = get_config_value(self.config, 'disableDb', False)
    if disaleDb:
      botDbkey = get_config_value(self.config, 'botDbKey', 's0meDefaultK3y?')
      dbPath = join(dirname(__file__), f"{get_config_value(self.config, 'botName', 'bot')}.db")
      if get_config_value(self.config, 'encryptDb', False):
        self.db = TinyDB(encryption_key=botDbkey, path=dbPath, storage=tae.EncryptedJSONStorage)
      else:
        self.db = TinyDB(path=dbPath, storage=JSONStorage)
    self.log.info('Setup complete')

  def run(self):
    port = get_config_value(self.config, 'port', 8080)
    botName = get_config_value(self.config, 'botName', 'mywebexbot')
    # Set up ngrok tunnel
    for tunnel in ngrok.get_tunnels():
      if botName in tunnel.public_url:
        ngrok.disconnect(tunnel.public_url)
    tunnel:ngrok.NgrokTunnel = ngrok.connect(port, 'http')
    public_url = tunnel.public_url.replace('http', 'https')
    # Init webex api
    for webhook in self.api.webhooks.list():
      self.api.webhooks.delete(webhookId=webhook.id)
    self.webhook = self.api.webhooks.create("bot_webhook_events", f"{public_url}/{botName}/events", WebhookResource.ALL.value, WebhookEvent.ALL.value)
    self.webhook = self.api.webhooks.create("bot_webhook_aa", f"{public_url}/{botName}/attachmentActions", WebhookResource.ATTACHMENT_ACTIONS.value, WebhookEvent.ALL.value)
    # Start server
    def callback(*args, **kwargs):
      for hook in self.hooks:
        ret = hook.matches(self.api, request.json)
        if ret is not None:
          hook.fn(ret, request.json)
    self.app.route(f'/{botName}/events', method=['GET','POST'], callback=callback)
    self.app.route(f'/{botName}/attachmentActions', method=['GET','POST'], callback=callback)
    self.app.run(host='127.0.0.1', port=port)

    # pidfile = join(getcwd(), f"{botName}.pid")
    # daemon_run(host='127.0.0.1', port=port, pidfile=pidfile)

  # HELPER

  def send_card(self, roomId:str, card:AdaptiveCard) -> Message:
    return self.api.messages.create(text='fallback', roomId=roomId, attachments=[card])

  @overload
  def mention(self, person:Person|Membership) -> str: pass 
  @overload 
  def mention(self, personId:str, displayName:str) -> str: pass 
  def mention(self, person:Person|Membership|str, displayName:str = None) -> str:
    if isinstance(person, str) and displayName:
      return f"<@personId:{person}|{displayName}>"
    else:
      id = \
        person.personEmail if 'personEmail' in person.to_dict() else\
        person.emails[0] if 'emails' in person.to_dict() else\
        person.personId if 'personId' in person.to_dict() else\
        person.id
      name = \
        person.firstName if 'firstName' in person.to_dict() else\
        person.displayName if 'displayName' in person.to_dict() else\
        person.personDisplayName
      idType = 'personEmail' if '@' in id else 'personId'
      return f"<@{idType}:{id}|{name}>"
    
  def send_help(self, source:Message) -> Message:
    help_text = (
      'Here are some commands I understand:\n'+
      '\n'.join([
        f"**{hook.name}**\n\t{hook.description}"
        for hook in self.hooks
      ])
    )
    return self.api.messages.create(roomId=source.roomId, text=help_text, markdown=help_text)

  # EVENTS

  def on(self, resource:str, event:str = None):
    return lambda fn: self.hooks.append(Hook(fn, resource, event, log=self.log))
    
  def hears(self, regex:str|list[str]|Pattern, name:str=None, description:str=None):
    return lambda fn: self.hooks.append(Hook(fn, regex=regex, name=name, description=description, log=self.log))