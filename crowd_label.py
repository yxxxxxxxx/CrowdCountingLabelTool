#-------------------------------------------------------------------------------
# Name:        Label tool 
# Purpose:     Label tool for Crowd Counting
# Author:      yangxu
# Created:     07/15/2018

#
#-------------------------------------------------------------------------------
from __future__ import division
from Tkinter import *
import tkMessageBox
from PIL import Image, ImageTk
import os
import glob
import random

# colors for the bboxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']
# image sizes for the examples
SIZE = 256, 256

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.pointfilename = ''
        self.tkimg = None

        # initialize point array
        self.POINTS = {}
        self.POINTS['click'] = 0
        self.POINTS['x'], self.POINTS['y'] = [], []
        self.POINTS['ID'] = []

        self.hl = None
        self.vl = None
        # reference to Points
        self.pointlist = []
        self.pointIdList = []

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text = "Image Dir:")
        self.label.grid(row = 0, column = 0, sticky = E)
        self.entry = Entry(self.frame)
        self.entry.grid(row = 0, column = 1, sticky = W+E)
        self.ldBtn = Button(self.frame, text = "Load", command = self.loadDir)
        self.ldBtn.grid(row = 0, column = 2, sticky = W+E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        # self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<BackSpace>", self.cancelPoint)
        self.parent.bind("a", self.prevImage) # press 'a' to go backforward
        self.parent.bind("d", self.nextImage) # press 'd' to go forward
        self.mainPanel.grid(row = 1, column = 1, rowspan = 4, sticky = W+N)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Points:')
        self.lb1.grid(row = 1, column = 2,  sticky = W+N)
        self.pointlistbox = Listbox(self.frame, width = 22, height = 12)
        self.pointlistbox.grid(row = 2, column = 2, sticky = N)
        self.btnDel = Button(self.frame, text = 'Delete', command = self.DelPoint)
        self.btnDel.grid(row = 3, column = 2, sticky = W+E+N)
        # self.btnDel = Button(self.frame, text = 'Delete', command = self.delBBox)
        # self.btnDel.grid(row = 3, column = 2, sticky = W+E+N)
        # self.btnClear = Button(self.frame, text = 'ClearAll', command = self.clearBBox)
        # self.btnClear.grid(row = 4, column = 2, sticky = W+E+N)


        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 5, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width = 10, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width = 10, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)

        # example pannel for illustration
        self.egPanel = Frame(self.frame, border = 10)
        self.egPanel.grid(row = 1, column = 0, rowspan = 5, sticky = N)
        self.tmpLabel2 = Label(self.egPanel, text = "Examples:")
        self.tmpLabel2.pack(side = TOP, pady = 5)
        self.egLabels = []
        for i in range(3):
            self.egLabels.append(Label(self.egPanel))
            self.egLabels[-1].pack(side = TOP)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

        self.ratio = 1.

        # for debugging
##        self.setImage()
##        self.loadDir()

    def loadDir(self, dbg = False):
        if not dbg:
            s = self.entry.get()
            self.parent.focus()
            self.category = int(s)
        else:
            s = r'D:\workspace\python\labelGUI'
