#! /usr/bin/env bash

### BEGIN INIT INFO
# Provides:          tribble-engine
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Should-Start:      $named
# Default-Start:     2 3 4 5
# Default-Stop:
# Short-Description: configuration management API for cloud providers
# Description:       configuration management API for cloud providers
### END INIT INFO

set -e

# /etc/init.d/tribble-engine: start and stop the tribble daemon
PROGRAM_NAME="tribble-engine"

DAEMON="/usr/local/bin/${PROGRAM_NAME}"
TRIBBLE_CONFIG_FILE="/etc/tribble/tribble.conf"
TRIBBLE_PID_FILE="/var/run/${PROGRAM_NAME}.pid"


source /lib/lsb/init-functions
export PATH="${PATH:+$PATH:}/usr/sbin:/sbin"

tribble_api_start() {
    if [ ! -s "$TRIBBLE_CONFIG_FILE" ]; then
        log_failure_msg "missing or empty config file $TRIBBLE_CONFIG_FILE"
        log_end_msg 1
        exit 0
    fi
        if start-stop-daemon --start --quiet --background \
        --pidfile $TRIBBLE_PID_FILE --make-pidfile --exec $DAEMON
    then
        rc=0
        sleep 1
        if ! kill -0 $(cat $TRIBBLE_PID_FILE) >/dev/null 2>&1; then
            rc=1
        fi
    else
        rc=1
    fi

    if [ $rc -eq 0 ]; then
        log_end_msg 0
    else
        log_failure_msg "${PROGRAM_NAME} daemon failed to start"
        log_end_msg 1
        rm -f $TRIBBLE_PID_FILE
    fi
}


case "$1" in
  start)
        log_daemon_msg "Starting ${PROGRAM_NAME} daemon" "${PROGRAM_NAME}"
        if [ -s $TRIBBLE_PID_FILE ] && kill -0 $(cat $TRIBBLE_PID_FILE) >/dev/null 2>&1; then
            log_progress_msg "Tribble is already running"
            log_end_msg 0
            exit 0
        fi
        tribble_api_start
        ;;
  stop)
        log_daemon_msg "Stopping ${PROGRAM_NAME} daemon" "${PROGRAM_NAME}"
        start-stop-daemon --stop --quiet --oknodo --pidfile $TRIBBLE_PID_FILE
        log_end_msg $?
        rm -f $TRIBBLE_PID_FILE
        ;;
  restart)
        set +e
        log_daemon_msg "Restarting ${PROGRAM_NAME} daemon" "${PROGRAM_NAME}"
        if [ -s $TRIBBLE_PID_FILE ] && kill -0 $(cat $TRIBBLE_PID_FILE) >/dev/null 2>&1; then
            start-stop-daemon --stop --quiet --oknodo --pidfile $TRIBBLE_PID_FILE || true
            sleep 1
        else
            log_warning_msg "${PROGRAM_NAME} daemon not running, attempting to start."
            rm -f $TRIBBLE_PID_FILE
        fi
        tribble_api_start
        ;;

  status)
        status_of_proc -p $TRIBBLE_PID_FILE "$DAEMON" tribble-api
        exit $?
        ;;
  *)
        echo "Usage: /etc/init.d/tribble-api {start|stop|restart|status}"
        exit 1
esac

exit 0
