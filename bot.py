import irc.bot
import logging
import time
import math

from config import *
from mpv_handler import mpvHandler

class DJBot(irc.bot.SingleServerIRCBot):
	def __init__(self, channel, nickname, identpw, server, port, password):
		logging.info('Connecting...')
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port, password)], nickname, nickname)
		logging.info('Connected!')
		self.channel = channel
		self.identpw = identpw
		self.realnick = nickname
		self.nickinuse = False

		self._title = "< nothing >"
		self._volume = PLAY_INITIAL_VOL
		self.player = mpvHandler(self.error_callback, self.title_callback)

	def on_nicknameinuse(self, c, e):
		logging.error('Nickname in use!')
		c.nick(c.get_nickname() + "_")
		self.nickinuse = True

	def on_welcome(self, c, e):
		logging.info('Identifying...')
		if self.nickinuse:
			c.privmsg("NickServ", "ghost " + self.realnick + " " + self.identpw)
			time.sleep(1)
			c.nick(self.realnick)
		c.privmsg("NickServ", "identify " + self.identpw)
		logging.info('Joining channel...')
		c.join(self.channel)

	def on_join(self, c, e):
		self._send_pub_answer(c, e, "Hi folks!")
		time.sleep(1)
		self._update_topic()

	def on_privmsg(self, c, e):
		print " == PRIVMSG From " + e.source + " to " + e.target + ": " + ', '.join(e.arguments)
		self._handle_command(c, e)
		pass

	def on_pubmsg(self, c, e):
		print " == PUBMSG From " + e.source + " on " + e.target + ": " + ', '.join(e.arguments)
		self._handle_command(c, e)
		pass

	def _handle_command(self, c, e):
		tokens = e.arguments[0].split()
		if len(tokens) == 0:
			return
		if not tokens[0].startswith('!'):
			return

		if self.player.ready_to_play():
			if tokens[0] == "!now":
				if len(tokens) < 2:
					self._send_answer(c, e, 'Usage: !now <url>')
					return
				self._handle_now(c, e, tokens[1])
			elif tokens[0] == "!skip":
				self._handle_skip(c, e)
			elif tokens[0] == "!stop":
				self._handle_stop(c, e)
			elif tokens[0] == "!queue":
				if len(tokens) < 2:
					self._send_answer(c, e, 'Usage: !queue <url>')
					return
				self._handle_queue(c, e, tokens[1])
			elif tokens[0] == "!list":
				self._handle_list(c, e)
			elif tokens[0] == "!clear":
				self._handle_clear(c, e)
			elif tokens[0] == "!vol":
				if len(tokens) < 2:
					self._send_answer(c, e, 'Usage: !vol [0-100]')
					return
				self._handle_vol(c, e, tokens[1])
			elif tokens[0] == "!help":
				self._handle_help(c, e)
			else:
				self._send_answer(c, e, 'Unkown command, use !help for help.')
		else:
			self._send_answer(c, e, "Chill, I'm not ready right now!")

	def _handle_now(self, c, e, url):
		url = self._style_url(url)

		self._send_pub_answer(c, e, "Coming right now " + e.source.nick + "!")
		self.player.start_interrupt((url, e.source.nick))

	def _handle_skip(self, c, e):
		if self.player.skip():
			self._send_pub_answer(c, e, e.source.nick + " skipped to the next item")
		else:
			self._send_pub_answer(c, e, "Queue is empty")

	def _handle_stop(self, c, e):
		self.player.stop_playback()
		self._send_pub_answer(c, e, "Playback stopped by " + e.source.nick)

	def _handle_queue(self, c, e, url):
		url = self._style_url(url)

		self._send_pub_answer(c, e, e.source.nick + " enqueued " + url)
		self.player.enqueue((url, e.source.nick))

	def _handle_list(self, c, e):
		queue = self.player.get_queue()

		self._send_priv_answer(c, e, "Coming up:")

		if len(queue) == 0:
			self._send_priv_answer(c, e, "<empty>")
		else:
			for i in range(len(queue)):
				entry = queue[i]
				self._send_priv_answer(c, e, str(i) + ": " + entry[0] + " by " + entry[1])

	def _handle_vol(self, c, e, vol):
		try:
			v = int(vol)
		except:
			self._send_answer(c, e, "Give me a natural number!")
			return

		if v < 0:
			self._send_answer(c, e, "What?!")
			return
		elif v > 100:
			self._send_answer(c, e, "\'You crazy?")
		else:
			self.volume_callback(v)
			self.player.set_volume(v)

	def _handle_clear(self, c, e):
		self.player.clear_queue()
		self._send_pub_answer(c, e, e.source.nick + " cleared the queue!")

	def _handle_help(self, c, e):
		self._send_priv_answer(c, e, "Commands:")
		self._send_priv_answer(c, e, "!now <url>: Plays the url right now, continues with the last played queue item afterwards.")
		self._send_priv_answer(c, e, "!queue <url>: Inserts the url at the end of the playback queue.")
		self._send_priv_answer(c, e, "!skip: Skips to the next item in the playback queue.")
		self._send_priv_answer(c, e, "!stop: Stops playback and clears queue.")
		self._send_priv_answer(c, e, "!clear: Clears the current playback queue.")
		self._send_priv_answer(c, e, "!list: List the content of the current playback queue.")
		self._send_priv_answer(c, e, "!vol [1-100]: Sets the volume.")
		self._send_priv_answer(c, e, "!help: Duh!")
		self._send_priv_answer(c, e, " ")
		self._send_priv_answer(c, e, "<url> can be a direct link to most media file formats or some url youtube-dl supports.")

	def _send_answer(self, c, e, msg):
		if e.type == "pubmsg":
			self._send_pub_answer(c, e, msg)
		elif e.type == "privmsg":
			self._send_priv_answer(c, e, msg)

	def _send_priv_answer(self, c, e, msg):
		c.privmsg(e.source.nick, msg)

	def _send_pub_answer(self, c, e, msg):
		c.privmsg(self.channel, msg)

	def _set_topic(self, msg):
		self.connection.topic(self.channel, msg)

	def _style_url(self, url):
		if not url.startswith('http://') and not url.startswith('https://'):
			url = 'http://' + url
		return url

	def _update_topic(self):
		self._set_topic("[Vol: "+str(self._volume)+"] Now playing: \"" + self._title + " \"")

	def error_callback(self):
		self._send_pub_answer(self.connection, None, "Playback failed!")

	def title_callback(self, title):
		self._title = title
		self._update_topic()

	def volume_callback(self, vol):
		if vol != None:
			v = int(math.floor(vol))
			if v != self._volume:
				self._volume = v
				self._update_topic()
