import signal
import sys
import logging

from config import *
from bot import DJBot

bot = None

def main():
	logging.basicConfig(level=logging.INFO)

	global bot
	bot = DJBot(NETWORK_CHANNEL,
				NETWORK_NICK,
				NETWORK_NICK_PASSWORD,
				NETWORK_SERVER,
				NETWORK_PORT,
				NETWORK_PASSWORD)

	signal.signal(signal.SIGINT, signal_handler)

	bot.start()


def signal_handler(signal, frame):
	print('Wohoo, seeya!\n')
	bot.die()
	sys.exit(0)

if __name__ == "__main__":
	main()