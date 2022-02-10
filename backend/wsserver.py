import asyncio
import os
from subprocess import run
import websockets
import sys
from tokenize import generate_tokens, untokenize
from code import InteractiveInterpreter
from io import StringIO, TextIOBase
from nest_asyncio import apply
from threading import Event
import websockets.legacy.server

class WSO(TextIOBase):
    def write(self, s):
        output.append(s)
        return len(s)

class WSI(TextIOBase):
    def readable(self):
        return True
    async def _receiver(self):
        try:
            ret = await websocket.recv()
            return ret
        except websockets.exceptions.ConnectionClosed:
            wsstop()
            return ''
    async def _write(self, s):
        try:
            await websocket.send(f'input: {s}')
        except websockets.exceptions.ConnectionClosed:
            wsstop()
    def read(self, s = None):
        loop.run_until_complete(self._write(output[-1]))
        output.pop()
        resp = loop.run_until_complete(self._receiver())
        return resp
    def readline(self, s = None):
        loop.run_until_complete(self._write(output[-1]))
        output.pop()
        resp = loop.run_until_complete(self._receiver())
        return resp

def tokener(code):
    return list(generate_tokens(StringIO(code).readline))

def stripFront(code, n):
    cur = n
    while cur < len(code) and ((code[cur] == ' ') or (code[cur] == '\t')):
        cur += 1
    return code[cur:]

def stripColon(code):
    cur = len(code) - 1
    while cur >= 0 and code[cur] != ':':
        cur -= 1
    return code[:cur]

def hook(out):
    global out2
    out2 = out

def countIndent(code):
    if code == '':
        return -1
    i = 0
    while code[i] == ' ':
        i += 1
        if i == len(code):
            return -1
    if code[i] == '#':
        return -1
    return i

def getArgs(tokens, k):
    tmp = 1
    tmp2 = 0
    tmp3 = 0
    tmpls = []
    j = k
    while tmp and (j < len(tokens)):
        if (tokens[j].string == ',') and (tmp2 == 0) and (tmp3 == 0) and (tmp == 1):
            tmpls.append(stripFront(untokenize(tokens[k:j]), 0))
            k = j + 1
        elif tokens[j].string == '(':
            tmp += 1
        elif tokens[j].string == ')':
            tmp -= 1
        elif tokens[j].string == '[':
            tmp2 += 1
        elif tokens[j].string == ']':
            tmp2 -= 1
        elif tokens[j].string == '{':
            tmp3 += 1
        elif tokens[j].string == '}':
            tmp3 -= 1
        j += 1
    if (tokens[k:j-1] != []):
        tmpls.append(stripFront(untokenize(tokens[k:j-1]), 0))
    return (tmpls, j)

def getSubsR(tokens, k):
    tmp = 0
    tmp2 = 1
    tmp3 = 0
    tmpls = []
    j = k
    while tmp2 and (j >= 0):
        if (tokens[j].string == ',') and (tmp2 == 1) and (tmp3 == 0) and (tmp == 0):
            tmpls.append(stripFront(untokenize(tokens[j+1:k+1]), 0))
            k = j - 1
        elif tokens[j].string == '(':
            tmp -= 1
        elif tokens[j].string == ')':
            tmp += 1
        elif tokens[j].string == '[':
            tmp2 -= 1
        elif tokens[j].string == ']':
            tmp2 += 1
        elif tokens[j].string == '{':
            tmp3 -= 1
        elif tokens[j].string == '}':
            tmp3 += 1
        j -= 1
    if (tokens[j+2:k+1] != []):
        tmpls.append(stripFront(untokenize(tokens[j+2:k+1]), 0))
    return (tmpls[::-1], j)

def functionCalls(tokens):
    i = 0
    global vars
    while i < len(tokens):
        if tokens[i].string in vars.functions:
            k = i
            while tokens[k].string != '(':
                k += 1
            k += 1
            (tmpls, j) = getArgs(tokens, k)
            vars.argvs.extend(tmpls)
            vars.callv.append((i, j))
            vars.called = True
            return tokens[i].string
        else:
            i += 1
    return False

def runCodeSafely(code):
    try:
        return env.runsource(code)
    except Exception as e:
        print(e)
        return False

def checkAssignment(tokens):
    assOps = set(('=', '+=', '-=', '*=', '/=', '//=', '%=', '**=', '&=', '|=', '^=', '<<=', '>>='))
    ret = []
    brackets = 0
    i = len(tokens) - 1
    while (tokens[i].string not in assOps) or (brackets != 0):
        if tokens[i].string == ')':
            brackets += 1
        elif tokens[i].string == '(':
            brackets -= 1
        if i == 0:
            return []
        i -= 1
    while i > 0:
        i -= 1
        if tokens[i].type == 1:
            tmp = runCodeSafely(tokens[i].string)
            tmp2 = out2
            ret.append((tokens[i].string, tmp2))
        elif tokens[i].string == ']':
            i, nm = getName(tokens, i)
            tmp = runCodeSafely(nm)
            tmp2 = out2
            ret.append((nm, tmp2))
    return ret

