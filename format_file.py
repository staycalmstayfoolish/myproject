import os
import re
import shutil
from multiprocessing import Pool


ptn_input = 'tv_mem'
ptn_golden = 'dump_file'

def formatting_input(path1):
    path1 += '/'
    for item in os.listdir(path1):
        if item.endswith('.hex'):
            core_num = item[item.index('@')+1:item.index('.')]
            new_name = 'risccode@' + str(core_num) + '.hex'
            os.rename(path1 + item, path1 + new_name)
        if item.endswith('.dat'):
            fnlist = item.split('_')
            temp = fnlist[-1]
            pos1 = temp.index('@')
            pos2 = temp.index('.')
            core_num = temp[pos1+1:pos2]
            ph_num = temp[0:pos1]
            if 'mem01' in fnlist or 'mem2' in fnlist:
                if ph_num != '0' and temp.find('input') < 0:
                    os.remove(path1 + item)
                    continue
                new_name = item[0:item.index('@')+1] + str(core_num) + '.dat'
                os.rename(path1 + item, path1 + new_name)

            if 'mem4' in fnlist:
                new_name = 'tv_mem4_0@' + str(core_num) + '.dat'
                os.rename(path1 + item, path1 + new_name)
def formatting_golden(path2):
    path2 += '/'
    for item in os.listdir(path2):
        if item.endswith('.dat'):
            fnlist = item.split('_')
            temp = fnlist[-1]
            pos1 = temp.index('@')
            pos2 = temp.index('.')
            core_num = temp[pos1 + 1:pos2]
            ph_num = temp[0:pos1]
            if 'mem2' in fnlist:
                if ph_num != '0':
                    hw_phase_num = int(ph_num) - 1
                    golden_name = 'tv_mem2_' + str(hw_phase_num) + '@' + str(core_num) + '.dat.hex.golden'
                    os.rename(path2 + item, path2 + golden_name)
                else:
                    os.remove(path2 + item)
        else:
            os.remove(path2 + item)

def get_all_subdir(rootdir):
    list_input = []
    list_golden = []
    #prcs = pool(4)
    for root, dirs, files in os.walk(rootdir):
        files = None
        for dirname in dirs:
            dir_name_new = os.path.join(root, dirname)
            if dir_name_new.find(ptn_input) >= 0:
                list_input.append(dir_name_new)
                #formatting_input(dir_name_new)
            if dir_name_new.find(ptn_golden) >= 0:
                list_golden.append(dir_name_new)
                #formatting_golden(dir_name_new)
    return list_input, list_golden

if __name__ == '__main__':

    rootdir = os.getcwd()
    ls_input = []
    ls_golden = []
    ls_input, ls_golden = get_all_subdir(rootdir)

    prcs = Pool(8)
    prcs.map(formatting_input, ls_input)
    prcs.map(formatting_golden, ls_golden)
    prcs.close()
    prcs.join()



