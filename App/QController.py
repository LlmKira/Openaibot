import time
from collections import deque
from typing import Union, Optional

from graia.amnesia.message import MessageChain
from graia.ariadne import Ariadne
from graia.ariadne.connection.config import config
from graia.ariadne.message import Source
from graia.ariadne.message.element import Voice, Plain
from graia.ariadne.message.parser.twilight import UnionMatch
from graia.ariadne.model import Group, Member, Friend
from graiax import silkcoder
from loguru import logger

from App import Event
from utils import Setting
from utils.Chat import Utils
from utils.Data import create_message, User_Message

time_interval = 60
# 使用 deque 存储请求时间戳
request_timestamps = deque()


def get_user_message(
		message: MessageChain,
		member: Union[Member, Friend],
		group: Optional[Group] = None) -> User_Message:
	return create_message(
		user_id=member.id,  # qq 号
		user_name=member.name if isinstance(member, Group) else member.nickname,
		group_id=group.id if group else member.id,
		text=str(message),
		group_name=group.name if group else "Group"
	)


class BotRunner:
	def __init__(self, _config):
		self.config = _config.bot

		self.app = Ariadne(config(verify_key=_config.bot.qq.verify_key, account=_config.bot.qq.account))

	def run(self):
		bot = self.app

		@bot.broadcast.receiver("FriendMessage", dispatchers=[UnionMatch("/about", "/start", "/help")])
		async def starter(app: Ariadne, message: MessageChain, friend: Friend, source: Source):
			logger.info(message.content)
			match str(message):
				case "/about":
					await app.send_message(friend, await Event.About(self.config), quote=source)
				case "/start":
					await app.send_message(friend, await Event.Start(self.config), quote=source)
				case "/help":
					await app.send_message(friend, await Event.Help(self.config), quote=source)

		async def get_message_chain(_hand: User_Message):
			request_timestamps.append(time.time())

			if not _hand.text.startswith("/"):
				_hand.text = f"/chat {_hand.text}"
			# _friends_message = await Event.Text(_hand, self.config)
			_friends_message = await Event.Friends(_hand, self.config)

			if not _friends_message.status:
				return None

			if not _friends_message.type == "Reply":
				return MessageChain([Plain(str(_friends_message.data))])

			_type: str = _friends_message.data.get("type")
			_caption = f"{_friends_message.data.get('text')}\n{_friends_message.data.get('msg')}\n{self.config.INTRO}"

			match _type:
				case "voice":
					# 转换格式
					voice = await silkcoder.async_encode(_friends_message.data.get("voice"), audio_format="ogg")
					message_chain = MessageChain([Voice(data_bytes=voice)])
				case "text":
					message_chain = MessageChain([Plain(_caption)])
				case _:
					message_chain = MessageChain([Plain(_friends_message.msg)])

			return message_chain

		# "msg" @ RegexMatch(r"\/\b(chat|voice|write|forgetme|remind)\b.*")

		@bot.broadcast.receiver("FriendMessage")
		async def chat(app: Ariadne, msg: MessageChain, friend: Friend, source: Source):

			_hand = get_user_message(msg, member=friend, group=None)

			if friend.id in self.config.master:
				_reply = await Event.MasterCommand(Message=_hand, config=self.config)
				if _reply:
					await app.send_message(friend, "".join(_reply), quote=source)

			message_chain = await get_message_chain(_hand)
			if message_chain:
				active_msg = await app.send_message(friend, message_chain, quote=source)

				Utils.trackMsg(f"{_hand.from_chat.id}{active_msg.id}", user_id=_hand.from_user.id)

		Setting.qqbot_profile_init()
		Ariadne.launch_blocking()
