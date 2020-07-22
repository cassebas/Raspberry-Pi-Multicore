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


class Fields(Enum):
    NUMBER = 1
    CONFIG_SERIES = 2
    CONFIG_BENCH = 3
    DISABLE_CACHE = 4
    ENABLE_MMU = 5
    ENABLE_SCREEN = 6
    NO_CACHE_MGMT = 7
    SB_DATASIZE = 8
    EXP_LABEL = 9
    PMU_CORE0 = 10
    PMU_CORE1 = 11
    PMU_CORE2 = 12
    PMU_CORE3 = 13
    DISP_INPUT = 14
    BSORT_INPUT = 15
    MATMULT_INPUT = 16
    TICK_RATE_HZ = 17


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

    def set_compilation(self, config_series=None, config_bench=None,
                        label=None, datasize=None,
                        pmu_cores=None, no_cache_mgmt=False,
                        enable_mmu=False, enable_screen=False,
                        disparity_inputsize=None, bsort_inputsize=None,
                        matmult_inputsize=None, tick_rate_hz=None):
        arg_m4_list = []
        arg_make_list = []
        if config_series is not None:
            # The python process that runs m4 cannot handle a string
            # with quotes well, remove leading and trailing quotes.
            logger.debug('config_series={}'.format(config_series))
            config_series = re.sub(r'^\'', '', config_series)
            config_series = re.sub(r'\'$', '', config_series)
            config_series_param = '-Dconfig_series=' + config_series
            logger.debug('config={}'.format(config_series_param))
            arg_m4_list.append(config_series_param)
        if config_bench is not None:
            # The python process that runs m4 cannot handle a string
            # with quotes well, remove leading and trailing quotes.
            logger.debug('config_benchmarks={}'.format(config_bench))
            config_bench = re.sub(r'^\'', '', config_bench)
            config_bench = re.sub(r'\'$', '', config_bench)
            config_bench_param = '-Dconfig_benchmarks=' + config_bench
            logger.debug('config={}'.format(config_bench_param))
            arg_m4_list.append(config_bench_param)
        if label is not None:
            logger.debug('label={}'.format(label))
            label_param = '-Dexp_label={}'.format(label)
            arg_m4_list.append(label_param)
        if enable_mmu is True:
            logger.debug('enable_mmu={}'.format(enable_mmu))
            enable_mmu_param = '-Dmmu_enable'
            arg_m4_list.append(enable_mmu_param)
        if enable_screen is True:
            logger.debug('enable_screen={}'.format(enable_screen))
            enable_screen_param = '-Dscreen_enable'
            arg_m4_list.append(enable_screen_param)
        if disparity_inputsize is not None:
            logger.debug('disparity_inputsize={}'.format(disparity_inputsize))
            disparity_inputsize_param = \
                '-Ddisparity_inputsize={}'.format(disparity_inputsize)
            arg_m4_list.append(disparity_inputsize_param)
        if bsort_inputsize is not None:
            logger.debug('bsort_inputsize={}'.format(bsort_inputsize))
            bsort_inputsize_param = \
                '-Dbsort_inputsize={}'.format(bsort_inputsize)
            arg_m4_list.append(bsort_inputsize_param)
        if matmult_inputsize is not None:
            logger.debug('matmult_inputsize={}'.format(matmult_inputsize))
            matmult_inputsize_param = \
                '-Dmatmult_inputsize={}'.format(matmult_inputsize)
            arg_m4_list.append(matmult_inputsize_param)
        if tick_rate_hz is not None:
            logger.debug('tick_rate_hz={}'.format(tick_rate_hz))
            tick_rate_hz_param = '-Dtick_rate_hz={}'.format(tick_rate_hz)
            arg_m4_list.append(tick_rate_hz_param)
        if no_cache_mgmt is True:
            no_cache_mgmt_param = 'NO_CACHE_MGMT=-DNO_CACHE_MGMT'
            arg_make_list.append(no_cache_mgmt_param)
        if datasize is not None:
            logger.debug('datasize={}'.format(datasize))
            datasize_param = ('SYNBENCH_DATASIZE=' +
                              '-DSYNBENCH_DATASIZE={}'.format(datasize))
            arg_make_list.append(datasize_param)
        if pmu_cores is not None:
            # if pmu_cores is not None, it must be a tuple of four
            pmu0, pmu1, pmu2, pmu3 = pmu_cores
            if not pd.isnull(pmu0):
                pmu0 = re.sub(r'^\'', '', pmu0)
                pmu0 = re.sub(r'\'$', '', pmu0)
                pmu_core0_param = '-Dpmu_core0={}'.format(pmu0)
                logger.debug('pmu0={}'.format(pmu0))
                arg_m4_list.append(pmu_core0_param)
            if not pd.isnull(pmu1):
                pmu1 = re.sub(r'^\'', '', pmu1)
                pmu1 = re.sub(r'\'$', '', pmu1)
                pmu_core1_param = '-Dpmu_core1={}'.format(pmu1)
                logger.debug('pmu1={}'.format(pmu1))
                arg_m4_list.append(pmu_core1_param)
            if not pd.isnull(pmu2):
                pmu2 = re.sub(r'^\'', '', pmu2)
                pmu2 = re.sub(r'\'$', '', pmu2)
                pmu_core2_param = '-Dpmu_core2={}'.format(pmu2)
                logger.debug('pmu2={}'.format(pmu2))
                arg_m4_list.append(pmu_core2_param)
            if not pd.isnull(pmu3):
                pmu3 = re.sub(r'^\'', '', pmu3)
                pmu3 = re.sub(r'\'$', '', pmu3)
                pmu_core3_param = '-Dpmu_core3={}'.format(pmu3)
                logger.debug('pmu3={}'.format(pmu3))
                arg_m4_list.append(pmu_core3_param)

        self.makeprepcmd = ['m4'] + arg_m4_list + ['benchmark_config.m4']
        logger.debug('makeprepcmd={}'.format(self.makeprepcmd))

        bench_config_m4 = 'BENCHMARK_CONFIG=-DBENCHMARK_CONFIG_M4'
        arg_make_list.append(bench_config_m4)

        self.makeinstallcmd = ['make'] + arg_make_list + ['install']
        logger.debug('makeinstallcmd={}'.format(self.makeinstallcmd))


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
    def __init__(self, tty, log_processor, min_observations=100):
        super(Resetter, self).__init__(tty)
        self.log_processor = log_processor
        # Flag for main thread to detect move to next experiment
        self.next_experiment = False
        self.min_observations = min_observations
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
                        self.log_processor.set_init_state()
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
                        self.log_processor.set_init_state()
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
        self.no_match = 0
        self.max_no_match = 50

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
                    string = line.decode('utf-8')
                    logger.debug('LogProcessor: line={}'.format(string.strip()))
                    match = re.search(r'iteration: ([0-9]+)', string)
                    if match:
                        iteration = int(match.group(1))
                        if self.is_logical_iteration(iteration):
                            self.input_ok = True
                            self.no_match = 0
                            logger.debug('Found iteration {}.'.format(iteration))
                            self.iteration = iteration
                            if self.filehandle is not None:
                                self.filehandle.write(string)
                        else:
                            self.set_init_state()
                            logger.warning('Discarding non-logical iteration ' +
                                           '{}.'.format(iteration))
                    else:
                        # no match in received line
                        logger.debug('LogProcessor: no match in ' +
                                     ' line {}'.format(line))
                        self.no_match += 1
                        if self.no_match > self.max_no_match:
                            logger.warning('LogProcessor: number ' +
                                           'of not-matched lines ' +
                                           'have exceeded threshold!')
                            self.set_init_state()
                            self.input_ok = False
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
        self.no_match = 0
        self.iteration = 0

    def get_iteration(self):
        return self.iteration

    def get_input_ok(self):
        return self.input_ok

    def cleanup(self):
        self.filehandle.close()


