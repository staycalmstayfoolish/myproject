#!/usr/bin/python
import os
import re
import shutil
import math
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
        self.ptn_invalid_line = '---- '*(const.FP16_CNT-1) + '----\n'
        self.ptn_invalid_single = '----'
        self.input_core_cnt = 0
        self.ptn_n_recv = 'N_RECEIVED'
        self.ptn_define = '#define'
        self.ptn_set_nrecv0 = '#define N_RECEIVED  0' + '\n'
        self.ptn_input_file = '.input.dat'

    def replace_nrecv_value(self, file_name):
        with open(file_name, 'r+') as f:
            lines = f.readlines()
            line_idx = 0
            for line in lines:
                if line.find(self.ptn_n_recv) > 0 and line.split(' ')[1] == self.ptn_n_recv:
                    lines[line_idx] = self.ptn_set_nrecv0
                    break
                line_idx += 1
            f.seek(0)
            f.writelines(lines)

    def modify_incore_nrecv(self, path_in):
        path_in += '/'
        file_list = os.listdir(path_in)
        input_core_list = [item for item in file_list if item.endswith(self.ptn_input_file)]
        max_input_core = max(map(lambda x: int(x[x.index('@')+1:x.index('.')]), input_core_list))

        input_core = [path_in + 'risccode@' + str(i) + '.c' for i in range(max_input_core + 1)]
        list(map(self.replace_nrecv_value, input_core))

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

    def format_input_core(self, valid_start, valid_cnt, path_input_core):
        with open(path_input_core, 'r+') as f:

            lines = f.readlines()
            lines[0:valid_start-1] = [self.ptn_invalid_line]*(valid_start-1)

            valid_lines, valid_data_residual = divmod(valid_cnt, const.FP16_CNT)
            temp_split = lines[valid_start+valid_lines-1].split(' ')
            #temp = temp_split[:valid_data_residual] + [self.ptn_invalid_single] * (const.FP16_CNT - valid_data_residual)
            #temp[-1] = '----\n'
            temp_split[valid_data_residual:-1] = [self.ptn_invalid_single] * (const.FP16_CNT - valid_data_residual)
            temp_split[-1] = '----\n'
            lines[valid_start + valid_lines - 1] = ' '.join(temp_split)

            lines[valid_start+valid_lines:const.MEM2_ROWS] = [self.ptn_invalid_line]*(const.MEM2_ROWS-valid_start-valid_lines)

            f.seek(0)
            f.writelines(lines)

    def end_with(self, end_str, mem4ptn):
        ends = end_str
        ptn = mem4ptn
        def run(s):
            f1 = map(s.endswith, ends)
            f2 = s.find(ptn)
            if True in f1 and f2 == -1:
                return s
        return run

    def find_mem4(self, mem4ptn):
        ptn = mem4ptn
        def run(s):
            f2 = s.find(ptn)
            if f2 > 0:
                return s
        return run

    def formatting_input(self, path_in):
        path_in += '/'
        ping_pong = 1
        last_core_id = 0
        first_entry = 1
        incre_lp_cnt = 1
        file_list = os.listdir(path_in)
        file_list_hex = list(filter(self.end_with('.hex',''),file_list))
        file_list_data = list(filter(self.end_with('.dat', 'mem4'),file_list))
        file_list_rlut = list(filter(self.find_mem4('mem4'), file_list))
        file_list_data.sort(key=lambda x: int(x[x.index('_',3)+1:x.index('@')]))
        file_list_data.sort(key=lambda x: int(x[x.index('@') + 1:x.index('.')]))

        path_route = path_in.replace('tv_mem/', '')
        route_file = path_route + 'board_route.txt'
        route_cfg = self.read_route_cfg(route_file)

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

                    mem_base1 = route_cfg[core_id][Route_cfg.MEM_BASE1_E.value]
                    incre = 1792#route_cfg[core_id][Route_cfg.INCRE_E.value] * 2
                    len = route_cfg[core_id][Route_cfg.LEN_E.value]
                    incre_loop = int(route_cfg[core_id][Route_cfg.INCRE_LOOP_E.value] / 28)

                    if core_id - last_core_id > 0:
                        incre_lp_cnt = 0

                    valid_data_start = int((mem_base1 + incre * incre_lp_cnt ) * 2 / const.LINE_LEN) + 1
                    #valid_data_line = int(len / const.FP16_CNT)

                    self.format_input_core(valid_data_start, len, path_in + item)

                    incre_lp_cnt += 1
                    if incre_lp_cnt >= incre_loop:
                        incre_lp_cnt = 0

                    last_core_id = core_id

                elif 'mem2' in fnlist and temp.find('input') > 0 and ph_num > '0':

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
                    #valid_data_line = int((mem_base2 - mem_base1) / const.LINE_LEN)
                    valid_data_cnt = route_cfg[core_id][Route_cfg.LEN_E.value]

                    last_core_id = core_id

                    if const.FOR_SIMU:
                        new_name = item[0:item.index('@') + 1] + str(core_id) + '.dat'
                        os.rename(path_in + item, path_in + new_name)

                    else:
                        # self.format_input_core(valid_data_start, valid_data_line, path_in+item)
                        self.format_input_core(valid_data_start, valid_data_cnt, path_in + item)

        for item in file_list_rlut:
            core_id = int(item[item.index('@')+1:item.index('.')])
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
                        golden_name = 'tv_mem2_' + str(hw_phase_num) + '@' + str(core_id) + '.dat.golden'
                        os.rename(path_golden + item, path_golden + golden_name)
                    else:
                        os.remove(path_golden + item)
            else:
                os.remove(path_golden + item)

    def get_all_subdir(self, rootdir):

        for root, dirs, files in os.walk(rootdir):
            files[:]= []
            #for dirname in dirs:
            if not dirs:
                dir_name_new = root

                if dir_name_new.find(self.ptn_in) >= 0:
                    self.ls_in.append(dir_name_new)

                elif dir_name_new.find(self.ptn_golden) >= 0:
                    self.ls_golden.append(dir_name_new)
        print(self.ls_in)
        print(self.ls_golden)

        return self.ls_in, self.ls_golden

if __name__ == '__main__':

    fmt = formatting()
    fmt.ls_in, fmt.ls_golden = fmt.get_all_subdir(fmt.root_dir)

    if const.FOR_SIMU:
        prcs = Pool(8)
        prcs.map(fmt.modify_incore_nrecv, fmt.ls_in)
        prcs.close()
        prcs.join()
    else:
        prcs = Pool(8)
        prcs.map(fmt.formatting_input, fmt.ls_in)
        prcs.map(fmt.formatting_golden, fmt.ls_golden)
        prcs.close()
        prcs.join()


