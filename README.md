webex bot creation framework and tools

`pip install webexbotsdk`

###### by Xavier Harris

<br/>

##### <a id='toc'></a> webexbotsdk

- [teams](#teams)
- [util](#util)
- [tinydb](#tinydb)

<br/>

## <a id='teams'></a> `webexbotsdk.teams`

###### [#EG](#teams-eg) | [#API](#teams-api) | A framework for creating a Webex Teams bot

<br/>

### <a id='teams-eg'></a> [^](#toc) EG

---

##### configure with **config.json**

```js
{
  "botAccessToken": "", // (required) create a bot at https://developer.webex.com/my-apps
  "port": 8080, // local server port
  "botName": "", // give it a unique identifier (ex. mybot)
  "encryptDb": false, // encrypts local json db
  "botDbKey": "", // key used when 'encryptDb' is true
  "ngrokAuthToken": "", // not recommended unless using a paid tier
  "disableDb": false // disable tinydb
}
```

##### quick start

```py
from webexbotsdk.teams import Bot

bot = Bot()

@bot.hears(r'hi|hello')
def hears_hi(message, data):
  person = bot.api.people.get(message.personId)
  return bot.api.messages.create(
    roomId = message.roomId,
    text = f"Hi {person.displayName}"
  )

bot.setup('config.json')
bot.run()
```

##### with class inheritence

```python
from webexbotsdk.teams import Bot, sdk

class HiBot(Bot):
  def say_hi(self, replyTo: sdk.Message) -> sdk.Message:
    person:sdk.Person = self.api.people.get(replyTo.personId)
    return self.api.messages.create(
      roomId=replyTo.roomId,
      text=f"Hi {person.displayName}"
    )

hibot = HiBot()

@hibot.hears(r'hi|hello')
def hears_hi(message:sdk.Message, data):
  hibot.say_hi(message)

hibot.setup('config.json')
hibot.run()
```

##### [webexteamssdk](https://webexteamssdk.readthedocs.io/en/latest/) is included

```python
from webexbotsdk.teams import Bot
bot = Bot()
all_rooms = api.rooms.list()
demo_rooms = [room for room in all_rooms if 'webexteamssdk Demo' in room.title]
```

##### local DB with [TinyDB](https://tinydb.readthedocs.io/en/latest/index.html) to remember things even after the bot is restarted

```python
from webexbotsdk.teams import Bot
from webexbotsdk.tinydb import where

bot = Bot()

@bot.hears(r'remember (\d+)')
def hears_remember(message, data):
  number = int(data['groups'][0][0])
  bot.db.table('stuff').upsert(
    { 'personId':message.personId, 'number':number },
    (where('personId') == message.personId) & (where('number') == number)
  )

@bot.hears('recall')
def hears_recall(message, data):
  docs = bot.db.table('stuff').search(where('personId') == message.personId)
  bot.api.messages.create(
    roomId=message.roomId,
    text=f"I remember {', '.join([str(doc['number']) for doc in docs])}" if len(docs) > 0
    else 'No numbers stored yet'
  )

bot.setup('config.json')
bot.run()
```

##### use dataclasses to type check DB documents

```python
from webexbotsdk.teams import Bot
from webexbotsdk.tinydb import where, dataclass, BotDoc

bot = Bot()

@dataclass
class Number(BotDoc):
  personId:str
  number:int

doc_id = bot.db.table('stuff').insert(Number(personId='asdf', number=14).dict())
docs = [Number(**doc) for doc in bot.db.table('stuff').get(doc_id=doc_id)]

bot.setup('config.json')
bot.run()
```

<br/>

### <a id='teams-api'></a> [^](#toc) API

---

**class Bot**

###### props

`app` [Bottle](https://bottlepy.org/docs/dev/) local server for teams webhooks

`api` [WebexTeamsAPI](https://webexteamssdk.readthedocs.io/en/latest/) will be abbreviated as `teams` in this doc

`db` [TinyDB](https://tinydb.readthedocs.io/en/latest/index.html)

`log` python 3 [Logger](https://docs.python.org/3/library/logging.html)

###### methods

```python
setup(config:dict)
setup(path:str)
```

> configure Bot using a python dict or a filepath to a json config

```python
table(name:str) -> TinyDB.Table
```

> retrieve [tinydb table](https://tinydb.readthedocs.io/en/latest/usage.html#tables)

```python
run()
```

> start the bot local server

```python
send_card(roomId:str, card:teams.AdaptiveCard) -> teams.Message
```

> [AdaptiveCard Components](https://webexteamssdk.readthedocs.io/en/latest/user/api.html#cards-and-buttons)

```python
mention(person:teams.Person|teams.Membership) -> str
mention(personId:str, displayName:str) -> str
```

> (BROKEN) returns a formatted string for mentioning a user in a message
>
> `bot.api.message.create(text = f"hello {bot.mention(person)}")`

```python
send_help(source:teams.Message) -> teams.Message
```

> reply to a message with help text which includes
>
> - commands the bot recognizes
> - command descriptions

```python
hears(regex:str|list[str]|Pattern, name:str=None, description:str=None)
```

> @decorator, listen for user giving the bot with a command

```python
on(resource:str, event:str = None)
```

> @decorator, listen for other resource events

<br/>
<br/>

## <a id='util'></a> `webexbotsdk.util`

###### [#API](#util-api) | Framework helper methods

<br/>

### <a id='util-api'></a> [^](#toc) API

---

###### methods

```python
is_bot(person:teams.Person|teams.Membership) -> bool
```

> determine whether a person is a human or bot

<br/>
<br/>

## <a id='tinydb'></a> `webexbotsdk.tinydb`

###### [^TOC](#toc) | [@DOCS](https://tinydb.readthedocs.io/en/latest/) | TinyDB library