flds = {
    Fields.NUMBER: 'experiment number',
    Fields.CONFIG_SERIES: 'benchmark series',
    Fields.CONFIG_BENCH: 'benchmark configuration',
    Fields.DISABLE_CACHE: 'disable cache',  # not implemented for now
    Fields.ENABLE_MMU: 'enable mmu',
    Fields.ENABLE_SCREEN: 'enable screen',
    Fields.NO_CACHE_MGMT: 'no cache management',
    Fields.SB_DATASIZE: 'synbench datasize',
    Fields.EXP_LABEL: 'experiment label',
    Fields.PMU_CORE0: 'pmu core 0',
    Fields.PMU_CORE1: 'pmu core 1',
    Fields.PMU_CORE2: 'pmu core 2',
    Fields.PMU_CORE3: 'pmu core 3',
    Fields.DISP_INPUT: 'disparity inputsize',
    Fields.BSORT_INPUT: 'bsort inputsize',
    Fields.MATMULT_INPUT: 'matmult inputsize',
    Fields.TICK_RATE_HZ: 'tick rate hz',
}


def do_experiments(infile, outfile, workdir, tty_reset, tty_logging,
                   min_observations, begin, count):

    logger.info('Instantiating Compile object.')
    comp = Compile()

    logger.info('Instantiating LogProcessor object.')
    log_processor = LogProcessor(tty_logging, outfile)
    log_processor.start_thread()

    logger.info('Instantiating Resetter object.')
    resetter = Resetter(tty_reset, log_processor, min_observations)
    resetter.start_thread()

    df = pd.read_excel(infile)

    # Convert boolean fields to actual bool type
    df[flds[Fields.NO_CACHE_MGMT]] = df[flds[Fields.NO_CACHE_MGMT]].astype(bool)
    df[flds[Fields.ENABLE_MMU]] = df[flds[Fields.ENABLE_MMU]].astype(bool)
    df[flds[Fields.ENABLE_SCREEN]] = df[flds[Fields.ENABLE_SCREEN]].astype(bool)

    for idx, row in df.iterrows():
        number = row[flds[Fields.NUMBER]]
        logger.debug('Experiment number read is {}.'.format(number))
        if number >= begin and number < (begin + count):
            # First compile this experiment
            logger.info('Starting a new compilation, ' +
                        'experiment nr is {}.'.format(number))
            config_series = row[flds[Fields.CONFIG_SERIES]]
            config_bench = row[flds[Fields.CONFIG_BENCH]]
            label = row[flds[Fields.EXP_LABEL]]
            no_cache_mgmt = row[flds[Fields.NO_CACHE_MGMT]]
            enable_mmu = row[flds[Fields.ENABLE_MMU]]
            enable_screen = row[flds[Fields.ENABLE_SCREEN]]
            datasize = row[flds[Fields.SB_DATASIZE]]
            pmu_cores = (row[flds[Fields.PMU_CORE0]],
                         row[flds[Fields.PMU_CORE1]],
                         row[flds[Fields.PMU_CORE2]],
                         row[flds[Fields.PMU_CORE3]])
            disparity_inputsize = row[flds[Fields.DISP_INPUT]]
            bsort_inputsize = row[flds[Fields.BSORT_INPUT]]
            matmult_inputsize = row[flds[Fields.MATMULT_INPUT]]
            tick_rate_hz = row[flds[Fields.TICK_RATE_HZ]]
            comp.set_compilation(config_series=config_series,
                                 config_bench=config_bench,
                                 label=label, datasize=datasize,
                                 pmu_cores=pmu_cores,
                                 no_cache_mgmt=no_cache_mgmt,
                                 enable_mmu=enable_mmu,
                                 enable_screen=enable_screen,
                                 disparity_inputsize=disparity_inputsize,
                                 bsort_inputsize=bsort_inputsize,
                                 matmult_inputsize=matmult_inputsize,
                                 tick_rate_hz=tick_rate_hz)
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

        else:
            logger.debug('Not processing experiment {}.'.format(number))

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
@click.option('--min-observations',
              default=100,
              help='Minimum number of observations to read.')
@click.option('--experiment-begin',
              default=1,
              help='Number of experiment to start processing.')
@click.option('--experiment-count',
              default=1,
              help='Number of experiments process.')
@click_log.simple_verbosity_option(logger)
def main(input_file, output_file, working_directory, tty_reset, tty_logging,
         min_observations, experiment_begin, experiment_count):
    if not isfile(input_file):
        print('Error: input file {}'.format(input_file), end=' ')
        print('does not exist!')
        exit(1)
    if isfile(output_file):
        print('Error: output file {}'.format(output_file), end=' ')
        print('already exists!')
        exit(1)
    do_experiments(input_file, output_file, working_directory,
                   tty_reset, tty_logging, min_observations,
                   experiment_begin, experiment_count)


if __name__ == "__main__":
    main()
