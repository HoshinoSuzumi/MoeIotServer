import json
import time
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

ACTIONS = ['get', 'set', 'ping']


def parse_request(bundle):
    try:
        result = json.loads(bundle, encoding='utf-8')
    except Exception:
        result = None
    return result


def make_response(errno, msg, data=None, str_mode=False):
    response = {
        'error': errno,
        'msg': msg,
        'data': '' if data is None else data
    }
    return str(json.dumps(response)) if str_mode else json.dumps(response)


def do_action(inst, bundle):
    action = None
    try:
        action = bundle['action']
    except Exception as e:
        inst.sendMessage(make_response(-1, 'Bad request'))
    if action is not None:
        if action not in ACTIONS:
            inst.sendMessage(make_response(-1, 'Unknown action'))
        else:
            try:
                if action == 'get':
                    inst.sendMessage(make_response(0, 'success', {
                        'type': 'temp',
                        'id:': 1,
                        'value': 21.68
                    }))
                elif action == 'set':
                    inst.sendMessage(make_response(0, 'success'))
                elif action == 'ping':
                    inst.sendMessage(make_response(0, 'pong'))
            except Exception:
                inst.sendMessage(make_response(-1, 'Missing argument'))


class CoreServer(WebSocket):

    def handleMessage(self):
        data = parse_request(self.data)
        if data is None:
            self.sendMessage(make_response(-1, 'Invalid request'))
        else:
            do_action(self, data)

    def handleConnected(self):
        print(self.address, 'connected')

    def handleClose(self):
        print(self.address, 'closed')


if __name__ == '__main__':
    print('Initializing...')
    server = SimpleWebSocketServer('0.0.0.0', 18770, CoreServer)
    time.sleep(0.5)
    print('Server is listening...')
    server.serveforever()
