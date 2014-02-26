# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
from multiprocessing import Process, cpu_count, active_children
import os
import traceback
import time

from daemon import pidfile

from tribble import info
from tribble.api.start import LOG, QUEUE, STATS
from tribble.common.db import zone_status as _zs


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
                    STATS.gauge('AvailableWorkers', workers)
                    self.logger.debug('queue size  %d' % _qs)
                    self.logger.debug('Active Jobs %d' % w_count)
                    self.logger.debug('num workers %d' % workers)

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
        from tribble.engine import constructor, utils, config_manager
        STATS.gauge('ActiveThreads', 1, delta=True)
        try:
            cells = queue.get(timeout=2)
            self.logger.debug(cells)
            for _cell in cells:
                try:
                    cell = utils.manager_dict(b_d=_cell)
                    state = _zs.ZoneState(cell=cell)
                    if cell['job'] in ('build', 'redeploy_build'):
                        state._build()
                        if cell['job'] == 'redeploy_build':
                            bobs = constructor.MainOffice(nucleus=cell)
                            bobs.api_setup()
                        else:
                            with STATS.timer('ZoneCreate'):
                                bobs = constructor.MainOffice(nucleus=cell)
                                bobs.api_setup()
                        state._active()
                    elif cell['job'] in ('schematic_delete',
                                         'zone_delete',
                                         'redeploy_delete',
                                         'instance_delete'):
                        if (cell.get('zone_id') and
                            not cell['job'] == 'instance_delete'):
                            state._delete()
                            if cell['job'] == 'redeploy_delete':
                                bobs = constructor.MainOffice(nucleus=cell)
                                bobs.bob_destroyer()
                            else:
                                if 'uuids' in cell and cell['uuids']:
                                    bobs = constructor.MainOffice(nucleus=cell)
                                    with STATS.timer('ZoneDelete'):
                                        bobs.bob_destroyer()
                        if cell['job'] == 'instance_delete':
                            bobs = constructor.MainOffice(nucleus=cell)
                            bobs.bob_destroyer()
                        elif cell['job'] == 'schematic_delete':
                            state._delete_resource(skm=True)
                        else:
                            state._delete_resource()
                    elif cell['job'] == 'reconfig':
                        STATS.incr('Reconfigurations')
                        state._reconfig()
                        config_manager.chef_update_instances(nucleus=cell)
                        state._active()
                    else:
                        raise NoJobToDo('No Job has been provided')
                except Exception, exp:
                    self.logger.error(traceback.format_exc())
                    cell['zone_msg'] = ('Issues are happening while performing'
                                        ' actions. MESSAGE : "%s"' % exp)
                    state._active()
                finally:
                    del cell
        except Exception, exp:
            self.logger.debug('Nothing to pull from Queue %s' % exp)
        finally:
            STATS.gauge('ActiveThreads', -1, delta=True)
