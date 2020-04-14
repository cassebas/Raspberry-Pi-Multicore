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
from warnings import warn
import sys
import traceback


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


class Lock:
    def __init__(self):
        self.flag = [False, False]
        self.turn = False

    def acquire_lock(self, process_flag):
        self.flag[process_flag] = True
        self.turn = process_flag
        while self.flag[not process_flag] is True and self.turn == process_flag:
            # busy wait
            pass
        # Lock has been acquired! Critical section may begin

    def release_lock(self, process_flag):
        self.flag[process_flag] = False


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

    def compile(self, lock, pflag):
        self.outputwin.log_message('working_dir={}'.format(self.working_dir),
                                   lock, pflag)
        os.chdir(self.working_dir)
        try:
            # do make clean to clean up previous makes
            cp = subprocess.run(self.makecleancmd,
                                check=True,
                                capture_output=True,
                                text=True,
                                env=self.myenv)
            self.outputwin.log_message(cp.stdout, lock, pflag)

            # generate the benchmark_config.h file
            self.outputwin.log_message('writing benchmark_config.h',
                                       lock, pflag)
            with open('benchmark_config.h', 'w') as outfile:
                subprocess.run(self.makeprepcmd,
                               stdout=outfile)

            # do the actual compilation
            self.outputwin.log_message('actual compilation',
                                       lock, pflag)
            cp = subprocess.run(self.makeinstallcmd,
                                check=True,
                                capture_output=True,
                                text=True,
                                env=self.myenv)
            text = cp.stdout.split('\n')
            for line in text:
                self.outputwin.log_message(line, lock, pflag)
        except (CalledProcessError, UnicodeDecodeError):
            self.outputwin.log_message('Compilation subprocess resulted ' +
                                       'in an error!',
                                       lock, pflag)

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


class UIthread(Thread):
    def __init__(self, uicomp):
        super(UIthread, self).__init__()
        self.settings = dict()
        self.uicomp = uicomp
        self.menuwin = uicomp.get_menuwin()
        self.expwin = uicomp.get_experimentwin()
        self.outputwin = uicomp.get_outputwin()

        # start/stop thread flag
        self.run_thread = False

    def ui_input_setting(self, name, lock, pflag):
        # critical section, first acquire lock
        lock.acquire_lock(pflag)

        curses.echo()
        (y, x) = self.menuwin.get_window().getyx()
        self.menuwin.get_window().addstr('{}: '.format(name))
        self.settings[name] = self.menuwin.get_window().getstr().decode()
        self.process_setting(name)
        # self.logfile = join(self.path, filename)
        # # open logfile for writing
        # self.filehandle = open(self.logfile, 'wb')
        curses.noecho()
        self.menuwin.get_window().move(y, x)
        self.menuwin.get_window().clrtobot()
        self.menuwin.get_window().box()
        self.menuwin.write_status('{} set to {}'.format(name,
                                                        self.settings[name]))
        # critical section end, release lock
        lock.release_lock(pflag)

    def process_setting(self, name):
        # abstract method, implementation in subclass if needed
        pass

    def set_lock(self, lock, process_flag):
        self.lock = lock
        self.pflag = process_flag

    def start_thread(self):
        self.run_thread = True
        self.start()

    def stop_thread(self):
        self.run_thread = False
        self.cleanup()

    def cleanup():
        # abstract method, implementation in subclass if needed
        pass

    def connect_to_serial(self, baud, timeout=None):
        try:
            self.serial = serial.Serial(self.settings['tty'],
                                        baud, timeout=timeout)
            self.connected = True
        except Exception:
            warn('Could not connect to serial port ' +
                 ' {}'.format(self.settings['tty']))
            warn(traceback.format_exception(*sys.exc_info()))


