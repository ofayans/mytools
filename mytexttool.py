#!/usr/bin/python
# -*- coding: UTF-8 -*-

####################################
##   Author Oleg Fajans, RedHat.  ###
##   mailto:ofajans@gmail.com
####################################

from Tkinter import *
import os, re, fileinput, shutil, tkFileDialog, sys, threading
import pdb


def Replace(SRCEXPR, STRING, FILE):
  """Replace(searchExp, ReplaceString, File)"""
  for line in fileinput.input(FILE, inplace=1, bufsize=1024):
    print re.sub(SRCEXPR, STRING, line.rstrip('\n'))

def PrependLine(File, Line):
  """PrependLine(File, Line) Puts a line to the head of the file (useful for adding file headers)"""
  with open(File, "r+", 1024) as f:
    old = f.read() # read everything in the file
    f.seek(0) # rewind
    f.write(Line+'\n'+old) # write the new line before

def Timetree(DIR, Regex):
  """Timetree(DIR, Regex)
  sorts all files in the provided folder - DIR, matching the given Regex, by date, creates a set of
  subfolders with date as names and moves files in corresponding folders
  """
  for i in os.listdir(DIR):
    a=os.path.join(DIR, i)
    Date=str(datetime.datetime.fromtimestamp(os.path.getatime(a))).split(' ')[0]
    try:
      os.makedirs(os.path.join(DIR, Date))
    except OSError:
      pass
    if int(os.path.getatime(a)) < int(time.time()) - 300 and Regex.match(i):
      shutil.move(a, os.path.join(DIR, Date))


def Massproc(ACT, SRC, RE1, RE2='', DST=''):
  """Recursively applies one of three actions at the files in given folder. Actions could be: Replace(), PrependLine, or selective copy/move of files. 
	Accepts from 3 to 5 string parameters. First one is Action. Possible values are: copy, move, prepend, replace. Second parameter is the source folder in which to perform actions. 
	Third parameter is a regex to process only files, whose filenames match this regex. Fourth parameter depends on the action: for copy/move it will be the path to destination folder. 
	For prepend it will be the line to prepend in files (for example - logfile header). For replace - it will be the regular expression to search in the files. 
  Fifth parameter only used for replace action and contains the replace string"""
  Dict1 = {'copy': shutil.copy, 'move': shutil.move, 'prepend': PrependLine, 'replace': Replace}
  if ACT == 'timetree':
    Timetree(SRC, RE1)
  else:
    for root, dirs, files in os.walk(SRC, topdown=False):
      List=[root, files]
      for i in List[1]:
        if re.match(RE1, i):
          a=os.path.join(List[0], i)
          if ACT == 'custom':
            if sys.platform == 'win32':
              a='\"'+a.replace('/', '\\')+'\"'
            else:
              a='\"'+a+'\"'
              job = threading.Thread(target = os.system(RE2+' '+a))
              job.start()
#            os.system(RE2+' '+a)
          elif ACT in ['copy', 'move']:
            DestinationDir=re.sub('^'+SRC, RE2, root)
            try:
              os.makedirs(DestinationDir)
            except(OSError):
              pass
            Dict1[ACT](a, DestinationDir)
          elif ACT == 'prepend':
            job = threading.Thread(target = Dict1[ACT](a, RE2))
            job.start()
          else:
            job = threading.Thread(target = Dict1[ACT](RE2, DST, a))
            job.start()
     
###########################################################################################
# GUI Part
###########################################################################################

class Error():
  def __init__(self):
    self.root=Tk()
    self.root.title('Error')
    self.Message=Label(self.root, text='You must chose an action in the drop-down menu').grid(row=0, column=0)
    self.root.mainloop()
    

