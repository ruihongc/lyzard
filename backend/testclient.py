import asyncio
import websockets

async def pythonshell():
    uri = 'ws://localhost:8765'
    print('Test client starting...')
    async with websockets.connect(uri, ping_interval=None) as websocket:
        while True:
            code = input('>>> ')
            await websocket.send(code)
            actions = await websocket.recv()
            while actions[:7] == 'input: ':
                print(actions[7:], end='')
                resp = input('')
                await websocket.send(resp)
                actions = await websocket.recv()
            print(actions)

if __name__ == '__main__':
    asyncio.run(pythonshell())
