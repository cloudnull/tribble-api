from multiprocessing import Process, cpu_count, active_children
from signal import SIGKILL
import os
import traceback
import time
from daemon import pidfile

from tribble.appsetup.start import LOG, QUEUE
from tribble import info


class NoJobToDo(Exception):
    pass


class MainDisptach(object):
    def __init__(self, sys_control=True):
        """
        Prep the sytem by adding logger/m_args to memory
        """
        self.logger = LOG
        self.queue = QUEUE
        self.system = sys_control
        self.amw = 100
        self.amq = 250
        self.main()

    def write_pid(self, pidfile_ext):
        """
        Write Pid will get the current pid for a process and then write a pid
        file for it. This method requires "pidfile_path" which is the path to
        where the pid wil exist.
        """
        pidfile_path = '%s%s' % ('/var/run/', pidfile_ext)
        if os.path.isfile(pidfile_path):
            os.remove(pidfile_path)
        open_flags = (os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        open_mode = 0644
        pidfile_fd = os.open(pidfile_path, open_flags, open_mode)
        pffd = os.fdopen(pidfile_fd, 'w')
        # var pid is written with the vars() method
        pid = os.getpid()
        line = "%(pid)d\n" % vars()
        pffd.write(line)
        pffd.close()
        pidfile.PIDLockFile(path=pidfile_path)
        return pidfile_path

    def main(self):
        """
        The main loop creats two sets of threads. The first is a Worker Queue
        processing thread the second creats a monitoring Thread. The monitoring
        thread process monitors instances as they are loaded in from the Narciss
        DB. If anything is found to need building, rebuilding or deleting the
        Queue processing thread takes care of those actions.
        """
        self.write_pid(pidfile_ext='%s.main' % info.__appname__)
        self.logger.info('Main Warm up.')

        # Available Processes
        self.work_thread()

    def compute_workers(self, w_count):
        """
        This method computes the total number of Processes which can be used
        for in a construction operation. This sets a limit which should
        protect the system. The number is a moving target with the ability to
        burst 20% beyond the computed maxium number of Processes which is set
        at 250. Bursting will only be used if the Queue size is larger than the
        maximum computed workers.Lastly, to regulate the created Processes,
        an active worker count is subtraced from the decided number of workers
        and is then returned as an integer.
        """
        cpu = cpu_count()
        tpc = cpu * 10
        _qz = self.queue.qsize()
        _mw = tpc
        if _mw > self.amw:
            _mw = self.amw

        if (_qz or tpc) < _mw:
            workers = max(_qz, tpc)
        elif _qz > tpc:
            burst = int((_mw * ((_qz * .50) / 100)) + tpc - w_count)
            workers = burst
        elif _qz > _mw:
            burst = int((_mw * ((_qz * .50) / 100)) + _mw - w_count)
            workers = burst
        else:
            workers = tpc

        if workers < 0:
            workers = 0
        return workers

    def work_thread(self):
        """
        The work thread is responsible for the timely processing of items in the
        queue. This method will spawn the worker threads for processing the
        queue.
        """
        pid = self.write_pid(pidfile_ext='%s.pid.worker' % info.__appname__)
        _aw = []
        while self.system:
            try:
                _qs = self.queue.qsize()
                self.logger.debug('queue size %s' % _qs)
                if (_qs == 0):
                    time.sleep(3)
                elif (_qs >= self.amq):
                    import tempfile
                    dump_file = ('%s%s%s_EMERGENCY.dump'
                                 % (tempfile.gettempdir(),
                                    os.sep,
                                    info.__appname__))
                    self.logger.critical('\n|========================\n'
                                            'Emergency Queue Dump in Progress'
                                            ' Size is "%s" which is likely'
                                            ' a PROBLEM. As such we are dumping'
                                            ' the tasks. Dump File is "%s"'
                                            '\n========================|\n'
                                            % (_qs, dump_file))
                    while not _qs > 0:
                        try:
                            with open(dump_file, 'a') as _file:
                                get_file = self.queue.get()
                                dumped = ('%s\n' % get_file)
                                _file.write(dumped)
                        except Exception:
                            self.logger.error(traceback.format_exc())
                            break
                else:
                    w_count = len(_aw)
                    workers = self.compute_workers(w_count)

                    self.logger.info('queue size  %d' % _qs)
                    self.logger.info('Active Jobs %d' % w_count)
                    self.logger.info('num workers %d' % workers)

                    for _ in xrange(workers):
                        wthread = Process(target=self.work_doer,
                                          args=(self.queue,))
                        wthread.start()

                    _aw = active_children()
                    if w_count > 0:
                        time.sleep(.25)
            except Exception:
                self.logger.error(traceback.format_exc())
            else:
                if _aw:
                    for job in _aw:
                        if not job.is_alive():
                            index = _aw.index(job)
                            _aw.pop(index)
                            w_count = len(_aw)
        if os.path.isfile(pid):
            os.remove(pid)

    def work_doer(self, queue):
        """
        This is the "doing part of the work thread. Once an Item is taken out of
        the queue, it is processed. The first action of the process is to
        authenticate. If authentication is good the item will be processed. If
        authentication is bad, then the method will log the authentication
        failure, or raise an exception.
        """
        from tribble.operations import constructor, utils
        try:
            cells = queue.get(timeout=2)
            self.logger.info(cells)
            for cell in cells:
                if cell['job'] == 'build':
                    job = constructor.bob_builder
                elif cell['job'] == 'delete':
                    job = constructor.bob_destroyer
                else:
                    raise NoJobToDo('No Job has been provided')

                qnty = int(cell.get('quantity', 1))
                LOG.info('Quantity of Nodes to build == %s' % qnty)
                utils.worker_proc(job_action=job,
                                  t_args=cell,
                                  num_jobs=qnty)
        except Exception:
            self.logger.debug('Nothing to pull from Queue')
        finally:
            os.kill(os.getpid(), SIGKILL)
