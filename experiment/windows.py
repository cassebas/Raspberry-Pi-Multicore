from os.path import basename, isfile, join
import pandas as pd
import curses
import time
from curses import wrapper
from enum import Enum
from abc import ABC


class UIComponents:
    def __init__(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        self.menuwin = MenuWin(self.stdscr)
        self.experimentwin = ExperimentWin(self.stdscr)
        self.outputwin = OutputWin(self.stdscr)
        self.refresh()

    def refresh(self):
        self.stdscr.erase()
        (nlines, ncols) = self.stdscr.getmaxyx()
        self.menuwin.draw_window(nlines, ncols, True)
        self.experimentwin.draw_window(nlines, ncols, True)
        self.outputwin.draw_window(nlines, ncols, False)

    def clear_status(self):
        self.menuwin.write_status('')
        self.experimentwin.write_status('')

    def get_menuwin(self):
        return self.menuwin

    def get_experimentwin(self):
        return self.experimentwin

    def get_outputwin(self):
        return self.outputwin


class Win(ABC):
    def draw_window(self, nlines, ncols, erase):
        if erase is True:
            self.win.erase()
        (self.nlines, self.ncols) = self.get_size(nlines, ncols)
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
        self.win.idlok(self.scrollok)

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
        # A window that scrolls does not have a status line
        if not self.scrollok:
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
        self.scrollok = False
        self.new_window()


class ExperimentWin(Win):
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.title = "Experiment window"
        self.ycoord = 0
        self.xcoord = 1
        self.divlines = 2
        self.divcols = 2
        self.scrollok = False
        self.new_window()


class OutputWin(Win):
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.title = "Scroll window"
        self.ycoord = 1
        self.xcoord = 0
        self.divlines = 2
        self.divcols = 1
        self.scrollok = True
        self.new_window()
        self.debug = 0

    def log_message(self, str):
        # plines: number of printable lines (-2 because of the box)
        plines = self.nlines - 2

        self.debug += 1
        try:
            (y, x) = self.win.getyx()
            line_len = len(str) // self.ncols + 1
            if y < 1:
                y = 1

            scroll = 0
            if y + line_len >= plines:
                # we are too far, must scroll to make space
                scroll = y + line_len - plines
                self.win.scroll(scroll)
                y -= scroll

            # clear the lines where we are going to print to
            for i in range(line_len+1):
                self.win.move(y+i, 1)
                self.win.clrtoeol()

            # and start at the first line where we are going to print
            self.win.move(y, 1)

            # move cursor to the next line for the next print statement
            if y + line_len <= plines:
                ny = y + line_len
            else:
                ny = plines

            # possibly remove newline at end of string
            str = str.rstrip()
            self.win.addstr(str)

            self.win.move(ny, 1)

            self.win.box()
            self.win.refresh()
        except curses.error:
            pass
