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
from threading import Thread
import serial


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
        self.makecleancmd = ['make', 'clean']
        self.makeinstallcmd = ['make', 'install']
        self.set_environment()
        self.set_compilation()

    def compile(self):
        self.outputwin.log_message('working_dir={}'.format(self.working_dir))
        os.chdir(self.working_dir)
        try:
            # do make clean to clean up previous makes
            cp = subprocess.run(self.makecleancmd,
                                check=True,
                                capture_output=True,
                                text=True,
                                env=self.myenv)
            self.outputwin.log_message(cp.stdout)

            # generate the benchmark_config.h file
            self.outputwin.log_message('writing benchmark_config.h')
            with open('benchmark_config.h', 'w') as outfile:
                subprocess.run(self.makeprepcmd,
                               stdout=outfile)

            # do the actual compilation
            self.outputwin.log_message('actual compilation')
            cp = subprocess.run(self.makeinstallcmd,
                                check=True,
                                capture_output=True,
                                text=True,
                                env=self.myenv)
            text = cp.stdout.split('\n')
            for line in text:
                self.outputwin.log_message(line)
        except (CalledProcessError, UnicodeDecodeError):
            self.outputwin.log_message('Compilation subprocess resulted ' +
                                       'in an error!')

        os.chdir(self.scriptdir)

    def set_environment(self):
        self.myenv = dict(os.environ,
                          BENCHMARK_CONFIG='-DBENCHMARK_CONFIG_M4')

    def set_compilation(self, config=None, dassign=None):
        if config is not None or dassign is not None:
            config_param = ''
            dassign_param = ''
            if config is not None:
                # The python process that runs m4 cannot handle a string
                # with quotes well, remove leading and trailing quotes.
                self.outputwin.log_message('config={}'.format(config))
                config = re.sub(r'^\'', '', config)
                config = re.sub(r'\'$', '', config)
                config_param = '-Dconfig=' + config
                self.outputwin.log_message('config={}'.format(config))
            if dassign is not None:
                # Same here, remove leading and trailing quotes.
                self.outputwin.log_message('dassign={}'.format(dassign))
                dassign = re.sub(r'^\'', '', dassign)
                dassign = re.sub(r'\'$', '', dassign)
                dassign_param = '-Ddassign=' + dassign
                self.outputwin.log_message('dassign={}'.format(dassign))

            self.makeprepcmd = ['m4',
                                config_param,
                                dassign_param,
                                'benchmark_config.m4']
        else:
            self.makeprepcmd = ['m4',
                                'benchmark_config.m4']


class Resetter(Thread):
    def __init__(self, logging, menuwin, outputwin):
        super(Resetter, self).__init__()
        self.logging = logging
        self.menuwin = menuwin
        self.outputwin = outputwin
        # default tty (can be changed in the application)
        self.tty = '/dev/ttyUSB0'
        self.serial = serial.Serial(self.tty, 115200)
        # Ok to reset?
        self.resetOK = False
        self.min_observations = 50
        self.last_iteration = -1
        # start/stop thread flag
        self.run_thread = False
        # timeout for not receiving data anymore (seconds)
        self.timeout = 120.0
        self.curtime = 0.0
        # number of seconds to sleep
        self.timeslice = 0.5

    def run(self):
        while self.run_thread is True:
            if self.resetOK is False:
                # Get number of log lines
                this_iteration = self.logging.get_iteration()
                if this_iteration > self.last_iteration:
                    # There is some progress, reset the curtime
                    self.curtime = 0
                    self.last_iteration = this_iteration
                    # Do we have enough observations?
                    if self.last_iteration > self.min_observations:
                        self.set_resetOK(True)
                else:
                    # check for timeout
                    self.curtime += self.timeslice
                    if int(self.curtime) % 10 == 0:
                        self.outputwin.log_message('Waiting {}'.format(self.curtime) +
                                                   ' secs and counting..')
                    if self.curtime > self.timeout:
                        self.set_resetOK(True)
            time.sleep(self.timeslice)

    def start_thread(self):
        self.run_thread = True
        self.start()

    def stop_thread(self):
        self.run_thread = False
        self.join()

    def get_resetOK(self):
        return self.resetOK

    def set_resetOK(self, reset):
        self.resetOK = reset
        if reset is True:
            # also reset the last_iteration back to default state
            self.last_iteration = -1

    def do_reset(self):
        if self.resetOK:
            self.serial.write('r'.encode())
            self.outputwin('Resetting the Raspberry Pi now.')

    def set_tty(self, name):
        curses.echo()
        (y, x) = self.menuwin.get_window().getyx()
        self.menuwin.get_window().addstr('TTY {}: '.format(name))
        tty = self.menuwin.get_window().getstr().decode()
        self.tty = tty
        self.serial = serial.Serial(tty, 115200)
        curses.noecho()
        self.menuwin.get_window().move(y, x)
        self.menuwin.get_window().clrtobot()
        self.menuwin.get_window().box()
        self.menuwin.write_status('TTY {} set to {}'.format(name, tty))


