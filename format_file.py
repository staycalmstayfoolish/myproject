import os
import re
import shutil
from multiprocessing import Pool



class formatting:
    def __init__(self):
        self.root_dir = os.getcwd()
        self.ls_in = []
        self.ls_golden = []
        self.ptn_in = 'tv_mem'
        self.ptn_golden = 'dump_file'

    def formatting_input(self, path1):
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
                    #new_name = item[0:item.index('@')+1] + str(core_num) + '.dat'
                    #os.rename(path1 + item, path1 + new_name)

                if 'mem4' in fnlist:
                    new_name = 'tv_mem4_0@' + str(core_num) + '.dat'
                    os.rename(path1 + item, path1 + new_name)
    def formatting_golden(self, path2):
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

    def get_all_subdir(self, rootdir):

        for root, dirs, files in os.walk(rootdir):
            files = None
            for dirname in dirs:
                dir_name_new = os.path.join(root, dirname)
                if dir_name_new.find(self.ptn_in) >= 0:
                    self.ls_in.append(dir_name_new)

                if dir_name_new.find(self.ptn_golden) >= 0:
                    self.ls_golden.append(dir_name_new)

        print(self.ls_in)
        print(self.ls_golden)

        return self.ls_in, self.ls_golden

if __name__ == '__main__':

    fmt = formatting()
    fmt.ls_in, fmt.ls_golden = self.get_all_subdir(fmt.root_dir)

    prcs = Pool(8)
    prcs.map(fmt.formatting_input, fmt.ls_in)
    prcs.map(fmt.formatting_golden, fmt.ls_golden)
    prcs.close()
    prcs.join()



