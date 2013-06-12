config_file = """
# ================================= NOTES ======================================
# Use this configuration file to store sensitive information
# The config file REQUIRES at least ONE section for functionality
# Section names don't matter, however they are nice for oganizing data
# This is a sample file not all variables are needed. Use what you want too.

# Place me in "/etc/Tribble/" with permissions "0600" or "0400"

# Not all variables are needed, simply use what you need to.

# Available System variables :
# ------------------------------------------------------------------------------
# DB_USERNAME = databaseUsername
# DB_PASSWORD = superSecretInformation
# DB_HOST = localhost
# DB_PORT = portNumber
# DB_NAME = databaseName
# DB_ENGINE = mysql
# BIND_PORT = portNumber
# BIND_HOST = localhost
# connection_pool = numberOfAvailableConnections
# log_level = {debug, info, warn, critical, error}
# debug_mode = True | False
# ================================= NOTES ======================================

[basic]
log_level = info
DB_USERNAME = tribble_db_username
DB_PASSWORD = tribble_password
DB_HOST = localhost
DB_PORT = 3306
DB_NAME = tribble_db_name
DB_ENGINE = mysql

# Using Debug Makes the system VERY Verbose
# debug_mode = True

"""

tribble_init = """
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

# What is the Directory to your server installation of HYPERIC
AGENT_APP="/usr/local/bin/tribbleapi"

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
    $AGENT_APP $CONFIG --start
}

stop() {
    $AGENT_APP $CONFIG --stop
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

"""