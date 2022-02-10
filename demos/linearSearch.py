def linearSearch(arr, x):
    for i in range(len(arr)):
        if arr[i] == x:
            return i
    return -1

print(linearSearch([91, 13, 36, 84, 5], 36))
print(linearSearch([91, 13, 36, 84, 5], 22))