import click
import click_log
import logging
import os
# from os.path import basename, isfile, join
from os.path import isfile
import subprocess
from subprocess import CalledProcessError
# import numpy as np
import pandas as pd
import re
import time
from enum import Enum
# import signal
from threading import Thread
import serial
# from warnings import warn
import sys


logger = logging.getLogger(__name__)
click_log.basic_config(logger)

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
    def __init__(self):
        self.target_dir = 'xRTOS_MMU_SEMAPHORE'
        self.scriptdir = os.getcwd()
        self.working_dir = self.scriptdir + '/../' + self.target_dir
        self.makecleancmd = ['make', 'clean']
        self.makeinstallcmd = ['make', 'install']
        self.set_environment()
        self.set_compilation()

    def compile(self):
        logger.debug('working_dir={}'.format(self.working_dir))
        os.chdir(self.working_dir)
        try:
            # do make clean to clean up previous makes
            logger.info('Run make clean')
            cp = subprocess.run(self.makecleancmd,
                                check=True,
                                capture_output=True,
                                text=True,
                                env=self.myenv)
            logger.debug(cp.stdout)

            # generate the benchmark_config.h file
            logger.info('Writing benchmark_config.h')
            with open('benchmark_config.h', 'w') as outfile:
                subprocess.run(self.makeprepcmd,
                               stdout=outfile)

            # do the actual compilation
            logger.info('Performing actual compilation')
            cp = subprocess.run(self.makeinstallcmd,
                                check=True,
                                capture_output=True,
                                text=True,
                                env=self.myenv)
            text = cp.stdout.split('\n')
            for line in text:
                logger.debug(line)
        except (CalledProcessError, UnicodeDecodeError):
            logger.warning('Compilation subprocess resulted ' +
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
                logger.debug('config={}'.format(config))
                config = re.sub(r'^\'', '', config)
                config = re.sub(r'\'$', '', config)
                config_param = '-Dconfig=' + config
                logger.debug('config={}'.format(config))
            if dassign is not None:
                # Same here, remove leading and trailing quotes.
                logger.debug('dassign={}'.format(dassign))
                dassign = re.sub(r'^\'', '', dassign)
                dassign = re.sub(r'\'$', '', dassign)
                dassign_param = '-Ddassign=' + dassign
                logger.debug('dassign={}'.format(dassign))

            self.makeprepcmd = ['m4',
                                config_param,
                                dassign_param,
                                'benchmark_config.m4']
        else:
            self.makeprepcmd = ['m4',
                                'benchmark_config.m4']


class SerialThread(Thread):
    def __init__(self, tty):
        super(SerialThread, self).__init__()
        # connection setting through cli or default setting
        self.tty = tty
        # start/stop thread flag
        self.run_thread = False

    def start_thread(self):
        self.run_thread = True
        self.start()

    def stop_thread(self):
        self.run_thread = False
        self.cleanup()
        self.join()

    def cleanup(self):
        # abstract method, implementation in subclass if needed
        pass

    def set_tty(self, tty):
        self.tty = tty

    def connect_to_serial(self, baud, timeout=None):
        try:
            self.serial = serial.Serial(self.tty,
                                        baud, timeout=timeout)
            self.connected = True
        except Exception:
            logger.warning('Could not connect to serial port ' +
                           ' {}'.format(self.tty))
            logger.warning(sys.exc_info()[0])


class Resetter(SerialThread):
    def __init__(self, tty, log_processor):
        super(Resetter, self).__init__(tty)
        self.log_processor = log_processor
        # Flag for main thread to detect move to next experiment
        self.next_experiment = False
        self.min_observations = 250
        # timeout for not receiving data anymore (seconds)
        self.timeout = 60.0
        self.curtime = 0.0
        # number of seconds to sleep
        self.timeslice = 1.0
        self.connected = False

    def run(self):
        # Make connection to the Arduino
        self.connect_to_serial(9600)

        while self.run_thread is True:
            if self.connected is True:
                # Get number of log lines
                input_ok = self.log_processor.get_input_ok()
                logger.debug('Resetter: got input ok={}.'.format(input_ok))
                if input_ok:
                    # There is some progress, reset the curtime
                    self.curtime = 0
                    observations = self.log_processor.get_iteration()
                    logger.debug('Resetter: ' +
                                 'observations={}.'.format(observations))
                    # Do we have enough observations?
                    if observations > self.min_observations:
                        logger.info('Enough observations read.')
                        logger.debug('Setting next experiment flag to True.')
                        self.set_next_experiment(True)
                        self.do_reset()
                else:
                    # check for timeout
                    self.curtime += self.timeslice
                    if int(self.curtime) % 10 == 0:
                        logger.info('Waiting {}'.format(self.curtime) +
                                    ' secs and counting..')
                    if self.curtime > self.timeout:
                        logger.warning('Timeout reached.')
                        logger.debug('Setting reset flag to True.')
                        self.do_reset()
            time.sleep(self.timeslice)

    def get_next_experiment(self):
        return self.next_experiment

    def set_next_experiment(self, flag):
        self.next_experiment = flag

    def do_reset(self):
        logger.info('Resetting the Raspberry Pi now.')
        self.serial.write('r'.encode())
        # Reset to initial state
        self.curtime = 0
        self.last_iteration = -1


class LogProcessor(SerialThread):
    def __init__(self, tty, output_file):
        super(LogProcessor, self).__init__(tty)
        # for the monitor that reads the log
        self.iteration = 0
        self.input_ok = False
        # start/stop thread flag
        self.run_thread = False
        self.logfile = output_file
        self.filehandle = None
        self.connected = False

    # Overridden from Thread.run()
    def run(self):
        # Make connection to the Raspberry Pi
        self.connect_to_serial(115200, timeout=0.5)

        # Open logfile for writing
        self.open_logfile()

        while self.run_thread is True:
            if self.connected is True:
                # readline is only temporarily blocking, timeout is set
                line = self.serial.readline()
                try:
                    string = line.decode('ascii')
                    logger.debug('LogProcessor: line={}'.format(string.strip()))
                    match = re.search(r'iteration: ([0-9]+)', string)
                    if match:
                        iteration = int(match.group(1))
                        if self.is_logical_iteration(iteration):
                            self.input_ok = True
                            logger.debug('Found iteration {}.'.format(iteration))
                            self.iteration = iteration
                            if self.filehandle is not None:
                                self.filehandle.write(string)
                        else:
                            self.set_init_state()
                            logger.warning('Discarding non-logical iteration ' +
                                           '{}.'.format(iteration))
                    else:
                        # oh oh, no match in received line
                        self.set_init_state()
                        logger.debug('LogProcessor: no match in ' +
                                     ' line {}'.format(line))
                except (TypeError, UnicodeDecodeError):
                    self.set_init_state()
                    logger.warning('Caught Error reading bytes via serial')
                    logger.debug('Error: ', sys.exc_info()[0])
            else:
                time.sleep(0.5)

    def open_logfile(self):
        # open logfile for writing
        try:
            self.filehandle = open(self.logfile, 'w')
        except Exception:
            logger.error('Could not open file ' +
                         '{}'.format(self.logfile))

    def is_logical_iteration(self, iteration):
        if iteration == self.iteration:
            return True
        elif iteration == self.iteration + 1:
            return True
        elif iteration == 1:
            return True
        else:
            return False

    def set_init_state(self):
        self.input_ok = False
        self.iteration = 0

    def get_iteration(self):
        return self.iteration

    def get_input_ok(self):
        return self.input_ok

    def cleanup(self):
        self.filehandle.close()


flds = {
    Fields.CONFIG: 'configuration of cores',
    Fields.DASSIGN: 'data assignment',
    Fields.DISABLE_CACHE: 'disable cache',
    Fields.NO_CACHE_MGMT: 'no cache management',
    Fields.FILENAME_PREFIX: 'filename prefix',
}


def do_experiments(infile, outfile, workdir, tty_reset, tty_logging):

    logger.info('Instantiating Compile object.')
    comp = Compile()

    logger.info('Instantiating LogProcessor object.')
    log_processor = LogProcessor(tty_logging, outfile)
    log_processor.start_thread()

    logger.info('Instantiating Resetter object.')
    resetter = Resetter(tty_reset, log_processor)
    resetter.start_thread()

    df = pd.read_excel(infile)

    i = 0
    for idx, row in df.iterrows():
        i += 1
        # First compile this experiment
        logger.info('Starting a new compilation, ' +
                    'experiment nr is {}.'.format(i))
        config = row[flds[Fields.CONFIG]]
        dassign = row[flds[Fields.DASSIGN]]
        comp.set_compilation(config=config, dassign=dassign)
        comp.compile()

        logger.info('Compilation done.')
        while True:
            if resetter.get_next_experiment() is True:
                # Oh! The resetter has reset the Pi. We should move on
                # to the next experiment
                logger.info('Detected reset, ' +
                            ' move on to next experiment..')
                # Finally reset the reset flag for the next iteration
                resetter.set_next_experiment(False)

                # break out of this loop
                break
            else:
                time.sleep(0.5)

    logger.info('Done processing excel file..')
    time.sleep(0.5)

    # Stop the threads
    resetter.stop_thread()
    log_processor.stop_thread()

    logger.info('Stopping.. bye now!')


@click.command()
@click.option('--input-file',
              required=True,
              help='Path and filename of the input Excel file.')
@click.option('--output-file',
              required=True,
              help='Path and filename of the log file for output.')
@click.option('--working-directory',
              default='../xRTOS_MMU_SEMAPHORE',
              help='Path of the working directory.')
@click.option('--tty-reset',
              default='/dev/ttyUSB0',
              help='Path of the Arduino Pi serial conn for the reset.')
@click.option('--tty-logging',
              default='/dev/ttyUSB1',
              help='Path of the Raspberry Pi serial conn for the logs.')
@click_log.simple_verbosity_option(logger)
def main(input_file, output_file, working_directory, tty_reset, tty_logging):
    if not isfile(input_file):
        print('Error: input file {}'.format(input_file), end=' ')
        print('does not exist!')
        exit(1)
    do_experiments(input_file, output_file, working_directory,
                   tty_reset, tty_logging)


if __name__ == "__main__":
    main()
