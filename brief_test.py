import os
from constant import const
from route_cfg_enum import Route_cfg

path = 'abc/def/gh'
path = path.replace('gh','')
print(path)

lis1 = [1,2,3]
lis2 = [4,5,6]

list3 = []
list3.append(lis1)
list3.append(lis2)
print(len(list3))
print(Route_cfg.MEM_BASE1_E.value)
a = 'abcg'
b= a*4
print(b)


def end_with(*end_str):
    ends = end_str

    def run(s):
        f = map(s.endswith, ends)
        if True in f:
            return s

    return run

list_file = os.listdir(os.getcwd())
a = end_with('.dat')
#f_file = list(filter(a,list_file))

file_list_data = list(filter(a, list_file))
file_list_data.sort(key = lambda x: x[x.index('_',3)+1:x.index('@')])
print(file_list_data)
file_list_data.sort(key = lambda x: x[x.index('@')+1:x.index('.')])
print(file_list_data)

print(type(Route_cfg.MEM_BASE1_E.value))

a = 'tv_mem01_20@2.input.dat'
print(int(a[a.index('_',3)+1:a.index('@')]))
print(int(a[a.index('@') + 1:a.index('.')]))
print(a.split('_')[2][0:a.split('_')[2].index('@')])
b = a.find('mem2')
print(type(b))
list1 = [1, 3 ,5, 7, 9]
list2 = [3, 7, 9]
print(list(set(lis1) - set(list2)))