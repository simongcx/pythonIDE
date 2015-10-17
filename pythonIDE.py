#-------------------------------------------------------------------------------
# Name:        pythonIDE
# Purpose:     A very basic Python IDE for Python scripts, potentially a basis for a fuller IDE
#
# Author:      Simon Cox
#
# Created:     17/10/2015
# Copyright:   (c) Simon Cox 2015
# Licence:     Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#-------------------------------------------------------------------------------

import wx
import threading
import os
import subprocess
import sys


# Define result event
EVT_RESULT_ID = wx.NewId()

def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data

# Define finished event
EVT_FINISHED_ID = wx.NewId()

def EVT_FINISHED(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_FINISHED_ID, func)

class FinishedEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self):
        """Init Finished Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_FINISHED_ID)

class WorkerThread(threading.Thread):
    """Worker Thread Class."""
    def __init__(self, notify_window, process):
        """Init Worker Thread Class."""
        threading.Thread.__init__(self)
        self._notify_window = notify_window
        self.process = process
        self.start()

    def run(self):
        """Run Worker Thread."""
        while True:
            line = self.process.stdout.readline()
            if line != '':
                wx.PostEvent(self._notify_window, ResultEvent(line))
            else:
                break
        wx.PostEvent(self._notify_window, FinishedEvent())

    def abort(self):
        """abort worker thread."""
        # Method for use by main thread to signal an abort
        self.process.terminate()

class ScriptPanel(wx.Panel):

    def __init__(self, parent, path=None):

        wx.Panel.__init__(self, parent)

        EVT_RESULT(self,self.OnResult)
        EVT_FINISHED(self,self.OnFinished)

        self.InitUI()

        self.worker = None

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.path = path
        self.parent = parent

        if path:
            file = open(path, 'r')
            self.scripteditor.AppendText(file.read())
            file.close()

    def InitUI(self):

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.scripteditor = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.scripteditor.SetBackgroundColour('#ededed')
        vbox.Add(self.scripteditor, 1, wx.EXPAND | wx.ALL, 0)

        self.scriptoutput = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.scriptoutput.SetBackgroundColour('#ededed')
        vbox.Add(self.scriptoutput, 1, wx.EXPAND | wx.ALL, 0)

        self.SetSizer(vbox)

    def RunScript(self, event):
        """Start Computation."""
        # Trigger the worker thread unless it's already busy
        if not self.worker:

            if self.path:
                pythonfile = self.path
            else:
                tempfile = open('tempfile.py','w')
                tempfile.write(self.scripteditor.GetValue())
                tempfile.close()
                pythonfile = os.path.join(os.getcwd(), 'tempfile.py')

            process = subprocess.Popen([sys.executable,'-u',pythonfile, '2>&1'], stdout=subprocess.PIPE)

            self.worker = WorkerThread(self, process)

    def StopScript(self, event):
        """Stop Computation."""
        # Flag the worker thread to stop if running
        if self.worker:
            self.worker.abort()

    def OnResult(self, event):
        """Show Result status."""
        self.scriptoutput.AppendText(event.data)

    def OnFinished(self, event):
        self.worker = None

    def OnSave(self, event):
        print self.path
        if self.path:
            f = open(self.path, 'w')
            f.write(self.scripteditor.GetValue())
            f.close()
        else:
            self.OnSaveAs(event)

    def OnSaveAs(self, event):
        saveFileDialog = wx.FileDialog(self, "Save Python file", "", "", "Python files (*.py)|*.py", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if saveFileDialog.ShowModal() == wx.ID_CANCEL:
            return     # the user changed idea...

        f = open(saveFileDialog.GetPath(), 'w')
        f.write(self.scripteditor.GetValue())
        f.close()

        self.path = saveFileDialog.GetPath()
        self.parent.SetPageText(self.parent.GetSelection(),os.path.split(self.path)[1])

    def OnClose(self, event):
        if self.worker:
            self.worker.abort()
        self.parent.DeletePage(self.parent.GetSelection())


class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, None, title=title)


        # Here we create a panel and a notebook on the panel
        p = wx.Panel(self)
        self.notebook = wx.Notebook(p)

        # create the page windows as children of the notebook
        page1 = ScriptPanel(self.notebook)
        page2 = ScriptPanel(self.notebook)
        page3 = ScriptPanel(self.notebook)

        # add the pages to the notebook with the label to show on the tab
        self.notebook.AddPage(page1, "Page 1")
        self.notebook.AddPage(page2, "Page 2")
        self.notebook.AddPage(page3, "Page 3")

        # finally, put the notebook in a sizer for the panel to manage
        # the layout
        sizer = wx.BoxSizer()
        sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL)
        p.SetSizer(sizer)

        self.createMenubar()
        self.createToolbar()

        self.Maximize(True)
        self.Show()

    def createMenubar(self):
        menubar = wx.MenuBar()

        fileMenu = wx.Menu()

        fitem1 = fileMenu.Append(wx.ID_OPEN, 'Open', 'Open script')
        self.Bind(wx.EVT_MENU, self.OnOpen, fitem1)

        fitem2 = fileMenu.Append(wx.ID_SAVE, 'Save', 'Save script')
        self.Bind(wx.EVT_MENU, self.OnSave, fitem2)

        fitem3 = fileMenu.Append(wx.ID_SAVEAS, 'Save as', 'Save script as')
        self.Bind(wx.EVT_MENU, self.OnSaveAs, fitem3)

        fitem4 = fileMenu.Append(wx.ID_CLOSE, 'Close', 'Close script')
        self.Bind(wx.EVT_MENU, self.OnClose, fitem4)

        fitem5 = fileMenu.Append(wx.ID_NEW, 'New', 'New script')
        self.Bind(wx.EVT_MENU, self.CreateTab, fitem5)

        fitem6 = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        self.Bind(wx.EVT_MENU, self.OnQuit, fitem6)

        runMenu = wx.Menu()

        ritem1 = runMenu.Append(wx.ID_ANY, 'Run', 'Run script')
        self.Bind(wx.EVT_MENU, self.RunScript, ritem1)

        ritem2 = runMenu.Append(wx.ID_ANY, 'Stop', 'Stop script')
        self.Bind(wx.EVT_MENU, self.StopScript, ritem2)

        helpMenu = wx.Menu()

        hitem1 = helpMenu.Append(wx.ID_ANY, 'About', 'About Python IDE')
        self.Bind(wx.EVT_MENU, self.OnAbout, hitem1)

        menubar.Append(fileMenu, '&File')
        menubar.Append(runMenu, '&Run')
        menubar.Append(helpMenu, '&Help')
        self.SetMenuBar(menubar)




    def createToolbar(self):
        """
        Create a toolbar.
        """

        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((16,16))  # sets icon size

        # Use wx.ArtProvider for default icons
        go_ico = wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR, (16,16))
        goTool = self.toolbar.AddSimpleTool(wx.ID_ANY, go_ico, "Run", "Runs the current file")
        self.Bind(wx.EVT_MENU, self.RunScript, goTool)

        stop_ico = wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_TOOLBAR, (16,16))
        stopTool = self.toolbar.AddSimpleTool(wx.ID_ANY, stop_ico, "Stop", "Stops the current execution")
        self.Bind(wx.EVT_MENU, self.StopScript, stopTool)

        self.toolbar.AddSeparator()

        open_ico = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, (16,16))
        openTool = self.toolbar.AddSimpleTool(wx.ID_ANY, open_ico, "Open", "Open a file")
        self.Bind(wx.EVT_TOOL, self.OnOpen, openTool)

        save_ico = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, (16,16))
        saveTool = self.toolbar.AddSimpleTool(wx.ID_ANY, save_ico, "Save", "")
        self.Bind(wx.EVT_TOOL, self.OnSave, saveTool)

        saveas_ico = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR, (16,16))
        saveasTool = self.toolbar.AddSimpleTool(wx.ID_ANY, saveas_ico, "Save as", "")
        self.Bind(wx.EVT_TOOL, self.OnSaveAs, saveasTool)

        close_ico = wx.ArtProvider.GetBitmap(wx.ART_QUIT, wx.ART_TOOLBAR, (16,16))
        closeTool = self.toolbar.AddSimpleTool(wx.ID_ANY, close_ico, "Close", "")
        self.Bind(wx.EVT_TOOL, self.OnClose, closeTool)

        new_ico = wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR, (16,16))
        newTool = self.toolbar.AddSimpleTool(wx.ID_ANY, new_ico, "Close", "")
        self.Bind(wx.EVT_TOOL, self.CreateTab, newTool)

        # This basically shows the toolbar
        self.toolbar.Realize()


    def RunScript(self, event):
        if len(self.notebook.Children):
            self.notebook.Children[self.notebook.GetSelection()].RunScript(event)

    def StopScript(self, event):
        if len(self.notebook.Children):
            self.notebook.Children[self.notebook.GetSelection()].StopScript(event)

    def OnOpen(self, event):
        openFileDialog = wx.FileDialog(self, "Open Python file", "", "", "Python files (*.py)|*.py", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if openFileDialog.ShowModal() == wx.ID_CANCEL:
            return

        self.CreateTab(event, openFileDialog.GetPath())

    def OnSave(self, event):
        if len(self.notebook.Children):
            self.notebook.Children[self.notebook.GetSelection()].OnSave(event)

    def OnSaveAs(self, event):
        if len(self.notebook.Children):
            self.notebook.Children[self.notebook.GetSelection()].OnSaveAs(event)

    def OnClose(self, event):
        if len(self.notebook.Children):
            self.notebook.Children[self.notebook.GetSelection()].OnClose(event)

    def CreateTab(self, event, path=None):
        page1 = ScriptPanel(self.notebook, path=path)
        if path:
            tabname = os.path.split(path)[1]
        else:
            tabname = "New tab"
        self.notebook.AddPage(page1, tabname)

        self.notebook.ChangeSelection(len(self.notebook.Children) - 1)

    def OnAbout(self, event):
        message = """Name: pythonIDE
Purpose: A very basic Python IDE for Python scripts, potentially a basis for a fuller IDE

Author: Simon Cox

Created: 17th October 2015
Copyright: (c) Simon Cox 2015
Licence: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)

With thanks to: Everyone who works on open source and shares their code and knowledge online"""
        dlg = wx.MessageDialog(self, message, 'About', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnQuit(self, event):
        self.Close()


if __name__ == '__main__':

    app = wx.App()
    MainFrame(None, title='pythonIDE')
    app.MainLoop()