def getName(tokens, i):
    i, subslist = getNameList(tokens, i)
    return (i, mergeName(subslist))

def mergeName(subslist):
    ret = subslist[0]
    for j in subslist[1:]:
        if isinstance(j, list):
            ret += '['+", ".join(j)+']'
        elif j != '':
            tmp = runCodeSafely(j)
            tmp3 = out2
            ret += f'[{tmp3}]'
        else:
            ret += f'[]'
    return ret

def getNameList(tokens, i):
    if i < 0:
        return ''
    subslist = []
    while tokens[i].string == ']':
        (tmpls, i) = getSubsR(tokens, i-1)
        if len(tmpls) == 1:
            subslist.insert(0, tmpls[0])
        elif len(tmpls) > 1:
            subslist.insert(0, tmpls)
        else:
            subslist.insert(0, '')
        if i < 0:
            return (i, ['']+subslist)
    if subslist == []:
        return (i, [tokens[i].string])
    if tokens[i].type == 1:
        return (i, [tokens[i].string] + subslist)
    return (i, [''] + subslist)

def checkList(tokens):
    ret = []
    i = len(tokens) - 1
    while i > 0:
        if tokens[i].string == 'append':
            i -= 2
            i, nm = getName(tokens, i)
            tmp = runCodeSafely(f'len({nm})')
            tmp2 = out2
            tmp = runCodeSafely(f'{nm}[{tmp2-1}]')
            tmp3 = out2 
            ret.append((f'{nm}[{tmp2-1}]', f'(INS){tmp3}'))
        elif tokens[i].string == 'clear':
            i -= 2
            i, nm = getName(tokens, i)
            ret.append((f'{nm}', '(CLR)'))
        elif tokens[i].string == 'insert':
            (tmpls, j) = getArgs(tokens, i+2)
            tmp = runCodeSafely(stripFront(f'{tmpls[0]}', 0))
            tmp2 = out2
            i -= 2
            i, nm = getName(tokens, i)
            tmp = runCodeSafely(f'{nm}[{tmp2}]')
            tmp3 = out2 
            ret.append((f'{nm}[{tmp2}]', f'(INS){tmp3}'))
        elif tokens[i].string == 'pop':
            (tmpls, j) = getArgs(tokens, i+2)
            i -= 2
            i, nm = getName(tokens, i)
            if tmpls != []:
                tmp = runCodeSafely(stripFront(f'{tmpls[0]}', 0))
                tmp2 = out2
            else:
                tmp = runCodeSafely(f'len({nm})')
                tmp2 = out2
            ret.append((f'{nm}[{tmp2}]', '(DEL)'))
        i -= 1
    return ret

def checkTuple(tupleList, x):
    for i in tupleList:
        if x == i[0]:
            return False
    return True

def checkUse(tokens, ignore):
    ret = []
    i = len(tokens) - 1
    while i > 0:
        if tokens[i].string == 'index':
            (tmpls, j) = getArgs(tokens, i+2)
            i -= 2
            i, nm = getNameList(tokens, i)
            for nmk in nm:
                if isinstance(nmk, list):
                    for nmkk in nmk:
                        ret.extend(checkUse(tokener(nmkk), ignore))
                elif nmk != '':
                    ret.extend(checkUse(tokener(nmk), ignore))
            if nm[0] != '':
                nm = mergeName(nm)
                tmp = runCodeSafely(f'{nm}.index({tmpls[0]})')
                tmp2 = out2
                ret.append(f'{nm}[{tmp2}]')
        elif tokens[i].string == ']':
            i, nm = getNameList(tokens, i)
            for nmk in nm:
                if isinstance(nmk, list):
                    for nmkk in nmk:
                        ret.extend(checkUse(tokener(nmkk), ignore))
                elif nmk != '':
                    ret.extend(checkUse(tokener(nmk), ignore))
            if nm[0] != '':
                nm = mergeName(nm)
                if checkTuple(ignore, nm):
                    ret.append(nm)
        elif (tokens[i].type == 1) and checkTuple(ignore, tokens[i].string):
            ret.append(tokens[i].string)
        i -= 1
    return ret

