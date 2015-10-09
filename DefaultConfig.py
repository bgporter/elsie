



DEBUG = True
SECRET_KEY = "![d\x04R\x1c\x05\xfc+\x93\xeb\x03\x1e\x1b\xb9\x94\xfb\x8f\xb4\xb8L'=D"
#USE_X_SENDFILE = True


import socket
hostname = socket.gethostname()
if hostname == 'zappa':
   kMusicBase = '/media/usb0/music/'
   kMongoIp = '127.0.0.1'
   kMp3UtilPath = '/home/bgporter/util/mp3utilities'   

elif hostname == 'Ornette.home':
   kMusicBase = '/Volumes/zappa_files/music/'
   kMongoIp = "192.168.1.8"
   kMp3UtilPath = "/Users/bgporter/personal/utilities/mp3/mover"

else:
   print "ERROR -- Unknown music location"