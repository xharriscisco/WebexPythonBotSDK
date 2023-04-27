
from bot import Bot

class HiBot(Bot):
  @Bot.hears(r'hi|hello')
  def say_hi(self, replyTo, data):
    person = self.api.people.get(replyTo.personId)
    return self.api.messages.create(
      roomId=replyTo.roomId,
      text=f"Hi {person.displayName}"
    )

hibot = HiBot()

hibot.setup('config.json')
hibot.run()