class Logging(Thread):
    def __init__(self, menuwin, outputwin):
        super(Logging, self).__init__()
        # default tty (can be changed in the application)
        self.tty = '/dev/ttyUSB1'
        # for the monitor that reads the log
        self.iteration = 0
        # start/stop thread flag
        self.run_thread = False
        self.serial = serial.Serial(self.tty, 115200)
        self.menuwin = menuwin
        self.outputwin = outputwin
        self.logfile = ''
        self.path = 'output'

    # Overridden from Thread.run()
    def run(self):
        i = 0
        while self.run_thread is True:
            line = self.serial.readline()
            i += 1
            if i % 100 == 0:
                self.outputwin.log_message(line)
            if len(self.logfile) > 0:
                with open(self.logfile, 'w') as outfile:
                    outfile.write(line)
            try:
                match = re.search(r'iteration: ([0-9]+)', line)
                if match:
                    iteration = match.group(1)
                    if iteration > self.iteration:
                        self.iteration = iteration
                else:
                    # oh oh, no match in received line
                    self.outputwin.log_message('no match in line {}'.format(line))
            except TypeError:
                self.outputwin_log_message('Caught TypeError')

    def start_thread(self):
        self.run_thread = True
        self.start()

    def stop_thread(self):
        self.run_thread = False
        self.join()

    def get_iteration(self):
        return self.iteration

    def set_filename(self):
        curses.echo()
        (y, x) = self.menuwin.get_window().getyx()
        self.menuwin.get_window().addstr('Filename: ')
        filename = self.menuwin.get_window().getstr().decode()
        self.logfile = join(self.path, filename)
        curses.noecho()
        self.menuwin.get_window().move(y, x)
        self.menuwin.get_window().clrtobot()
        self.menuwin.get_window().box()
        self.menuwin.write_status('Output filename set to {}'.format(self.logfile))

    def set_tty(self, name):
        curses.echo()
        (y, x) = self.menuwin.get_window().getyx()
        self.menuwin.get_window().addstr('TTY {}: '.format(name))
        tty = self.menuwin.get_window().getstr().decode()
        self.tty = tty
        self.serial = serial.Serial(tty, 115200)
        curses.noecho()
        self.menuwin.get_window().move(y, x)
        self.menuwin.get_window().clrtobot()
        self.menuwin.get_window().box()
        self.menuwin.write_status('TTY {} set to {}'.format(name, tty))

    def set_path(self, path):
        self.path = path


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
    window.addstr(' [l] Set TTY for Raspberry Pi logging')
    window.move(4, 2)
    window.addstr(' [r] Set TTY for Arduino resetter')
    window.move(5, 2)
    window.addstr(' [n] Next experiment')
    window.move(6, 2)
    window.addstr(' [q] Quit application')
    window.move(7, 2)
    window.addstr(' ---> ')
    return window.getch()


def do_experiments(stdscr, infile, workdir):
    uicomp = windows.UIComponents()
    menuwin = uicomp.get_menuwin()
    expwin = uicomp.get_experimentwin()
    outputwin = uicomp.get_outputwin()
    uicomp.refresh()

    comp = Compile(outputwin)
    logging = Logging(menuwin, outputwin)
    logging.start_thread()
    resetter = Resetter(logging, menuwin, outputwin)
    resetter.start_thread()

    expwin.write_status('Processing input file {}.'.format(infile))
    time.sleep(0.5)
    df = pd.read_excel(infile)
    expwin.write_status('Input file {} processed.'.format(infile))
    time.sleep(1.0)

    run = True
    do_reset = False
    for idx, row in df.iterrows():
        uicomp.clear_status()

        if run is True:
            # First compile this experiment
            menuwin.write_status('Compiling experiment')
            config = row['configuration of cores']
            dassign = row['data assignment']
            comp.set_compilation(config=config, dassign=dassign)
            comp.compile()
            menuwin.write_status('Compilation done.')

            do_next = False

            if do_reset is True:
                resetter.do_reset()
                resetter.set_resetOK(False)
                do_reset = False

            while not do_next:
                print_experiment(expwin.get_window(), idx, row)

                # check if the next experiment can be selected
                # automatically (this is the case when enough
                # log lines have been printed. Class Putty knows
                # this).
                if resetter.get_resetOK() is True:
                    # Oh! we can do the next experiment
                    do_reset = True
                    do_next = True
                    menuwin.write_status('Reset to next experiment..')
                    time.sleep(0.5)
                else:
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
                        logging.set_filename()
                    elif key == ord('t'):
                        # Set tty for logging
                        logging.set_tty('logging')
                    elif key == ord('T'):
                        # Set tty for arduino
                        resetter.set_tty('arduino')
                    elif key == ord('n'):
                        # manually continue with next experiment
                        outputwin.log_message('Next experiment selected' +
                                              ' manually')
                        do_next = True
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
