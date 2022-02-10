def hex2dec(ip):
    ret = 0
    tlen = len(ip)
    for i in range(tlen):
        hex = "0123456789ABCDEF"
        value= hex.index(ip[i])
        power = (tlen -(i+1))
        ret = ret + (value*16**power)
    return ret

print(hex2dec('DEADBEEF'))
print(hex2dec('CAFEBABE'))