NETWORK_SERVER = "irc.hackint.eu"
NETWORK_PORT = 6667
NETWORK_PASSWORD = ""
NETWORK_NICK = "djgnulpf"
NETWORK_NICK_PASSWORD = ""
NETWORK_CHANNEL = "#djgnulpf"

PLAY_INITIAL_VOL = 75
PLAY_COMMAND = "/usr/bin/mpv"
PLAY_SOCKET = "/tmp/mpv_socket"
PLAY_PARAMS = 	[
				"--volume="+str(PLAY_INITIAL_VOL),
				"--no-video",
				"--vo=null",
				"--softvol",
				"--really-quiet",
				"--input-unix-socket="+PLAY_SOCKET,
				"--idle",
				"--no-input-default-bindings",
				"--no-terminal"
				]