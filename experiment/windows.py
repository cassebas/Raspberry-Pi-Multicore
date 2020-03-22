from os.path import basename, isfile, join
import pandas as pd
import curses
import time
from curses import wrapper
from enum import Enum


class UIComponents:
    def __init__(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        self.menuwin = MenuWin(self.stdscr)
        self.experimentwin = ExperimentWin(self.stdscr)
        self.scrollwin = ScrollWin(self.stdscr)
        self.refresh()

    def refresh(self):
        self.stdscr.erase()
        (nlines, ncols) = self.stdscr.getmaxyx()
        self.menuwin.draw_window(nlines, ncols, True)
        self.experimentwin.draw_window(nlines, ncols, True)
        self.scrollwin.draw_window(nlines, ncols, False)
        self.scrollwin.addstr('refreshed maxy={} maxx={}'.format(nlines, ncols))

    def get_menuwin(self):
        return self.menuwin

    def get_experimentwin(self):
        return self.experimentwin

    def get_scrollwin(self):
        return self.scrollwin


class Win:
    def draw_window(self, nlines, ncols, erase):
        if erase is True:
            self.win.erase()
            pass
        (self.nlines, self.myncols) = self.get_size(nlines, ncols)
        (self.ypos, self.xpos) = self.get_position(nlines, ncols)
        self.win.resize(self.nlines, self.ncols)
        try:
            self.win.mvwin(self.ypos, self.xpos)
        except curses.error:
            pass
        self.win.box()
        self.win.refresh()

    def new_window(self):
        (ymax, xmax) = self.stdscr.getmaxyx()
        (self.nlines, self.ncols) = self.get_size(ymax, xmax)
        (self.ypos, self.xpos) = self.get_position(ymax, xmax)
        self.win = curses.newwin(self.nlines, self.ncols, self.ypos, self.xpos)
        self.win.scrollok(self.scrollok)

    def get_window(self):
        return self.win

    def get_size(self, nlines, ncols):
        mynlines = nlines // self.divlines + (nlines % self.divlines) * self.ycoord
        myncols = ncols//self.divcols + (ncols % self.divcols) * self.xcoord
        return (mynlines, myncols)

    def get_position(self, nlines, ncols):
        (mynlines, myncols) = self.get_size(nlines, ncols)
        myypos = mynlines * self.ycoord - (nlines % self.divlines) * self.ycoord
        if myypos < 0:
            myypos = 0
        myxpos = myncols * self.xcoord - (ncols % self.divcols) * self.xcoord
        if myxpos < 0:
            myxpos = 0
        return (myypos, myxpos)

    def write_status(self, string):
        (y, x) = (self.nlines - 2, 2)
        try:
            self.win.move(y, x)
            self.win.clrtoeol()
            self.win.box()
            self.win.addstr(string)
            self.win.refresh()
        except curses.error:
            pass


class MenuWin(Win):
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.title = "Menu window"
        self.ycoord = 0
        self.xcoord = 0
        self.divlines = 2
        self.divcols = 2
        self.scrollok = True
        self.new_window()


class ExperimentWin(Win):
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.title = "Experiment window"
        self.ycoord = 0
        self.xcoord = 1
        self.divlines = 2
        self.divcols = 2
        self.scrollok = True
        self.new_window()


class ScrollWin(Win):
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.title = "Scroll window"
        self.ycoord = 1
        self.xcoord = 0
        self.divlines = 2
        self.divcols = 1
        self.scrollok = False
        self.new_window()

    def addstr(self, str):
        try:
            (y, x) = self.win.getyx()
            if y < 1:
                y = 1
            if y >= self.nlines-1:
                self.win.scroll()
                y -= 1
            self.win.move(y, 1)
            self.win.addstr('nlines={} ncols={}'.format(self.nlines,
                                                        self.ncols))
            self.win.addstr('y={} x={} str={}'.format(self.ypos, self.xpos, str))
        except curses.error:
            pass