class Resetter(UIthread):
    def __init__(self, uicomp, logging):
        super(Resetter, self).__init__(uicomp)
        self.logging = logging
        # default tty (can be changed in the application)
        self.settings['tty'] = '/dev/ttyUSB0'
        # Flag for other thread to detect reset condition
        self.resetflag = False
        self.min_observations = 50
        self.last_iteration = -1
        # timeout for not receiving data anymore (seconds)
        self.timeout = 40.0
        self.curtime = 0.0
        # number of seconds to sleep
        self.timeslice = 0.5
        self.connected = False

    def run(self):
        while self.run_thread is True:
            if self.resetflag is False and self.connected is True:
                # Get number of log lines
                this_iteration = self.logging.get_iteration()
                if this_iteration > self.last_iteration:
                    # There is some progress, reset the curtime
                    self.curtime = 0
                    self.last_iteration = this_iteration
                    # Do we have enough observations?
                    if self.last_iteration > self.min_observations:
                        self.outputwin.log_message('Enough observations read.',
                                                   self.lock, self.pflag)
                        self.outputwin.log_message('Setting reset flag to True.',
                                                   self.lock, self.pflag)
                        self.set_resetflag(True)
                        self.do_reset()
                else:
                    # check for timeout
                    self.curtime += self.timeslice
                    if int(self.curtime * 2) % 20 == 0:
                        self.outputwin.log_message('Waiting {}'.format(self.curtime) +
                                                   ' secs and counting..',
                                                   self.lock, self.pflag)
                    if self.curtime > self.timeout:
                        self.outputwin.log_message('Timeout reached.',
                                                   self.lock, self.pflag)
                        self.outputwin.log_message('Setting reset flag to True.',
                                                   self.lock, self.pflag)
                        self.set_resetflag(True)
                        self.do_reset()
            time.sleep(self.timeslice)

    def get_resetflag(self):
        return self.resetflag

    def set_resetflag(self, reset):
        self.resetflag = reset

    def do_reset(self, manual=False):
        # If manual is True, this method is called by main thread,
        # that means that we must use the other flag (main's) for the
        # mutual exclusion lock.
        pflag = not self.pflag if manual else self.pflag

        self.outputwin.log_message('Resetting the Raspberry Pi now.',
                                   self.lock, pflag)
        self.serial.write('r'.encode())
        self.curtime = 0
        # also reset the last_iteration back to default state
        self.last_iteration = -1


class Logging(UIthread):
    def __init__(self, uicomp):
        super(Logging, self).__init__(uicomp)
        # default tty (can be changed in the application)
        self.settings['tty'] = '/dev/ttyUSB1'
        # for the monitor that reads the log
        self.iteration = 0
        # start/stop thread flag
        self.run_thread = False
        self.logfile = ''
        self.filehandle = None
        self.connected = False

    # Overridden from Thread.run()
    def run(self):
        # i = 0
        while self.run_thread is True:
            if self.connected is True:
                # readline is only temporarily blocking, timeout is set
                line = self.serial.readline()
                # i += 1
                # if i % 100 == 0:
                #     self.outputwin.log_message(line)
                if self.filehandle is not None:
                    self.filehandle.write(line)
                try:
                    match = re.search(r'iteration: ([0-9]+)', line)
                    if match:
                        iteration = match.group(1)
                        if iteration > self.iteration:
                            self.iteration = iteration
                    # else:
                    #     # oh oh, no match in received line
                    #     self.outputwin.log_message('no match in line {}'.format(line))
                except TypeError:
                    warn('Caught TypeError')
            else:
                time.sleep(0.5)

    def get_iteration(self):
        return self.iteration

    def process_setting(self, name):
        # implementation of abstract method
        # open logfile for writing
        try:
            self.filehandle = open(self.settings[name], 'wb')
        except Exception:
            warn('Could not open file ' +
                 '{}'.format(self.settings[name]))


class MenuThread(UIthread):
    def __init__(self, uicomp):
        super(MenuThread, self).__init__(uicomp)
        # initialize
        self.menu_option = None
        self.menu_set = {'flrcnRq'}
        self.input_flag = False
        self.status_message = None

    # Overridden from Thread.run()
    def run(self):
        while self.run_thread is True:
            self.menu_input()
            time.sleep(0.5)
            # if not self.input_flag:
            #     self.menu_input()
            # else:
            #     time.sleep(0.1)

    def menu_input(self):
        # critical section, first acquire lock
        self.lock.acquire_lock(self.pflag)

        window = self.menuwin.get_window()
        window.erase()
        window.box()
        window.move(1, 2)
        window.addstr('Menu:')
        window.move(2, 2)
        window.addstr(' [f] Set filename for output')
        window.move(3, 2)
        window.addstr(' [l] Set TTY for Raspberry Pi logging')
        window.move(4, 2)
        window.addstr(' [r] Set TTY for Arduino resetter')
        window.move(5, 2)
        window.addstr(' [c] Connect to serial ports')
        window.move(6, 2)
        window.addstr(' [n] Next experiment')
        window.move(7, 2)
        window.addstr(' [R] Reset Raspberry Pi manually')
        window.move(8, 2)
        window.addstr(' [q] Quit application')
        window.move(9, 2)
        window.addstr(' ---> ')
        key = window.getch()

        # if key == curses.KEY_RESIZE:
        #     self.uicomp.refresh()

        # critical section end, release lock
        self.lock.release_lock(self.pflag)

        if key > 0 and set(chr(key)).issubset(self.menu_set):
            # We got a valid input, set flag for handling the input
            self.menu_option = key
            self.input_flag = True

    def get_menu_input(self):
        if self.input_flag is True:
            # return valid input
            return self.menu_option
        else:
            # No valid input
            return None

    def reset_input_flag(self):
        self.input_flag = False
        self.menu_option = None

    # def set_status_message(self, status_message):
    #     self.status_message = status_message


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


