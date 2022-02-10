def insertionSort(a):
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >=0 and key < a[j] :
                a[j+1] = a[j]
                j = j - 1
        a[j+1] = key
    return a
arr = [12, 11, 13, 5, 6]
sortedArr = insertionSort(arr.copy())
for i in range(len(sortedArr)):
    print (sortedArr[i])