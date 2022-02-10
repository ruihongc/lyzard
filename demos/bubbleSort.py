def bubbleSort(a):
    n = len(a)
    for i in range(n-1):
        for j in range(0, n-i-1):
            if a[j] > a[j + 1]:
                tmp = a[j]
                a[j] = a[j + 1]
                a[j+1] = tmp
    return a

arr = [64, 34, 25, 11, 90]
sortedArr = bubbleSort(arr.copy())
for i in range(len(sortedArr)):
    print (sortedArr[i])