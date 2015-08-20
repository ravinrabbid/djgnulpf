import subprocess
import threading
import logging
import socket
import os
import json
import time
import select
import Queue

from collections import deque
from config import *

class mpvHandler():
	def __init__(self, error_callback, title_callback):
		self.lock = threading.RLock()

		self._running = True
		self._ready = False

		self._error_callback = error_callback
		self._title_callback = title_callback

		self._queue = deque()
		self._current_item = None
		self._mpv_process = None

		self._start_watch_mpv()
		self._reader_queue = Queue.Queue()
		self._writer_queue = Queue.Queue()
		self._start_message_handler()
		self._start_reader()
		self._start_writer()

	def __del__(self):
		self._running = False
		self._stop_mpv()

	def ready_to_play(self):
		return self._ready

	def start_interrupt(self, entry):
		self.lock.acquire()
		if self._current_item != None:
			self._queue.appendleft(self._current_item)
		self._queue.appendleft(entry)
		if self._current_item != None:
			self._stop_playback()
		else:
			self._play_next()
		self.lock.release()

	def stop_playback(self):
		self.lock.acquire()
		self._queue.clear()
		self._stop_playback()
		self.lock.release()

	def enqueue(self, entry):
		self.lock.acquire()
		self._queue.append(entry)
		if self._current_item == None:
			self._play_next()
		self.lock.release()

	def skip(self):
		self.lock.acquire()
		if len(self._queue) == 0:
			r = False
		else:
			r = True
		self._stop_playback()
		self.lock.release()
		return r

	def get_queue(self):
		self.lock.acquire()
		l = list(self._queue)
		self.lock.release()
		return l

	def clear_queue(self):
		self.lock.acquire()
		self._queue.clear()
		self.lock.release()

	def _play_next(self):
		self.lock.acquire()
		if len(self._queue) > 0:
			self._current_item = self._queue.popleft()
			self._playback_url(self._current_item[0])
			self._title_callback("< retrieving url... >")
		else:
			self._current_item = None
			self._stop_playback()
			self._title_callback("< nothing >")
		self.lock.release()

	def _playback_url(self, url):
		self._send_plain_message("loadfile \""+url+"\" replace")

	def _stop_playback(self):
		# also: triggers 'end-file' event and therefore continues with playback queue
		self._send_plain_message("stop")

	# Process control
	def _start_watch_mpv(self):
		self._watch_mpv_thread = threading.Thread(target=self._watch_mpv)
		self._watch_mpv_thread.daemon = True
		self._watch_mpv_thread.start()

	def _watch_mpv(self):
		while self._running:
			self._start_mpv()
			self._mpv_process.wait()

	def _stop_mpv(self):
		if self._mpv_running():
			logging.info("Stop MPV")
			self._mpv_process.terminate()

	def _start_mpv(self):
		if not self._mpv_running():
			logging.info("Start MPV")
			self._mpv_process = subprocess.Popen([PLAY_COMMAND] + PLAY_PARAMS,
												shell=False)

	def _mpv_running(self):
		if self._mpv_process == None:
				return False
		else:
			if self._mpv_process.poll() == None:
				return True
			else:
				return False

	# Message handling
	def _send_plain_message(self, msg):
		self._writer_queue.put(msg)

	def _send_json_message(self, msg):
		msg = json.dumps(msg, separators=",:")
		msg = msg.encode("utf8", "strict")
		logging.info("sendding: " + msg)
		self._writer_queue.put(msg)

	def _start_message_handler(self):
		self._message_handler_thread = threading.Thread(target=self._message_handler)
		self._message_handler_thread.daemon = True
		self._message_handler_thread.start()

	def _message_handler(self):
		while True:
			jmsg = self._reader_queue.get()

			try:
				msg = json.loads(jmsg)
			except:
				continue

			if "error" in msg:
				self._handle_reply(msg)
			elif "event" in msg:
				self._handle_event(msg)

	def _handle_reply(self, msg):
		if msg["error"] != "success":
			logging.info("got error: " + msg["error"])
		else:
			logging.info("got reply: " + msg["data"])
			self._title_callback(msg["data"] + " (request by: " + self._current_item[1] + ")")

	def _handle_event(self, msg):
		logging.info("got event: " + msg["event"])
		if msg["event"] == "metadata-update":
			self._send_json_message({"command":["get_property","media-title"]})
		elif msg["event"] == "idle":
			self._play_next()

	# Writer
	def _start_writer(self):
		self._writer_thread = threading.Thread(target=self._writer)
		self._writer_thread.daemon = True
		self._writer_thread.start()

	def _writer(self):
		while True:
			try:
				msg = self._writer_queue.get() + b"\n"
				while msg:
					size = self._sck.send(msg)
					if size == 0:
						break
					msg = msg[size:]
			except:
				pass

	# Reader
	def _start_reader(self):
		self._reader_thread = threading.Thread(target=self._reader)
		self._reader_thread.daemon = True
		self._reader_thread.start()

	def _reader(self):
		logging.info("Trying to connect to mpv...")
		while True:
			time.sleep(0.1)
			try:
				self._sck = socket.socket(socket.AF_UNIX)
				self._sck.connect(PLAY_SOCKET)
			except:
				continue
			else:
				break

		logging.info("Connected to mpv")
		self._ready = True

		buf = b""

		while True:
			try:
				r, w, e = select.select([self._sck],[],[],1)
				if r:
					msg = self._sck.recv(1024)
					if not msg:
						break
					buf += msg
			except:
				break

			linebreak = buf.find(b"\n")
			while linebreak >= 0:
				json_msg = buf[:linebreak + 1]
				buf = buf[linebreak + 1:]

				self._reader_queue.put(json_msg)
				linebreak = buf.find(b"\n")

		self._ready = False
		logging.info("Conection to mpv lost.")
		self._start_reader()