class Maingui():
  def __init__(self, string1, string2, string3, string4, string5=''):
    self.string1=string1
    self.string2=string2
    self.string3=string3
    self.string4=string4
    self.string5=string5
    self.root=Tk()
    self.root.title(self.string1)
    self.Input1 = Entry(self.root, bg = "white")  # creates a text entry field
    self.Input1.grid(row=2, column=1)
    self.Input1.insert(0, "") # Place text into the box.
    self.Input1Label=Label(self.root, text=self.string2)
    self.Input1Label.grid(row=2, column=0)
    self.BrowseSrc=Button(self.root, text = 'Browse', command = self.BrowseSRC).grid(row=2, column=2)
    if self.string3:
      self.Input2 = Entry(self.root, bg = "white")
      self.Input2.grid(row=3, column=1)
      self.Input2.insert(0, "")
      self.Input2Label=Label(self.root, text=self.string3)
      self.Input2Label.grid(row=3, column=0)
    if self.string4:
      self.Input3 = Entry(self.root, bg = "white")
      self.Input3.grid(row=4, column=1)
      self.Input3.insert(0, "")
      self.Input3Label=Label(self.root, text=self.string4)
      self.Input3Label.grid(row=4, column=0)
    if self.string5:
      self.Input4 = Entry(self.root, bg = "white")
      self.Input4.grid(row=5, column=1)
      self.Input4.insert(0, "")
      self.Input4Label=Label(self.root, text=self.string5)
      self.Input4Label.grid(row=5, column=0)
    if self.string1 == 'Selective copy/move':
      self.MOVE = 0
      Chk = Checkbutton(self.root, text='Move files instead of copy', command = self.ChangeValue).grid(row=5, column=0)
      self.BrowseDst=Button(self.root, text = 'Browse', command = self.BrowseDST).grid(row=3, column=2)
    if self.string1 == 'Perform custom action':
      self.BrowseUtil=Button(self.root, text = 'Browse', command = self.BrowseUtil).grid(row=3, column=2)
    button=Button(self.root, text="Proceed", command = self.Proceed).grid(row=6, column=0)
    self.root.mainloop()
  def BrowseSRC(self):
    self.BrowsedSrcDir=tkFileDialog.askdirectory()
    self.Input1.insert(0, self.BrowsedSrcDir)
  def BrowseDST(self):
    self.BrowsedDstDir=tkFileDialog.askdirectory()
    self.Input2.insert(0, self.BrowsedDstDir)
  def BrowseUtil(self):
    self.BrowsedUtil=tkFileDialog.askopenfilename()
    self.Input2.insert(0, self.BrowsedUtil)
  def ChangeValue(self):
    if self.MOVE:
      self.MOVE=0
    else:
      self.MOVE=1
  def Proceed(self):
    if self.string1 == 'Global string replace':
      self.folder = self.Input1.get()
      self.RE1 = self.Input2.get()
      self.FileRE = self.Input3.get()
      self.String = self.Input4.get()
      Massproc('replace', self.folder, self.FileRE, self.RE1, self.String)
    elif self.string1 == 'Global prepend line':
      self.folder = self.Input1.get()
      self.String = self.Input2.get()
      self.FileRE = self.Input3.get()
      Massproc('prepend', self.folder, self.FileRE, self.String)
    elif self.string1 == 'Perform custom action':
      self.folder = self.Input1.get()
      self.String = self.Input2.get()
      self.FileRE = self.Input3.get()
      Massproc('custom', self.folder, self.FileRE, self.String)
    elif self.string1 == 'Sort files by creation time':
      self.folder = self.Input1.get()
      self.RE1 = self.Input2.get()
      Massproc('timetree', self.folder, self.RE1)
    else:
      self.SRCFolder = self.Input1.get()
      self.DSTFolder = self.Input2.get()
      self.FileRE = self.Input3.get()
      if self.MOVE:
        self.Act='move'
      else:
        self.Act='copy'
      Massproc(self.Act, self.SRCFolder, self.FileRE, self.DSTFolder)

class Startgui():
  def __init__(self):
    self.root=Tk()
    self.root.title("select an action")
    self.var = StringVar(self.root)
    self.var.set("select action")
    self.chosen_option="default"
    self.drop_menu = OptionMenu(self.root, self.var,  "replace regex", "prepend line", \
        "selective move", "custom action", "sort files by ctime", command = self.WhatYouWant)
    self.drop_menu.grid(row=0, column=0)
    global callback_1
    self.button_1=Button(self.root, text='Next', command=self.callback_1).grid(row=1, column=0)
    self.root.mainloop()
    
  def WhatYouWant(self, event):
    global chosen_option
    self.chosen_option = self.var.get()
    
  def callback_1(self):
    global chosen_option
    if self.chosen_option == 'replace regex':
      self.Str1='Global string replace'
      self.Str2='Enter full path to the directory'
      self.Str3='Enter regex to search in files'
      self.Str4='Proceed only filenames matching this regex'
      self.Str5='Enter replace string'
    elif self.chosen_option == 'prepend line':
      self.Str1='Global prepend line'
      self.Str2='Enter full path to the directory'
      self.Str3='Enter string to prepend in files'
      self.Str4='Proceed only filenames matching this regex'
      self.Str5=''
    elif self.chosen_option == 'selective move':
      self.Str1='Selective copy/move'
      self.Str2='Enter full path to the source directory'
      self.Str3='Enter full path to the destination directory'
      self.Str4='Proceed only filenames matching this regex'
      self.Str5=''
    elif self.chosen_option == 'custom action':
      self.Str1='Perform custom action'
      self.Str2='Enter full path to the source directory'
      self.Str3='Enter command line to be performed \
      (with full path to the executable)'
      self.Str4='Proceed only filenames matching this regex'
      self.Str5=''
    elif self.chosen_option == 'sort files by ctime':
      self.Str1='Sort files by creation time'
      self.Str2='Enter full path to the source directory'
      self.Str3='Proceed only filenames matching this regex'
      self.Str4=''
      self.Str5=''
    if self.chosen_option == 'default':
      Newindow=Error()
    else:
      Newindow=Maingui(self.Str1, self.Str2, self.Str3, self.Str4, self.Str5)
      
if __name__ == '__main__':
  a=Startgui()
