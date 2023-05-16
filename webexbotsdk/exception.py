class WebexBotSdkException(Exception):
  errors:dict[str,str] = {}
  def __init__(self, messageId, *args):
    message = self.errors[messageId] if messageId in self.errors else messageId
    super().__init__(
      f"[{messageId}] {message}",
      *args
    )

class DbError(WebexBotSdkException):
  errors = {
    'disabled': 'DB is disabled. Turn of "disableDb" in config.'
  }