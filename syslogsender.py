#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
####################################
# Syslog sender 
# Author: Oleg Fajans, Bridge-Quest Labs Inc.
####################################
#

import socket, tkFileDialog, time, threading, Queue, sys, os, pickle
from Tkinter import *
from collections import deque

PickleFile='settings.pickle'



class Processor:
  def __init__(self):
    self.Q = Queue.Queue()
    self.Act = deque()
    self.SockDictTCP={'IPv4': socket.socket(socket.AF_INET, socket.SOCK_STREAM), 'IPv6': socket.socket(socket.AF_INET6, socket.SOCK_STREAM)}
    self.SockDictUDP={'IPv4': socket.socket(socket.AF_INET, socket.SOCK_DGRAM), 'IPv6': socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)}


  def send_events(self, ThreadEvent, File, Destination, IPVersion, Protocol, Port, EPS, Loop, Header, Count):
    Interval=1/EPS
    try:
      with open(File, 'r') as F:
        LinesSent=0
        start = time.time()
        if Protocol == 'TCP':
            s=SockDictTCP[IPVersion]
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((Destination, int(Port)))
            g=s.makefile()
            while True:
              if Header:
                a=F.readline()
                if not a and Loop:
                  F.seek(0)
                  a=F.readline()
                elif not a:
                  del g
                  s.close()
                  ThreadEvent.clear()
                  break
                a = time.asctime() + ' ' + Header+' '+a
                g.write(a)
                g.flush()
                LinesSent+=1
                self.Q.put(1)
                time.sleep(Interval)
                if not ThreadEvent.isSet() or Count and str(self.Q.qsize()) == str(Count): # Do not change this! Comparison of integers here always return False. I wish I knew why
                  ThreadEvent.clear()
                  del g
                  s.close()
#                s.shutdown('SHUT_WR')
                  break
              else: # No header
                a=F.readline()
                if not a and Loop:
                  F.seek(0)
                  a=F.readline()
                elif not a:
                  del g
                  s.close()
                  ThreadEvent.clear()
                  break
                g.write(a)
                g.flush()
                LinesSent+=1
                self.Q.put(1)
                time.sleep(Interval)
                if not ThreadEvent.isSet() or Count and str(self.Q.qsize()) == str(Count): # Do not change this! Comparison of integers here always return False. I wish I knew why
                  ThreadEvent.clear()
                  del g
                  s.close()
#                        s.shutdown('SHUT_WR')
                  break
    except IOError as X:
      ThreadEvent.clear()
      if len(X.args) == 2:
        if X.args[0] in (106, 9):
          h=ErrorMessage('Error', X.args[1]+'. If you are sending file via TCP, try relaunching '+os.path.basename(sys.argv[0]).split('.')[0])
        else:
          h=ErrorMessage('Error', X.args[1])
      else:
        h=ErrorMessage('Error', X.args[0])
    except ValueError as Y:
      ThreadEvent.clear()
      if len(Y.args) == 2:
        h=ErrorMessage('Error', Y.args[1]+' or you did not supply destination host name')
      else:
        h=ErrorMessage('Error', 'Please, supply port number')
    except OverflowError as Z:
      ThreadEvent.clear()
      h=ErrorMessage('Error', Z.args[0])
    finally:
      if Protocol == 'UDP':
        end = time.time()
        elapsed = end - start
        RealEPS=self.Q.qsize()/elapsed
        self.Act.append(RealEPS)
      else:
        pass
    
############################
# Gui part
############################

class Basic():
  def Destroy(self):
    self.root.destroy()

class ErrorMessage(Basic):
  def __init__(self, message1, message2):
    self.root=Tk()
    self.root.title(message1)
    self.Label = Label(self.root, text=message2).grid(row=0, column=0)
    self.OKButton=Button(self.root, text='OK', command=self.Destroy).grid(column=0, row=1)  
    self.root.mainloop()

