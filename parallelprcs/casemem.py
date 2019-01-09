#!/usr/bin/env python3
# -*- coding: utf-8 -*-
########################
#    Author: Dingrq
#    Date  : 2018.11.8
########################
import subprocess as sp
import time
import re
import sys
from tqdm import tqdm
from path import *

class casemem:
    '''
    Compare the generated IO memory files with files from high level model.
    Write reports to log file.
    '''
    def __init__(self,casename=''):
        self.caseName=casename
        self.logName=casename
        self.homeDir=HOMEDIR
        self.srcDir=TVDIR
        self.dstDir=CYCLOGDIR
        self.logDir=LOCALLOG
    def setDir(self,homedir='',srcdir='',dstdir='',logdir=''):
        if homedir !='':
            self.homeDir=homedir
        if srcdir !='':
            self.srcDir=srcdir
        if dstdir !='':
            self.dstDir=dstdir
        if logdir !='':
            self.logDir=logdir
    @staticmethod
    def primFetchInfoEx(filename):#查找fetch原语的位置
        corelist=[]
        linenolist=[]
        with open(filename,'r') as f:#with内文件一直打开
            while True:
                lines=f.readlines(0x4000)#先读取一个数据块
                if lines:
                    for line in lines:
                        line=line.replace('\n','')#若是个空行则跳过
                        if line=='':
                            continue
                        elements=re.split(':',line)#按：进行分割
                        #cord=elements[0].split(',')
                        #x=cord[0]
                        #y=cord[1]
                        #cord=y+'_'+x
                        corelist.append(elements[0])
                        corelineno=[]
                        for ele in elements[1:]:
                            ele=ele.split(',')
                            lineno=(ele[0],ele[1])
                            corelineno.append(lineno)#核内有多个fetch拼成一个list
                        linenolist.append(corelineno)#多个核再拼成一个list
                else:
                    break
        primFetchInfoDict=dict(zip(corelist,linenolist))#核与fetch的位置信息一一对应，一个核可能包含多个fetch
        return primFetchInfoDict
    @staticmethod
    def sameFileList(srcdir,dstdir,feature):#列出相同文件名的源与目的的list
        cmd='find '+srcdir+' -name \"'+feature+'*\"|sort '#查找某一特征的文件并排序
        ret,srcfiles = sp.getstatusoutput(cmd)#ret是返回是否有命令执行错误
        if ret==256:#有错误则退出
            return False,srcfiles
        srcfiles=srcfiles.replace(srcdir,'') # Keep the file name and delete the path
        srcfiles=srcfiles.split('\n');#以\n进行分割成多条单独的文件名
        cmd='find '+dstdir+' -name \"'+feature+'*\"|sort '
        ret,dstfiles = sp.getstatusoutput(cmd)
        if ret==256:
            return False,dstfiles
        dstfiles=dstfiles.replace(dstdir,'')
        dstfiles=dstfiles.split('\n');
        if len(srcfiles)==0 or len(dstfiles)==0:
            return False,'There was no mem2 file in directory!\n'
        filelist=[]
        for srcfile in srcfiles:
            #ignore input core, mem2Name.replace('input','')
            for dstfile in dstfiles:
                if srcfile == dstfile:
                    filelist.append(srcfile)
        filelist.sort(key = lambda filename : int(re.split('_',re.split('@',filename)[0])[-1]))#对文件名相同的文件进行按coreid排序
        return True,filelist
    def memDiffIsFetch(self,content,fetchdict,filename):
        cord = re.split('@',filename)
        cord = re.split('\.',cord[1])
        cord = cord[0]
        for key in fetchdict:
            if key == cord:
                for line in content.split('\n'):
                    if 'a' == line[0]:
                        return False
                    elif 'd' in line[0]:
                        return False
                    elif 'c' in line[0]:
                        positions = re.split(' ',line[1:])
                        for pos in positions:
                            issame = False
                            for val in fetchdict[key]:
                                if int(pos) == int(val[1])+1:
                                    issame = True
                                    break
                            if not issame:
                                return False
                return True
        return False
    def caseMem2Cmp(self):
        '''
            Compare the mem2 contents. Src is from C model. Dst is from tj3cycleacc
            input: casename
        '''
        if self.caseName=='':#若文件夹内没有文件则返回
            print('casename is empty')
            return False
        tmpstr='Compare the mem2 contents of '+self.caseName+':'#打印比较当前casename的文件信息
        tvdir=self.srcDir+self.caseName+'/tv_mem/'#源文件名
        logdumpdir=self.dstDir+'/dump_file/'#目的文件名
        fpLog=open(self.logDir+self.logName+'.log','a+')#打开log文件
        fpLog.read()#将指针指到文件最后
        fpLog.write(tmpstr+'\n')#追加写入信息
        ret,filelist=self.sameFileList(tvdir,logdumpdir,'tv_mem2_')#找到文件名一致的列一个list
        if not ret:
            fpLog.write(filelist+'\n')
            print(filelist)
            return False
        fetchinfo = self.primFetchInfoEx(self.srcDir+self.caseName+'/fetchprim_pos.txt')#找到文件中fetch的原语位置
        allsame=1
        samefiles=0
        if len(filelist)==0:
            allsame=0
        dumpnum=0
        bar=tqdm(filelist)
        bar.set_description('Verifying ')
        for filename in bar:
            cmd='diff '+tvdir+filename+' '+logdumpdir+filename+' -f'
            ret,result=sp.getstatusoutput(cmd)#比较文件是否相同
            if result == '':
                samefiles+=1
            elif self.memDiffIsFetch(result,fetchinfo,filename):
                samefiles+=1
            else:
                allsame=0
                if dumpnum<2:
                    fpLog.write('File '+filename+' diff content:\n')
                    fpLog.write(result+'\n')
                    dumpnum=dumpnum+1
                else:
                    break
        bar.close()
        if allsame==1:
            tmpstr=self.caseName+' passed:'+str(samefiles)+' same files'
            ret=True
        else:
            tmpstr=self.caseName+' failed:'+str(samefiles)+' same files'
            ret=False
        print(tmpstr)
        fpLog.write(tmpstr+'\n')
        fpLog.close()
        return ret


if __name__ == '__main__':
    if len(sys.argv)==1:
        casename=''
    else:
        casename=sys.argv[1]
    casename=casename.replace('/','')
    if not os.path.exists(LOCALLOG):
        os.makedirs(LOCALLOG)
    cmd='rm -f '+LOCALLOG+'*.log'
    sp.getstatusoutput(cmd)
    case=casemem(casename)
    case.caseMem2Cmp()
