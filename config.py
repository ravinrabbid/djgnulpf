NETWORK_SERVER = "irc.hackint.eu"
NETWORK_PORT = 6667
NETWORK_PASSWORD = ""
NETWORK_NICK = "djgnulpf"
NETWORK_NICK_PASSWORD = ""
NETWORK_CHANNEL = "#djgnulpf"

PLAY_COMMAND = "/usr/bin/mpv"
PLAY_SOCKET = "/tmp/mpv_socket"
PLAY_PARAMS = 	[
				"--vo=null",
				"--really-quiet",
				"--input-unix-socket="+PLAY_SOCKET,
				"--idle",
				"--no-input-default-bindings",
				"--no-terminal"
				]