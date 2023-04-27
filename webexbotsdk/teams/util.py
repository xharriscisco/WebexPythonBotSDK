from webexteamssdk import Person, Membership

__all__ = ["is_bot"]

def get_config_value(config:dict, key:str, default=None):
  if default is None and not key in config:
    raise Exception(f'{key} not found in config')
  return config[key] if key in config else default

def is_bot(person:Person|Membership):
  emails:list[str] = person.emails if isinstance(person, Person) else [person.personEmail]
  return any([email.endswith('webex.bot') for email in emails])
