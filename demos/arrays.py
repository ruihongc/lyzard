a = [[1, 2], [3, 4]]
x = 7
a[1][0] = a[0][0]
a[1][1] = [3, 4, 5, 6, 6]
a[1][1][3] = [1, 2, 3]
print(a[1][1].index(4))
a[1][1].append(a[1][0])
a[1][1][3].clear()
a[1][1][3].append(x)
a[1][1].pop(1)
a[1][1].insert(1, [1, 2, 3])