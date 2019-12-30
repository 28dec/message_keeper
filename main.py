from fbchat import Client, ThreadType, Message, VideoAttachment, ImageAttachment
from termcolor import colored
from getpass import getpass
import colorama
import asyncio
import sentry_sdk
import os
import pickle
import requests
import codecs  # https://stackoverflow.com/questions/30469575/how-to-pickle-and-unpickle-to-portable-string-in-python-3
import DB

colorama.init()
sentry_sdk.init("https://ddc9dbf023ba4e30b241b74ad7b7efcb@sentry.io/1520935")
db = DB.DB()
client = None


class Keeper(Client):

	async def load_user_name_by_id(self, uid):
		user_name = db.loda('ids', uid)
		if user_name is None:
			user_name = uid
			await_users = await self.fetch_user_info(uid)
			users = list(await_users.values())
			for user in users:
				user_name = user.name
				db.seva('ids', user.id, user.name)
		return user_name

	async def load_group_name_by_id(self, gid):
		group_name = db.loda('ids', gid)
		if group_name is None:
			group_name = gid
			await_groups = await self.fetch_group_info(gid)
			groups = list(await_groups.values())
			for group in groups:
				group_name = group.name + \
					" - {} participants".format(len(group.participants))
		return group_name

	async def on_message(self, mid=None, author_id=None, message_object=None, thread_id=None, thread_type=None, at=None, metadata=None, msg=None):
		print(colored("Received new message", 'green'))
		print(message_object)
		key = message_object.uid.replace('.$', '_')
		value = codecs.encode(pickle.dumps(message_object), 'base64').decode()
		# print("Saving...\nkey -> [{}]\nvalue -> [{}]".format(key, value))
		db.seva('messages2', key, value)
		if author_id == self.uid and message_object.text == "#off":
			if loop.stop():
				print(colored('SAFETY LOGOUT RETURNED NON-ZERO', 'white', 'on_blue'))
			else:
				print(colored('SAFETY LOGOUT RETURNED ZERO', 'white', 'on_green'))

	async def on_message_unsent(self, mid=None, author_id=None, thread_id=None, thread_type=None, at=None, msg=None):
		print(colored("{} removed a message on {} {}".format(
			author_id, thread_type, thread_id), 'magenta'))
		# print("id -> {}".format(mid))
		pickled = db.loda('messages2', mid.replace('.$', '_'))
		removed_msg = pickle.loads(codecs.decode(pickled.encode(), 'base64'))
		print(removed_msg)
		# fetch attachments
		media_urls = []
		other_attachment_urls = ""
		if removed_msg.attachments:
			for item in removed_msg.attachments:
				if(isinstance(item, (VideoAttachment, ImageAttachment, ))):
					url = await self.fetch_image_url(item.uid)
					media_urls.append(url)
				else:
					other_attachment_urls += item.url + "\n"
		print(colored("fetch attachment done!", 'green'))
		user_name = await self.load_user_name_by_id(author_id)
		print("username -> [{}]".format(user_name))
		if thread_type == ThreadType.GROUP:
			thread_name = await self.load_group_name_by_id(thread_id)
		else:
			thread_name = 'INBOX'
		print("thread_name -> [{}]".format(thread_name))
		msg = "{} removed a message in [{}]\n".format(user_name, thread_name)
		replied_to = "\n* -> [{}]".format(removed_msg.text)
		if removed_msg.attachments:
			replied_to += " {} attachment(s)".format(len(removed_msg.attachments))
		if removed_msg.replied_to:
			replied_to += "\nreplied to {} -> [{}]".format(await self.load_user_name_by_id(removed_msg.replied_to.author), removed_msg.replied_to.text)
			if len(removed_msg.replied_to.attachments):
				replied_to += " {} attachments".format(
					len(removed_msg.replied_to.attachments))
		msg += replied_to
		await self.send(Message(text=msg, sticker=removed_msg.sticker), thread_id=self.uid)
		await self.send_remote_files(media_urls, other_attachment_urls, self.uid)


def custom_exception_handler(loop, context):
	loop.default_exception_handler(context)
	exception = context.get('exception')
	print(context)
	loop.stop()


loop = asyncio.get_event_loop()


async def start():
	global client
	client = Keeper(loop=loop)
	print("Logging in...")
	session = None
	if os.path.isfile('session'):
		with open('session', 'rb') as f:
			session = pickle.load(f)
	await client.start(input("facebook username: "), getpass("facebook password: "), session)
	with open('session', 'wb') as f:
		pickle.dump(client.get_session(), f)
	print("Hello, i'm MessageKeeper, i'm listening...")
	client.listen()

loop.set_exception_handler(custom_exception_handler)
loop.run_until_complete(start())
loop.run_forever()
