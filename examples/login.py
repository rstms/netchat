import netchat

# connect to telnet server with username and password
script = "login: haxx0r1337 password: $uper$ecret"
netchat.Session(('localhost', 23), script).run()