def do_experiments(stdscr, infile, workdir):
    uicomp = windows.UIComponents()
    menuwin = uicomp.get_menuwin()
    expwin = uicomp.get_experimentwin()
    outputwin = uicomp.get_outputwin()
    uicomp.refresh()

    # Mutual exclusion mechaninism for writing to UI screen
    # There are 2 threads writing to UI screen, the main thread (this one)
    # and the MenuThread object.
    # Both processes are identified by their process flag (pflag)
    pflag_main = False
    pflag_menu = True
    pflag_resetter = True
    menulock = Lock()
    outputlock = Lock()

    comp = Compile(outputwin)

    logging = Logging(uicomp)
    logging.start_thread()

    resetter = Resetter(uicomp, logging)
    resetter.set_lock(outputlock, pflag_resetter)
    resetter.start_thread()

    menuthread = MenuThread(uicomp)
    menuthread.set_lock(menulock, pflag_menu)
    menuthread.start_thread()

    expwin.write_status('Processing input file {}.'.format(infile))

    time.sleep(0.5)

    df = pd.read_excel(infile)
    expwin.write_status('Input file {} processed.'.format(infile))

    time.sleep(1.0)

    run = True
    for idx, row in df.iterrows():
        print_experiment(expwin.get_window(), idx, row)
        # uicomp.clear_status(lock, pflag_main)

        if run is True:
            # First compile this experiment
            expwin.write_status('Compiling experiment')

            config = row['configuration of cores']
            dassign = row['data assignment']
            comp.set_compilation(config=config, dassign=dassign)
            comp.compile(outputlock, pflag_main)
            expwin.write_status('Compilation done.')

            do_next = False

            while not do_next:
                # # Wait a bit to avoid spinlocking while waiting for user input
                # time.sleep(0.5)

                # check if the next experiment can be selected
                # automatically (this is the case when enough
                # log lines have been printed or if a timeout has
                # been reached.
                if resetter.get_resetflag() is True:
                    # Oh! The resetter has reset the Pi. We should move on
                    # to the next experiment

                    # reset the reset flag
                    resetter.set_resetflag(False)
                    expwin.write_status('Detected reset, ' +
                                        ' repeat same experiment..',
                                        menulock, pflag_main)
                    time.sleep(0.5)
                else:
                    # Not yet a reset condition, move on to the menu
                    # and wait for input.
                    action = menuthread.get_menu_input()

                    if action is not None:
                        # reset the menu input flag for next input
                        menuthread.reset_input_flag()

                        if action == ord('q'):
                            run = False
                            do_next = True
                        elif action == ord('f'):
                            # Set output file
                            logging.ui_input_setting('filename',
                                                     menulock, pflag_main)
                        elif action == ord('l'):
                            # Set tty for logging
                            logging.ui_input_setting('tty logging',
                                                     menulock, pflag_main)
                        elif action == ord('r'):
                            # Set tty for resetter
                            resetter.ui_input_setting('tty arduino',
                                                      menulock, pflag_main)
                        elif action == ord('c'):
                            # Connect to serial ports
                            menulock.acquire_lock(pflag_main)
                            menuwin.write_status('Connecting to both serial ports..')
                            time.sleep(0.2)
                            resetter.connect_to_serial(9600)
                            logging.connect_to_serial(115200, timeout=0.5)
                            menuwin.write_status('Connected.')
                            menulock.release_lock(pflag_main)
                        elif action == ord('R'):
                            # Manually reset Raspberry Pi
                            menuwin.write_status('Resetting Raspberry Pi manually..',
                                                 menulock, pflag_main)
                            resetter.do_reset(manual=True)
                            menuwin.write_status('Raspberry Pi manually reset.',
                                                 menulock, pflag_main)
                        elif action == ord('n'):
                            # manually continue with next experiment
                            do_next = True
                            outputwin.log_message('Next experiment selected' +
                                                  ' manually',
                                                  menulock, pflag_main)
                            # Manually reset Raspberry Pi
                            menuwin.write_status('Resetting Raspberry Pi manually..',
                                                 menulock, pflag_main)
                            resetter.do_reset(manual=True)
                            menuwin.write_status('Raspberry Pi manually reset.',
                                                 menulock, pflag_main)

    menuwin.write_status('Stopping..',
                         menulock, pflag_main)
    time.sleep(0.5)
    menuwin.write_status('Stopping.. bye now!',
                         menulock, pflag_main)
    time.sleep(1)
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
