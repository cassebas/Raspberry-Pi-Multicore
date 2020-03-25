import click
import os
from os.path import basename, isfile, join
import subprocess
from subprocess import CalledProcessError
import numpy as np
import pandas as pd
import re
import time
from enum import Enum
import curses
from curses import wrapper
import signal
import windows


benchmarks = ['malardalenbsort100',
              'malardalenedn',
              'lineararrayaccess',
              'randomarrayaccess']


class Fields(Enum):
    CONFIG = 2
    DASSIGN = 3
    DISABLE_CACHE = 4
    NO_CACHE_MGMT = 5
    FILENAME_PREFIX = 6


class Compile:
    def __init__(self, outputwin):
        self.outputwin = outputwin
        self.target_dir = 'xRTOS_MMU_SEMAPHORE'
        self.scriptdir = os.getcwd()
        self.working_dir = self.scriptdir + '/../' + self.target_dir
        self.myenv = dict(os.environ, BENCHMARK_CONFIG='-DBENCHMARK_CONFIG_M4')
        self.makecleancmd = ['make', 'clean']
        self.makeinstallcmd = ['make', 'install']

    def compile(self):
        self.outputwin.log_message('working_dir={}'.format(self.working_dir))
        os.chdir(self.working_dir)
        try:
            cp = subprocess.run(self.makecleancmd,
                                check=True,
                                capture_output=True,
                                text=True,
                                env=self.myenv)
            self.outputwin.log_message(cp.stdout)
            cp = subprocess.run(self.makeinstallcmd,
                                check=True,
                                capture_output=True,
                                text=True,
                                env=self.myenv)
            text = cp.stdout.split('\n')
            for line in text:
                self.outputwin.log_message(line)
        except CalledProcessError:
            self.outputwin.log_message('Compilation subprocess resulted in an error!')

        os.chdir(self.scriptdir)



class Putty:
    def __init__(self, window):
        self.window = window
        self.pid = -1
        self.logfile = ''
        self.path = 'output'

    def set_filename(self):
        curses.echo()
        (y, x) = self.window.get_window().getyx()
        self.window.get_window().addstr('Filename: ')
        filename = self.window.get_window().getstr().decode()
        self.logfile = join(self.path, filename)
        curses.noecho()
        self.window.get_window().move(y, x)
        self.window.get_window().clrtobot()
        self.window.get_window().box()
        self.window.write_status('Output filename set to {}'.format(self.logfile))

    def set_path(self, path):
        self.path = path

    def start(self):
        if self.pid == -1:
            # ok process was not started yet, start now
            self.window.write_status('Starting putty..')
            time.sleep(1)
            self.pid = os.spawnlp(os.P_NOWAIT,
                                  'putty',
                                  'putty',
                                  '/dev/ttyUSB0',
                                  '-serial',
                                  '-sercfg',
                                  '115200,8,n,1,N',
                                  '-log',
                                  self.logfile)
            self.window.write_status('Process id of putty is {}\n'.format(self.pid))
        else:
            # putty already active
            self.window.write_status('Putty is already running, pid={}'.format(self.pid))

    def stop(self):
        if self.pid != -1:
            # process was started alright, let's kill it
            self.window.write_status('Stopping putty..')
            time.sleep(1)
            os.kill(self.pid, signal.SIGKILL)
            self.pid = -1
            self.window.write_status('Putty has been stopped.')
        else:
            self.window.write_status('Putty was not running, cannot stop putty.')


flds = {
    Fields.CONFIG: 'configuration of cores',
    Fields.DASSIGN: 'data assignment',
    Fields.DISABLE_CACHE: 'disable cache',
    Fields.NO_CACHE_MGMT: 'no cache management',
    Fields.FILENAME_PREFIX: 'filename prefix',
}


def print_experiment(window, idx, row):
    window.move(1, 2)
    window.addstr('Next up experiment number {} with these settings:'.format(idx+1))
    window.move(2, 2)
    window.addstr('Configuration of cores: {}'.format(row[flds[Fields.CONFIG]]))
    window.move(3, 2)
    window.addstr('Data assignment: {}'.format(row[flds[Fields.DASSIGN]]))
    window.move(4, 2)
    window.addstr('Disable cache: {}'.format(row[flds[Fields.DISABLE_CACHE]]))
    window.move(5, 2)
    window.addstr('No cache management: {}'.format(row[flds[Fields.NO_CACHE_MGMT]]))
    window.move(6, 2)
    window.addstr('Filename prefix: {}'.format(row[flds[Fields.FILENAME_PREFIX]]))
    window.refresh()


def menu_input(window):
    window.move(1, 2)
    window.addstr('Menu:')
    window.move(2, 2)
    window.addstr(' [f] Set filename for output')
    window.move(3, 2)
    window.addstr(' [c] Compile/build experiment')
    window.move(4, 2)
    window.addstr(' [n] Next experiment')
    window.move(5, 2)
    window.addstr(' [p] Start putty')
    window.move(6, 2)
    window.addstr(' [s] Stop putty')
    window.move(7, 2)
    window.addstr(' [q] Quit application')
    window.move(8, 2)
    window.addstr(' ---> ')
    return window.getch()
    # return window.getkey()


def do_experiments(stdscr, infile, workdir):
    uicomp = windows.UIComponents()
    menuwin = uicomp.get_menuwin()
    expwin = uicomp.get_experimentwin()
    outputwin = uicomp.get_outputwin()
    uicomp.refresh()

    putty = Putty(menuwin)
    comp = Compile(outputwin)

    run = True
    while run:
        expwin.write_status('Processing input file {}.'.format(infile))
        time.sleep(0.5)
        df = pd.read_excel(infile)
        expwin.write_status('Input file {} processed.'.format(infile))
        time.sleep(1.0)

        for idx, row in df.iterrows():
            uicomp.clear_status()
            compiled = False
            do_next = False
            if run is True:
                while not do_next:
                    print_experiment(expwin.get_window(), idx, row)
                    key = menu_input(menuwin.get_window())

                    if key == ord('q'):
                        run = False
                        do_next = True
                        menuwin.write_status('Stopping..')
                        time.sleep(0.5)
                        menuwin.write_status('Stopping.. bye now!')
                        time.sleep(1)
                    elif key == ord('f'):
                        # Set output file
                        putty.set_filename()
                    elif key == ord('c'):
                        # compile this experiment
                        menuwin.write_status('Compiling experiment')
                        comp.compile()
                        # time.sleep(1)
                        menuwin.write_status('Compilation done.')
                        compiled = True
                    elif key == ord('n'):
                        # continue with next experiment
                        outputwin.log_message('Next experiment selected')
                        do_next = True
                    elif key == ord('p'):
                        # start putty
                        if compiled is False:
                            # first compile
                            menuwin.write_status('You need to compile this experiment first!')
                            time.sleep(2)
                            menuwin.write_status('')
                        else:
                            menuwin.write_status('Starting putty now.')
                            putty.start()
                            menuwin.write_status('Putty has been started.')
                    elif key == ord('s'):
                        # stop putty
                        putty.stop()
                    elif key == curses.KEY_RESIZE:
                        uicomp.refresh()

    stdscr.erase()


@click.command()
@click.option('--input-file',
              required=True,
              help='Path and filename of the input Excel file.')
@click.option('--working-directory',
              default='../xRTOS_MMU_SEMAPHORE',
              help='Path of the working directory.')
def main(input_file, working_directory):
    if not isfile(input_file):
        print('Error: input file {}'.format(input_file), end=' ')
        print('does not exist!')
        exit(1)
    wrapper(do_experiments, input_file, working_directory)


if __name__ == "__main__":
    main()
