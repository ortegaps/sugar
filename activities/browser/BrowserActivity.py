import os

import gtk
import gtkmozembed
import gobject

from sugar.activity.Activity import Activity
from sugar.presence.PresenceService import PresenceService
from sugar.p2p.model.LocalModel import LocalModel
from sugar.p2p.model.RemoteModel import RemoteModel
import gecko

from NotificationBar import NotificationBar
from NavigationToolbar import NavigationToolbar
from sugar import env

class Browser(gecko.Browser):
	__gtype_name__ = "SugarBrowser"
	def __init__(self):
		gecko.Browser.__init__(self)

	def do_create_window(self):
		activity = BrowserActivity()
		activity.set_type('com.redhat.Sugar.BrowserActivity')
		return activity.get_embed()

class BrowserActivity(Activity):
	def __init__(self):
		Activity.__init__(self)

		self._share_service = None
		self._model_service = None
		self._notif_service = None
		self._model = None

		self.set_title("Web Page")
		self.connect('destroy', self._destroy_cb)

		vbox = gtk.VBox()

		nav_toolbar = NavigationToolbar()
		vbox.pack_start(nav_toolbar, False)
		nav_toolbar.show()

		self._notif_bar = NotificationBar()
		vbox.pack_start(self._notif_bar, False)
		self._notif_bar.connect('action', self.__notif_bar_action_cb)

		self._embed = Browser()
		self._embed.connect("title", self.__title_cb)
		vbox.pack_start(self._embed)		
		self._embed.show()

		nav_toolbar.set_embed(self._embed)
		self._embed.load_url('http://www.google.com')		

		self.add(vbox)
		vbox.show()

	def join(self, activity_ps):
		Activity.join(self, activity_ps)

		activity_ps.connect('service-appeared', self._service_appeared_cb)

		services = activity_ps.get_services_of_type(self._default_type)
		if len(services) > 0:
			self._notif_service = services[0]

		services = activity_ps.get_services_of_type(LocalModel.SERVICE_TYPE)
		if len(services) > 0:
			self._model_service = services[0]

		if self._notif_service and self._model_service:
			self._listen_to_model()
	
	def _service_appeared_cb(self, pservice, service):
		if service.get_type() == self._default_type:
			self._notif_service = service
		elif service.get_type() == LocalModel.SERVICE_TYPE:
			self._model_service = service
		
		if not self._model and self._notif_service and self._model_service:
			self._listen_to_model()

	def _listen_to_model(self):
		self._model = RemoteModel(self._model_service, self._notif_service)
		self._model.add_listener(self.__shared_location_changed_cb)
		self._go_to_shared_location()
	
	def _update_shared_location(self):
		address = self._embed.get_location()
		self._model.set_value('address', address)
		title = self._embed.get_title()
		self._model.set_value('title', title)
		
	def __notif_bar_action_cb(self, bar, action_id):
		if action_id == 'set_shared_location':
			self._update_shared_location()
		elif action_id == 'goto_shared_location':
			self._go_to_shared_location()

	def _go_to_shared_location(self):
		address = self._model.get_value("address")
		self._embed.load_url(address)
		self._notif_bar.hide()

	def get_embed(self):
		return self._embed
	
	def share(self):
		Activity.share(self)

		self._model = LocalModel(self, self._pservice, self._service)
		self._model.set_value('owner', self._pservice.get_owner().get_name())
		self._update_shared_location()
		
		self._notif_bar.set_text('Share this page with the group.')
		self._notif_bar.set_action('set_shared_location', 'Share')
		self._notif_bar.set_icon('stock_shared-by-me')
		self._notif_bar.show()

	def __title_cb(self, embed):
		self.set_title(embed.get_title())

	def __shared_location_changed_cb(self, model, key):
		self._notify_shared_location_change()

	def _notify_shared_location_change(self):
		owner = self._model.get_value('owner')
		title = self._model.get_value('title')
		
		text = '<b>' + owner + '</b> is reading <i>' + title + '</i>'
		self._notif_bar.set_text(text)
		self._notif_bar.set_action('goto_shared_location', 'Go There')
		self._notif_bar.set_icon('stock_right')
		self._notif_bar.show()

	def _destroy_cb(self, window):
		if self._model:
			self._model.shutdown()

def start():
	gtkmozembed.set_profile_path(env.get_profile_path(), 'gecko')
	gtkmozembed.push_startup()
	gecko.startup()