def runner(code):
    jump = -1
    ict = 0
    list1 = []
    list2 = []
    global output, vars, out2
    output.clear()
    out2 = None
    tmp = countIndent(code)
    #detect deindent
    if tmp != -1:
        if code == '<===7':
            tmp = 0
        tokens = tokener(code[tmp:])
        if vars.rflag == True:
            vars.rflag = False
            code = untokenize(tokens[:vars.callv[-1][0]]) + str(vars.rvalue) + untokenize(tokens[vars.callv[-1][1]:])
            vars.callv.pop()
            tokens = tokener(code)
        if tmp <= vars.lazy:
            vars.lazy = -1
        global ctx
        if (vars.lazy == -1) and (tmp < ctx[-1].level):
            #go to jump location
            ict = 1
            ctx[-1].dedent = vars.idincrement + ict
            if (ctx[-1].stacktrace != []) and (ctx[-1].stacktrace[-1][0] >= tmp):
                jump = ctx[-1].stacktrace[-1][1]
            while ctx[-1].ifflag and (ctx[-1].ifflag[-1] > tmp):
                ctx[-1].ifflag.pop()
                
            if (jump == -1) and (vars.callindent[-1] >= tmp):
                jump = vars.callstack[-1]
                vars.callindent.pop()
                ctx.pop()
                vars.callstack.pop()
                vars.rflag = True
                #tmp = runCodeSafely(stripFront(code, 6))
                vars.rvalue = None
        ctx[-1].level = tmp
        code = code[tmp:] #remove indentations

        #if no jump
        if jump == -1:
            if code == '<===7':
                return 'Finished'

            if vars.lazy == -1:
                sys.stdin = WSI()
                sys.stdout = WSO()
                sys.stderr = sys.stdout
                fname = False
                if (tokens[0].string != 'def') and (tokens[0].string != 'class'):
                    fname = functionCalls(tokens)
                if (fname != False):
                    ict = 1
                    vars.callstack.append(vars.idincrement + ict)
                    vars.callindent.append(ctx[-1].level)
                    ctx.append(Context())
                    jump = vars.functions[fname]
                else:
                    if tokens[0].string == 'return':
                        jump = vars.callstack[-1]
                        vars.callindent.pop()
                        ctx.pop()
                        vars.callstack.pop()
                        vars.rflag = True
                        tmp = runCodeSafely(stripFront(code, 6))
                        vars.rvalue = out2
                        #return value
                    elif tokens[0].string == 'pass':
                        pass #may need to fix next time
                    elif tokens[0].string == 'continue':
                        jump = ctx[-1].stacktrace[-1][1]
                    elif tokens[0].string == 'elif':
                        if ctx[-1].ifflag and (ctx[-1].ifflag[-1] == ctx[-1].level):
                            vars.lazy = ctx[-1].level
                        else:
                            tmp = runCodeSafely(stripColon(stripFront(code, 4)))
                            if out2:
                                ctx[-1].ifflag.append(ctx[-1].level)
                            else:
                                vars.lazy = ctx[-1].level
                    elif tokens[0].string == 'else':
                        if ctx[-1].ifflag and (ctx[-1].ifflag[-1] == ctx[-1].level):
                            vars.lazy = ctx[-1].level
                    elif runCodeSafely(code) == True:
                        if (tokens[0].string == 'def') or (tokens[0].string == 'class'):
                            if vars.called:
                                curArg = 0
                                while (curArg < len(vars.argvs)) and (tokens[curArg*2+2].string != ')') and (tokens[curArg*2+3].string != ')'):
                                    tmp = runCodeSafely(f'{tokens[curArg*2+3].string} = {vars.argvs[curArg]}')
                                    tmp = runCodeSafely(vars.argvs[curArg])
                                    tmp3 = out2
                                    list1.append((tokens[curArg*2+3].string, tmp3))
                                    list2.extend(checkUse(tokener(vars.argvs[curArg]), [tokens[curArg*2+3].string]))
                                    curArg += 1
                                #set each arg to their value
                                vars.called = False
                                vars.argvs.clear()
                            else:
                                vars.lazy = ctx[-1].level
                                ict = 1
                                vars.functions[tokens[1].string] = vars.idincrement + ict
                        elif tokens[0].string == 'for':
                            if (ctx[-1].stacktrace == []) or (ctx[-1].stacktrace[-1][0] != ctx[-1].level):
                                #first time entering
                                ict = 1
                                ctx[-1].stacktrace.append((ctx[-1].level, vars.idincrement + ict))
                                tmp = stripColon(stripFront(code, 3))
                                tmp = stripFront(tmp, len(tokens[1].string))
                                tmp = stripFront(tmp, 2)
                                tmp = runCodeSafely(tmp)
                                vars.forstack.append(list(out2))
                                vars.fornames.append(tokens[1].string)
                            if vars.forstack[-1] == []:
                                jump = ctx[-1].dedent
                                ctx[-1].stacktrace.pop()
                                vars.fornames.pop()
                                vars.forstack.pop()
                            else:
                                tmp = runCodeSafely(f'{vars.fornames[-1]} = {vars.forstack[-1][0]}')
                                list1.append((vars.fornames[-1], vars.forstack[-1][0]))
                                vars.forstack[-1].pop(0)
                        elif tokens[0].string == 'while':
                            if (ctx[-1].stacktrace == []) or (ctx[-1].stacktrace[-1][0] != ctx[-1].level):
                                ict = 1
                                ctx[-1].stacktrace.append((ctx[-1].level, vars.idincrement + ict))
                            tmp = runCodeSafely(stripColon(stripFront(code, 5)))
                            if not out2:
                                jump = ctx[-1].dedent
                                ctx[-1].stacktrace.pop()
                        elif tokens[0].string == 'if':
                            if ctx[-1].ifflag and (ctx[-1].ifflag[-1] == ctx[-1].level):
                                ctx[-1].ifflag.pop()
                            tmp = runCodeSafely(stripColon(stripFront(code, 2)))
                            if out2:
                                ctx[-1].ifflag.append(ctx[-1].level)
                            else:
                                vars.lazy = ctx[-1].level
                    list1.extend(checkAssignment(tokens))
                    list1.extend(checkList(tokens))
                    list2.extend(checkUse(tokens, list1))
                    #check for list assignment
                sys.stdin = sys.__stdin__
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
                #f = open(os.devnull, 'w')
                #sys.stdin = f
                #sys.stdout = f
                #sys.stderr = f
                    
    vars.idincrement += ict
    actions = ''.join(output)
    actions += '------\n'
    if vars.lazy == -1:
        for i in list1:
            actions += f'{i[0]} {i[1]}, '
    actions += '\n'
    if vars.lazy == -1:
        for i in list2:
            actions += f'{i} '
    if ict:
        actions += '\n' + str(vars.idincrement)
    else:
        actions += '\n-1'
    actions += '\n' + str(jump)
    return actions

