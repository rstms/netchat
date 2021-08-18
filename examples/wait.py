import netchat

# connect and wait for the string 'AAA'
netchat.Session(('localhost', 2000), 'AAA').run()
