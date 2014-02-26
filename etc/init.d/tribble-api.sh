#!/usr/bin/env bash
### BEGIN INIT INFO
# Provides:          tribbleapi
# Required-Start:    $local_fs $remote_fs $network $syslog $named
# Required-Stop:     $local_fs $remote_fs $network $syslog $named
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start Tribble daemon at boot time.
### END INIT INFO

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# What is the Name of this Script, and what are we starting
PROGRAM="Tribble API"

# What is the Directory to your server installation
AGENT_APP="/usr/local/bin/tribble-api"

### -------------------------------------------------------------- ###
###    DO NOT EDIT THIS AREA UNLESS YOU KNOW WHAT YOU ARE DOING    ###
### -------------------------------------------------------------- ###

if [ "$(id -u)" != "0" ]; then
    echo "This script must be run as ROOT"
    echo "You have attempted to run this as $USER"
    echo "use su -c "" or sudo or change to root and try again."
    exit 0
fi

start() {
    $AGENT_APP --start
}

stop() {
    $AGENT_APP --stop
}

case "$1" in
    start)
        start
        ;;

    stop)
        stop
        ;;

    status)
        $AGENT_APP --status
        ;;

    restart)
        stop
        sleep 1
        start
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|status}" >&2
        ;;
esac

EXITCODE=$(echo $?)
echo $EXITCODE | logger
exit $EXITCODE