#!/usr/bin/env python3
# -*- coding: utf-8 -*-
########################
#    Author: Dingrq
#    Date  : 2018.11.8
########################
import subprocess as sp
import re
import sys
import argparse
import xlsxwriter
import threading
import ctypes
import inspect
from tqdm import tqdm
from time import sleep
from casemem import *
from caselog import *
from path import *
from label import *

class case:
    '''
    Compare the generated IO memory files with files from high level model.
    Write reports to log file.
    '''
    def __init__(self,casename=''):
        self.caseName=casename
        self.homeDir=HOMEDIR
        self.srcDir=TVDIR
        self.dstDir=CYCLOGDIR
        self.logDir=LOCALLOG
        self.statistic=[]
        if not os.path.exists(LOCALLOG):#没有此路径则创建一个
            os.makedirs(LOCALLOG)
        cmd='rm -f '+LOCALLOG+'*.log '+LOCALLOG+'*.xlsx'
        sp.getstatusoutput(cmd)#bash 执行
    def argParse(self):#./case000_
        arg=argparse.ArgumentParser()#解析字符串
        arg.add_argument('case',metavar='CASE',help='set the testvector directory')#添加参数和help信息
        arg.add_argument('-l','--level',metavar='LEVEL',choices=[0,1,2],type=int,default=0,help='set the tb level '
                                                                                                '0:single case '  
                                                                                                '1:single group of cases '  
                                                                                                '2:groups of cases')
        arg.add_argument('-o','--log',metavar='LOGDIR',default=LOCALLOG,help='set the log directory')
        arg.add_argument('-d','--dump',metavar='RESULT',default=CYCLOGDIR,help='set the cycaccu dumped directory')
        argv=arg.parse_args()
        self.level=argv.level#将参数给到自己的类里
        self.dstDir=argv.dump
        self.logDir=argv.log
        self.caseDirParse(argv.case)
    def setDir(self,homedir='',srcdir='',dstdir='',logdir=''):#设置路径
        if homedir !='':
            self.homeDir=homedir
        if srcdir !='':
            self.srcDir=srcdir
        if dstdir !='':
            self.dstDir=dstdir
        if logdir !='':
            self.logDir=logdir
    def caseDirParse(self,string):#当参数中有没有文件夹最后的/都可以正确执行 ./test/concat/
        if string[-1]=='/':
            string = string[:-1]
        ele=re.split('/',string)
        if len(ele)<=1:
            self.srcDir='./'
            self.caseName=ele
        else:
            self.srcDir='/'.join(ele[:-1])+'/'
            self.caseName=ele[-1]
    def genCoreIdList(self,directory,casename):#产生coreid的list
        tvmemdir=directory+casename+'/tv_mem/'
        ret,cfile=self.fileList(tvmemdir,'risccode@*.c')
        idlist=[]
        if ret:
            for ele in cfile:#对每个.c文件进行分割找到其中的num
                cord=re.split('@',ele)
                cord=re.split('\.',cord[1])
                #cord=re.split('_',cord[0])
                idlist.append(int(cord[0]))
        return ret,idlist
    def procRunStdOut(self,content):
        startphase=-1
        endphase=-1
        totalclk=0
        maxclk=-1
        maxphase=-1
        statis=[]
        lines=re.split('\n',content)
        for line in lines:
            if 'phase :' in line:
                ele=re.split(' ,',line)
                phase=re.split(' : ',ele[0])
                endphase=int(phase[1])
                if startphase==-1:
                    startphase=endphase
                clk=re.split(' : ',ele[1])
                clk=int(clk[1])
                totalclk=totalclk+clk
                phase=re.split(' : ',ele[0])
                phase=int(phase[1])
                if clk>maxclk:
                    maxclk=clk
                    maxphase=phase
        statis.append(('RunPhase',str(startphase)+'-'+str(endphase),startphase,endphase))
        statis.append(('TotalClks',str(totalclk),totalclk))
        statis.append(('MaxClks-Phase',str(maxclk)+'-'+str(maxphase),maxclk,maxphase))
        return statis
    def procSingleCaseLog(self,directory,casename,idlist):
        casel=caselog(casename)
        casel.corelist=idlist
        casel.setDir(homedir=self.homeDir,cyclogdir=directory,logdir=self.logDir)
        return casel.process()
    @staticmethod
    def singleCaseProgressDisplay(casedir):
        ret,mem2files=case.fileList(casedir+'/tv_mem/','tv_mem2_*.dat')
        if not ret:
            return
        maxphase=0
        for mem2file in mem2files: 
            ele=re.split('@',mem2file)
            ele=re.split('_',ele[0])
            phase=int(ele[-1])
            if phase>maxphase:
                maxphase=phase
        with open('bashstdout.txt','r') as f:#with内文件一直打开
            curphase=0
            bar=tqdm(range(maxphase))
            bar.set_description('Simulating')
            for i in bar:
                if curphase>=i:
                    continue;
                while(1):
                    sleep(0.1)
                    lines=f.readlines()
                    if lines:
                        for line in lines:
                            if 'phase :' in line:
                                ele=re.split(' ,',line)
                                phase=re.split(' : ',ele[0])
                                if curphase<int(phase[1]):
                                    curphase=int(phase[1])
                        if curphase>=i:
                            break;
            bar.close()
    def verifySingleCase(self,directory,casename,cmd):
        statis=[('Case',casename)]
        idret,idlist=self.genCoreIdList(directory,casename)
        if idret:
            statis.append(('Cores',len(idlist)))
        cmd=cmd+'|tee bashstdout.txt'
        progress=threading.Thread(target=case.singleCaseProgressDisplay,args=(directory+casename,))
        progress.start()
        ret,content=sp.getstatusoutput(cmd)
        progress.join(100)#stop_thread(progress)

        if ret!=0:#若命令执行出错 则返回屏幕的打印信息
            print(content)
            return False
        casem=casemem(casename)
        casem.logName='Tsummary'#将所有core信息都打印到同一个文件中
        casem.setDir(homedir=self.homeDir,srcdir=directory,dstdir=self.dstDir,logdir=self.logDir)
        ########################################
        #####added by wjw for dump_file copy####

        temp = cmd[cmd.index(' ')+1:]
        temp = temp.replace('tv_mem','')
        cmd1 = 'cp -r ' + self.dstDir + 'dump_file/ ' + temp
        ret1,constent1 = sp.getstatusoutput(cmd1)

        ###############end by wjw###############
        ########################################

        ret=casem.caseMem2Cmp()#将对mem2进行比较
        if ret:
            statis.append(('Verify','passed'))
            statis=statis+self.procRunStdOut(content)
            if idret:
                statis=statis+self.procSingleCaseLog(self.dstDir,casename,idlist)
        else:
            statis.append(('Verify','failed'))
        self.statistic.append(statis)
        return ret
    def verifyCases(self):
        passcnt=0
        cmd='cp -f {main,start_compile_ln} '+self.srcDir+self.caseName
        ret,content = sp.getstatusoutput(cmd)
        if ret!=0:
            print(content)
            return 0
        if self.level==0:
            print('Processing '+self.caseName)
            cmd=self.srcDir+self.caseName+'/start_compile_ln '+self.srcDir+self.caseName+'/tv_mem'
            if self.verifySingleCase(self.srcDir,self.caseName,cmd):
                passcnt=passcnt+1
        elif self.level==1:
            ret,lv0dirlist=self.subDirList(self.srcDir+self.caseName+'/','case')
            if ret:
                for lv0dir in lv0dirlist:
                    print('Processing '+lv0dir)
                    casedir=self.srcDir+self.caseName+'/'
                    cmd=self.srcDir+self.caseName+'/start_compile_ln '+casedir+lv0dir+'/tv_mem'
                    if self.verifySingleCase(casedir,lv0dir,cmd):
                        passcnt=passcnt+1
        elif self.level==2:
            ret,lv1dirlist=self.subDirList(self.srcDir+self.caseName+'/','')
            if ret:
                for lv1dir in lv1dirlist:
                    print('\nEntering '+lv1dir+':')
                    self.statistic.append(('Dir',lv1dir+':'))
                    ret,lv0dirlist=self.subDirList(self.srcDir+self.caseName+'/'+lv1dir+'/','case')
                    if ret:
                        for lv0dir in lv0dirlist:
                            print('Processing '+lv0dir)
                            casedir=self.srcDir+self.caseName+'/'+lv1dir+'/'
                            cmd=self.srcDir+self.caseName+'/start_compile_ln '+casedir+lv0dir+'/tv_mem'
                            if self.verifySingleCase(casedir,lv0dir,cmd):
                                passcnt=passcnt+1
        else:
            print("Verified level is undefined!")
        return passcnt
    @staticmethod
    def fileList(srcdir,feature):
        cmd='find '+srcdir+' -name \"'+feature+'*\"|sort '#查找某一特征的文件并排序
        ret,filelist = sp.getstatusoutput(cmd)
        if ret==256 or 'No such' in filelist:
            print(filelist)
            return False,filelist
        filelist=filelist.replace(srcdir,'') # delete the srcdir
        filelist=filelist.split('\n');
        return True,filelist
    @staticmethod
    def subDirList(srcdir,feature):
        cmd='ls -d '+srcdir+feature+'*/|sort'
        ret,subdirlist = sp.getstatusoutput(cmd)
        if ret==256 or 'No such' in subdirlist:
            print(subdirlist)
            return False,subdirlist
        subdirlist=subdirlist.replace(srcdir,'') # delete the srcdir
        subdirlist=subdirlist.replace('/','') # delete the '/'
        subdirlist=subdirlist.split('\n');
        return True,subdirlist
    def genXlsxFile(self,name=''):
        if name=='':
            realname=self.logDir+'Tsummary.xlsx'
        else:
            realname=self.logDir+name+'.xlsx'        
        workbook = xlsxwriter.Workbook(realname)
        worksheet = workbook.add_worksheet()
        header_format = workbook.add_format()
        header_format.set_bold()
        header_format.set_align('left') #'center' 'justify'
        cell_format = workbook.add_format()
        cell_format.set_align('left')
        dicts=xlsxStatisItemDict
        worksheet.set_row(0,40,header_format)
        mincol=''
        maxcol=''
        for key in dicts:
            if mincol=='':
                mincol=dicts[key][0]
                maxcol=dicts[key][0]
            if mincol > dicts[key][0]:
                mincol=dicts[key][0]
            if maxcol < dicts[key][0]:
                maxcol=dicts[key][0]
            worksheet.set_column(dicts[key][0]+':'+dicts[key][0],dicts[key][1])
            worksheet.write(dicts[key][0]+'1',key)
        row=0
        for caseitem in self.statistic:
            row=row+1
            if isinstance(caseitem[0],str):
                if caseitem[0]=='Dir':
                    worksheet.merge_range(mincol+str(row+1)+':'+maxcol+str(row+1),caseitem[1],cell_format)
                    continue
            worksheet.set_row(row,20,cell_format)
            for item in caseitem:
                for key in dicts:
                    if item[0]==key:
                        worksheet.write(dicts[key][0]+str(row+1),item[1])
                        break
        workbook.close()

def _async_raise(tid, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")
def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)

def verifyCycAcc(casedir,level=0):
    tv=case()
    tv.level=level
    tv.caseDirParse(casedir)
    cnt=tv.verifyCases()
    tv.genXlsxFile()
    return cnt


if __name__ == '__main__':
    tv=case()
    tv.argParse()
    cnt=tv.verifyCases()
    tv.genXlsxFile()
