import firebase_admin
import json

from firebase_admin import credentials
from firebase_admin import db


class DB(object):
	def __init__(self):
		super(DB, self).__init__()
		cred = credentials.Certificate('creds_m_p_r.json')
		firebase_admin.initialize_app(cred, {
			'databaseURL': 'https://messenger-prevent-remove.firebaseio.com'
		})
		self.db = db

	def save(self, msg_id, msg_object):
		msg_id = msg_id.replace('.$', '_')
		msg = {}
		msg['text'] = msg_object.text
		msg['attachments'] = []
		if msg_object.attachments:
			for attachment in msg_object.attachments:
				msg['attachments'].append(attachment)
		msg_object = json.dumps(msg_object.__dict__)
		ref = self.db.reference('/messages/'+msg_id)
		ref.set(msg_object)

	def seva(self, collection, key, value):
		self.db.reference('/' + collection + '/' + key).set(value)

	def loda(self, collection, key):
		ref = self.db.reference('/' + collection + '/' + key).get()
		return ref

	def load(self, msg_id):
		msg_id = msg_id.replace('.$', '_')
		ref = self.db.reference('/messages/'+msg_id).get()
		return ref

	def save_id(self, id, value):
		ref = self.db.reference('/ids/'+id)
		ref.set(value)

	def load_id(self, id):
		ref = self.db.reference('/ids/'+id).get()
		return ref

	def load_all_id(self):
		ref = self.db.reference('/ids/').get()
		return ref