class Maingui(Basic):
  def __init__(self):
    try:
      with open(PickleFile, 'r') as self.PF:
        self.Settings = pickle.load(self.PF)
    except IOError:
      self.Settings = ['', '', '', 'IPv4', 'UDP', 1, '', '', '']
      pass 
    self.processor = Processor()
    self.Trigger=threading.Event()
    self.root=Tk()
    self.root.title('Syslog event sender')
    self.Input1 = Entry(self.root, bg="white")
    self.Input1.grid(row=0, column=1)
    self.Input1.insert(0, self.Settings[0])
    self.Input1Label = Label(self.root, text='Logfile you want to send').grid(row=0, column=0, sticky = E)
    self.CheckVar1 = IntVar()
    self.CheckVar2 = IntVar()
    self.Chk1 = Checkbutton(self.root, variable=self.CheckVar1, onvalue = 1, offvalue = 0, text = 'Send in a loop').grid(row=0, column=3, sticky = W)
    self.Chk2 = Checkbutton(self.root, variable=self.CheckVar2, onvalue = 1, offvalue = 0, text = 'Add syslog header', command=self.Warn).grid(row=3, column=3, sticky = SW)
    self.BrowseDst=Button(self.root, text = 'Browse', command = self.BrowseSRC).grid(row=0, column=2, sticky = W)
    self.Input2 = Entry(self.root, bg="white")
    self.Input2.grid(row=1, column=1)
    self.Input2.insert(0, self.Settings[1])
    self.Input2Label=Label(self.root, text='Target hostname or IP').grid(row=1, column=0, sticky = E)
    self.Input3 = Entry(self.root, bg="white", width = 5)
    self.Input3.grid(row=1, column=3, sticky = W)
    self.Input3.insert(0, self.Settings[2])
    self.Input3Label=Label(self.root, text='Port').grid(row=1, column=2, sticky = E)
    self.var0 = StringVar(self.root)
    self.var0.set(self.Settings[3])
    self.drop_menu1 = OptionMenu(self.root, self.var0,  "IPv4", "IPv6").grid(row=2, column=1, sticky = W)
    self.DropLabel1 = Label(self.root, text='Network protocol version').grid(row=2, column=0, sticky = E)
    self.var1 = StringVar(self.root)
    self.var1.set(self.Settings[4])
    self.drop_menu2 = OptionMenu(self.root, self.var1,  "UDP", "TCP").grid(row=2, column=3, sticky = W)
    self.DropLabel2 = Label(self.root, text='Transport protocol').grid(row=2, column=2, sticky = E)
    self.var2 = DoubleVar()
    self.scale = Scale(self.root, variable = self.var2, from_ = 1, to_ = 5000, orient=HORIZONTAL).grid(row=3, column=1, sticky = W, columnspan = 3, ipadx=80)
#    self.scale.set(self.Settings[5])
    self.ScaleLabel = Label(self.root, text='Events Per Second').grid(row=3, column=0, sticky = E)
    self.Input4 = Entry(self.root, bg="white", width = 7)
    self.Input4.insert(0, "")
    self.Input4.grid(row=4, column=1, sticky = W)
    self.Input4Label = Label(self.root, text='How many lines to send').grid(row=4, column=0, sticky = E)
    self.OKButton = Button(self.root, text="Send", bg='green', fg='black', bd=4, relief=RAISED, command = self.Send)
    self.OKButton.grid(row=4, column=3)
    self.CancelButton = Button(self.root, text="Stop", bg='red', fg='black', bd=4, command = self.Cancel, state=DISABLED)
    self.CancelButton.grid(row=4, column=2)
    self.SentBox = Label(self.root)
    self.SentBox.grid(row=5, column=1, sticky = W)
    self.SentboxLabel = Label(self.root, text = 'Events sent').grid(row=5, column=0, sticky = E)
    self.RealEps = Label(self.root)
    self.RealEps.grid(row=5, column=3, sticky = W)
    self.RealEpsLabel = Label(self.root, text = 'Actual EPS').grid(row=5, column=2, sticky = E)
    self.root.mainloop()
	
  def BrowseSRC(self):
    self.SrcFile=tkFileDialog.askopenfilename()
    self.Input1.insert(0, self.SrcFile)		
		
  def Send(self):
    self.CancelButton.config(state=NORMAL)
    self.OKButton.config(state=DISABLED)
    self.File = self.Input1.get()
    self.Target = self.Input2.get()
    self.Port = self.Input3.get()
    self.Version = self.var0.get()
    self.Proto = self.var1.get()
    self.Speed = self.var2.get()
    self.Count = self.Input4.get()
    self.HeaderInt = self.CheckVar2.get()
    self.Loop = self.CheckVar1.get()
    self.NumEvents = self.Count if self.Count else 0
    self.Header = socket.gethostname() + ' ' + os.path.basename(sys.argv[0]).split('.')[0] if self.HeaderInt else ''
    self.Trigger.set()
    self.Job = threading.Thread(target = self.processor.SendEvents, args = (self.Trigger, self.File, self.Target, self.Version, self.Proto, self.Port, self.Speed, self.Loop, self.Header, self.NumEvents))
    self.Controller = threading.Thread(target = self.JobController)
    self.Job.start()
    self.Controller.start()

  def Warn(self):
    self.HeaderInt = self.CheckVar2.get()
    if self.HeaderInt == 1:
      e=ErrorMessage('Warning', 'Please note: adding syslog header to each sent line slightly affects performance.\nPlease, adjust sending speed accordingly')

  def JobController(self):
    while True:
      time.sleep(1/self.Speed)
      self.SentBox.config(text=q.qsize())
      if self.Trigger.isSet():
        pass
      else:
        del self.Job
        self.Cancel()
        if self.Proto == 'UDP':
          self.RealEps.config(text=int(Act.pop()))
        else:
          pass
        break

  def Cancel(self):
    self.Trigger.clear()
    self.OKButton.config(state=NORMAL)
    self.CancelButton.config(state=DISABLED)
                
if __name__ == '__main__':
	a=Maingui()