##        if not os.path.isdir(s):
##            tkMessageBox.showerror("Error!", message = "The specified dir doesn't exist!")
##            return
        # get image list
        self.imageDir = os.path.join(r'./Images', '%03d' %(self.category))
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.bmp'))
        self.imageList.extend(glob.glob(os.path.join(self.imageDir, '*.jpg')))
        self.imageList.extend(glob.glob(os.path.join(self.imageDir, '*.JPEG')))
        self.imageList.extend(glob.glob(os.path.join(self.imageDir, '*.jpeg')))
        self.imageList.sort() 
        if len(self.imageList) == 0:
            print('No .JPEG images found in the specified dir!')
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

         # set up output dir
        self.outDir = os.path.join(r'./Labels', '%03d' %(self.category))
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)
        self.loadImage()
        print('%d images loaded from %s' %(self.total, s))

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(imagepath)
        self.ratio = 1200./max(self.img.size[0],self.img.size[1])
        self.img = self.img.resize((int(self.img.size[0]*self.ratio), int(self.img.size[1]*self.ratio)), Image.ANTIALIAS)

        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width = self.tkimg.width() , height = self.tkimg.height())
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))

        # load labels
        self.clearPoints()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        pointlabelname = self.imagename + '_points' + '.txt'
        self.pointfilename = os.path.join(self.outDir, pointlabelname)
        point_cnt = 0
        if os.path.exists(self.pointfilename):
            with open(self.pointfilename) as f2:
                for (i, line) in enumerate(f2):
                    if i == 0:
                        point_cnt = int(line.strip())
                        continue
                    tmp = [int(t.strip()) for t in line.split()]
                    self.pointlist.append((map(lambda x:int(x*self.ratio),tmp[0:2])[0], map(lambda x:int(x*self.ratio),tmp[0:2])[1]))
                    tmpId = []
                    tmpId.append(self.mainPanel.create_line(tmp[0]*self.ratio - 1 ,tmp[1]*self.ratio - 1, tmp[0]*self.ratio + 1, tmp[1]*self.ratio + 1, width=2, fill = 'red'))#,outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                    self.pointIdList.append(tmpId)
                    self.pointlistbox.insert(END, '(%d, %d)' %(int(tmp[0]*self.ratio), int(tmp[1]*self.ratio)))
                    #self.pointlistbox.itemconfig(len(self.pointIdList) - 1)

    def saveImage(self):
        with open(self.pointfilename, 'w') as f2:
            f2.write('%d\n' %len(self.pointlist))
            for point in self.pointlist:
                tmp_point = map(lambda x:int(x/self.ratio) , point)
                f2.write(' '.join(map(str, tmp_point)))
                f2.write(' ')
                f2.write('\n')
        print('Image No. %d saved' %(self.cur))


    def mouseClick(self, event):
        self.POINTS['click'] += 1
        self.POINTS['x'].append(event.x)
        self.POINTS['y'].append(event.y)
        self.POINTS['ID'].append(self.mainPanel.create_line(event.x - 1, event.y - 1, event.x + 1, event.y + 1, width = 4, fill = 'red'))
        self.pointIdList.append([self.POINTS['ID'][-1]])
        self.pointlistbox.insert(END, '(%d, %d)' %(event.x, event.y))
        #self.pointlistbox.itemconfig(len(self.pointIdList) - 1)

    # def mouseMove(self, event):
    #     self.disp.config(text = 'x: %d, y: %d' %(event.x, event.y))
    #     if self.tkimg:
    #         if self.hl:
    #             self.mainPanel.delete(self.hl)
    #         self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2, fill = 'white')
    #         if self.vl:
    #             self.mainPanel.delete(self.vl)
    #         self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2, fill = 'white')

    def cancelPoint(self, evet):
        if self.POINTS['click'] == 0:
            return
        self.POINTS['click'] -= 1
        self.POINTS['x'].pop()
        self.POINTS['y'].pop()
        self.mainPanel.delete(self.POINTS['ID'][-1])
        self.pointlistbox.delete(END)
        self.POINTS['ID'].pop()

    def DelPoint(self):
        sel = self.pointlistbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        for i in range(len(self.pointIdList[idx])):
            self.mainPanel.delete(self.pointIdList[idx][i])
        self.pointlistbox.delete(idx)
        self.pointIdList.pop(idx)
        if len(self.pointlist) == 0:
            return
        self.pointlist.pop(idx)
        if len(self.POINTS['x']) == 0:
            return
        self.POINTS['x'].pop(idx)
        self.POINTS['y'].pop(idx)



    def clearPoints(self):
        for idx in range(len(self.pointIdList)):
            for i in range(len(self.pointIdList[idx])):
                self.mainPanel.delete(self.pointIdList[idx][i])
        self.pointlistbox.delete(0, len(self.pointlist))
        self.pointIdList = []
        self.pointlist = []

    def prevImage(self, event = None):
        self.pointlist.extend(zip(self.POINTS['x'], self.POINTS['y']))
        self.saveImage()
        self.POINTS['click'] = 0
        self.POINTS['x'] = []
        self.POINTS['y'] = []
        self.POINTS['ID'] = []
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()


    def nextImage(self, event = None):
        self.pointlist.extend(zip(self.POINTS['x'], self.POINTS['y']))
        self.saveImage()
        self.POINTS['click'] = 0
        self.POINTS['x'] = []
        self.POINTS['y'] = []
        self.POINTS['ID'] = []
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

##    def setImage(self, imagepath = r'test2.png'):
##        self.img = Image.open(imagepath)
##        self.tkimg = ImageTk.PhotoImage(self.img)
##        self.mainPanel.config(width = self.tkimg.width())
##        self.mainPanel.config(height = self.tkimg.height())
##        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width =  True, height = True)
    root.mainloop()
