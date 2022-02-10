from bottle import route, run, static_file
from threading import Thread
from backend.wsserver import checkConnection, start, wsstop, wsshutdown
from backend.icon import icn
import webbrowser
from time import sleep
import sys
import os

@route('/')
def index():
    if checkConnection():
        return 'Lyzard is already opened in another tab.'
    return open('./ui/index.html', 'rb').read()
    #return html

@route('/<url:path>')
def files(url):
    if url == 'reset':
        wsstop()
        return 'Finished'
    #elif url == 'main.js':
    #    return js
    elif url == 'index.html':
        if checkConnection():
            return 'Lyzard is already opened in another tab.'
        return open('./ui/index.html', 'rb').read()
        #return html
    try:
        f = static_file(url, root='./ui/')
    except:
        f = 'Not Found'
    return f

def runserver():
    global ws
    ws = Thread(target = start)
    ws.start()
    #f = open(os.devnull, 'w')
    #sys.stdin = f
    #sys.stdout = f
    #sys.stderr = f
    bt = Thread(target = httpserve)
    bt.start()
    sleep(1)
    if (ws.is_alive()) and (bt.is_alive()):
        print('Go to http://127.0.0.1:8080 in your browser to open the app.')
        print('Do not use the app from more than one tab.')
        print(icn)
        webbrowser.open('http://127.0.0.1:8080', new=2)

def httpserve():
    try:
        run(host='localhost', port=8080, quiet=True)
    except OSError:
        os.system('cls' if os.name == 'nt' else "printf '\033c'")
        print('Error: Lyzard is already opened or is unavailable.')

def stopthread():
    wsshutdown()
    global ws
    ws.join()

if __name__ == "__main__":
    import signal
    def keyboardInterruptHandler(signal, frame):
        print("KeyboardInterrupt (ID: {}) has been caught. Shutting down server...".format(signal))
        stopthread()
        exit(0)
    signal.signal(signal.SIGINT, keyboardInterruptHandler)
    runserver()