async def receiver(wsk, path):
    global websocket, repeat, Connected
    websocket = wsk
    Connected = True
    while repeat:
        resp = ''
        try:
            code = await websocket.recv()
        except websockets.exceptions.ConnectionClosed:
            wsstop()
            break
        resp = runner(code)
        try:
            await websocket.send(resp)
        except websockets.exceptions.ConnectionClosed:
            wsstop()
            break
        if resp == 'Finished':
            wsstop()
    Connected = False

def checkConnection():
    return Connected

async def main():
    #print("Serving WebSocket at port 8765...")
    try:
        async with websockets.serve(receiver, "localhost", 8765, ping_interval=None):
            await stop
    except OSError:
        os.system('cls' if os.name == 'nt' else "printf '\033c'")
        print('Error: Lyzard is already opened or is unavailable.')

def wsshutdown():
    global repeat
    repeat = False
    wsstop()
    stop_event.set()

class Vars():
    def __init__(self):
        self.functions = {}
        self.callstack = []
        self.callindent = [-1]
        self.forstack = []
        self.fornames = []
        self.argvs = []
        self.callv = []
        self.rflag = False
        self.rvalue = None
        self.called = False
        self.lazy = -1
        self.idincrement = 0

class Context():
    def __init__(self):
        self.level = 0
        self.stacktrace = []
        self.ifflag = []
        self.dedent = 0

def init():
    global env, ctx, out2, run, output, vars
    env = InteractiveInterpreter()
    ctx = [Context()]
    out2 = None
    output = []
    vars = Vars()
    run = True

def start():
    init()
    sys.displayhook = hook
    ll = asyncio.new_event_loop()
    asyncio.set_event_loop(ll)
    apply()
    global loop, repeat, websocket, stop_event, stop, Connected
    repeat = True
    Connected = False
    websocket = None
    stop_event = Event()
    loop = asyncio.get_event_loop()
    stop = loop.run_in_executor(None, stop_event.wait)
    loop.run_until_complete(main())
    loop.close()

def wsstop():
    global run
    if run == False:
        return
    run = False
    #f = open(os.devnull, 'w')
    sys.stdin = sys.__stdin__
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    #sys.stdin = f
    #sys.stdout = f
    #sys.stderr = f
    print("Resetting...")
    try:
        global env, ctx, out2, output, vars
        del env, ctx, out2, output, vars
    except Exception:
        pass
    init()

if __name__ == "__main__":
    import signal
    def keyboardInterruptHandler(signal, frame):
        print("KeyboardInterrupt (ID: {}) has been caught. Shutting down server...".format(signal))
        wsshutdown()
        exit(0)
    signal.signal(signal.SIGINT, keyboardInterruptHandler)
    start()
