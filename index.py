from backend.server import runserver, stopthread
import sys
import os

if __name__ == "__main__":
    print('Loading...', end='\r')
    if getattr(sys, 'frozen', False):
        application_path = os.path.realpath(os.path.expanduser(sys._MEIPASS))
    else:
        application_path = os.path.dirname(os.path.realpath(os.path.expanduser(__file__)))
    os.chdir(application_path)
    #import signal
    #def keyboardInterruptHandler(signal, frame):
    #    print("KeyboardInterrupt (ID: {}) has been caught. Shutting down server...".format(signal))
    #    stopthread()
    #    exit(0)
    #signal.signal(signal.SIGINT, keyboardInterruptHandler)
    try:
        runserver()
    except SystemExit:
        raise