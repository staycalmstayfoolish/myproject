import os
import re
import shutil
from multiprocessing import Pool
from constant import const
from route_cfg_enum import Route_cfg

class formatting:
    def __init__(self):
        self.root_dir = os.getcwd()
        self.ls_in = []
        self.ls_golden = []
        self.ptn_in = 'tv_mem'
        self.ptn_golden = 'dump_file'
        self.ptn_input_core = 'board_route'
        self.ptn_invalid = '---- '*(const.FP16_CNT-1) + '----\n'
        self.input_core_cnt = 0

    def read_route_cfg(self, path_route):
        total_core_cfg = []
        with open(path_route, 'r') as f:
            route_cnt = int(f.readline())
            for i in range(route_cnt):
                single_core_cfg = []
                for j in range(const.TOTAL_ROUTE_CFG):
                    single_core_cfg.append(int(f.readline()))
                total_core_cfg.append(single_core_cfg)
        return total_core_cfg

    def format_input_core(self, valid_start, valid_lines, path_input_core):
        with open(path_input_core, 'r+') as f:
            lines = f.readlines()
            lines[0:valid_start-1] = [self.ptn_invalid]*(valid_start-1)
            lines[valid_start+valid_lines-1:const.MEM2_ROWS] = [self.ptn_invalid]*(const.MEM2_ROWS-valid_start-valid_lines+1)

            f.seek(0)
            f.writelines(lines)

    def end_with(self, *end_str):
        ends = end_str
        def run(s):
            f = map(s.endswith, ends)
            if True in f:
                return s
        return run


    def formatting_input(self, path_in):
        path_in += '/'
        ping_pong = 1
        last_core_id = 0
        first_entry = 1
        file_list = os.listdir(path_in)
        file_list_hex = list(filter(self.end_with('.hex'),file_list))
        file_list_data = list(filter(self.end_with('.dat'),file_list))
        file_list_data.sort(key=lambda x: x[x.index('_',3)+1:x.index('@')])
        file_list_data.sort(key=lambda x: x[x.index('@') + 1:x.index('.')])

        for item in file_list_hex:
            #if item.endswith('.hex'):
            core_id = item[item.index('@')+1:item.index('.')]
            new_name = 'risccode@' + str(core_id) + '.hex'
            os.rename(path_in + item, path_in + new_name)
        for item in file_list_data:
            #if item.endswith('.dat'):
            fnlist = item.split('_')
            temp = fnlist[-1]
            pos1 = temp.index('@')
            pos2 = temp.index('.')
            core_id = int(temp[pos1+1:pos2])
            ph_num = temp[0:pos1]

            if 'mem01' in fnlist or 'mem2' in fnlist:
                if ph_num != '0' and temp.find('input') < 0:
                    os.remove(path_in + item)
                    continue
                elif 'mem01' in fnlist and temp.find('input') > 0 and ph_num > '0':
                    path_route = path_in.replace('tv_mem/','')
                    route_file = path_route + 'board_route.txt'
                    route_cfg = self.read_route_cfg(route_file)

                    mem_base1 = route_cfg[core_id][Route_cfg.MEM_BASE1_E.value]
                    #mem_base2 = route_cfg[core_id][Route_cfg.MEM_BASE2_E.value]
                    valid_data_start = mem_base1 / const.LINE_LEN + 1
                    valid_data_line = (mem_base2 - mem_base1) / const.LINE_LEN
                    self.format_input_core(valid_data_start, valid_data_line, path_in + item)


                elif 'mem2' in fnlist and temp.find('input') > 0 and ph_num > '0':

                    path_route = path_in.replace('tv_mem/', '')
                    route_file = path_route + 'board_route.txt'
                    route_cfg = self.read_route_cfg(route_file)

                    mem_base1 = route_cfg[core_id][Route_cfg.MEM_BASE1_E.value]
                    mem_base2 = route_cfg[core_id][Route_cfg.MEM_BASE2_E.value]

                    if first_entry:
                        ping_pong = 1
                        first_entry = 0
                    else:
                        if (core_id - last_core_id) > 0:
                            ping_pong = 1
                        else:
                            ping_pong = 0 if ping_pong == 1 else 1

                    valid_data_start = int((mem_base2 - const.MEM2_BASE) / const.LINE_LEN) + 1 if ping_pong == 1 else int((mem_base1 - const.MEM2_BASE) / const.LINE_LEN) + 1
                    valid_data_line = int((mem_base2 - mem_base1) / const.LINE_LEN)

                    last_core_id = core_id

                    self.format_input_core(valid_data_start, valid_data_line, path_in+item)

                #new_name = item[0:item.index('@')+1] + str(core_num) + '.dat'
                #os.rename(path1 + item, path1 + new_name)

            if 'mem4' in fnlist:
                new_name = 'tv_mem4_0@' + str(core_id) + '.dat'
                os.rename(path_in + item, path_in + new_name)
    def formatting_golden(self, path_golden):
        path_golden += '/'
        for item in os.listdir(path_golden):
            if item.endswith('.dat'):
                fnlist = item.split('_')
                temp = fnlist[-1]
                pos1 = temp.index('@')
                pos2 = temp.index('.')
                core_id = temp[pos1 + 1:pos2]
                ph_num = temp[0:pos1]
                if 'mem2' in fnlist:
                    if ph_num != '0':
                        hw_phase_num = int(ph_num) - 1
                        golden_name = 'tv_mem2_' + str(hw_phase_num) + '@' + str(core_id) + '.dat.hex.golden'
                        os.rename(path_golden + item, path_golden + golden_name)
                    else:
                        os.remove(path_golden + item)
            else:
                os.remove(path_golden + item)

    def get_all_subdir(self, rootdir):

        for root, dirs, files in os.walk(rootdir):
            files = None
            for dirname in dirs:
                dir_name_new = os.path.join(root, dirname)
                if dir_name_new.find(self.ptn_in) >= 0:
                    self.ls_in.append(dir_name_new)

                if dir_name_new.find(self.ptn_golden) >= 0:
                    self.ls_golden.append(dir_name_new)

        #print(self.ls_in)
        #print(self.ls_golden)

        return self.ls_in, self.ls_golden

if __name__ == '__main__':

    fmt = formatting()
    fmt.ls_in, fmt.ls_golden = fmt.get_all_subdir(fmt.root_dir)

    prcs = Pool(8)
    prcs.map(fmt.formatting_input, fmt.ls_in)
    prcs.map(fmt.formatting_golden, fmt.ls_golden)
    prcs.close()
    prcs.join()



