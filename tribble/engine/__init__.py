# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import tribble


def ipvfour_validator(host_ip):
    """
    Validate the IP addresses that have been provided to it
    """
    try:
        host_ip = host_ip.strip().split(".")
    except AttributeError:
        return False
    try:
        return len(host_ip) == 4 and all(int(octet) < 256 for octet in host_ip)
    except ValueError:
        return False


def scan_port(log, oper, port):
    """
    Scan the Ports that have been Provided
    """
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((oper, int(port)))
        if not (result == 0) or (result == 35):
            log.warn('port closed on "%s:%s"' % (oper, port))
            raise Exception('Port Closed for IP')
    except Exception, exp:
        log.warn('error %s%s ==> %s' % (oper, port, exp))
        return False
    else:
        return True
    finally:
        sock.close()


def ipsopenport(log, instance, specs):
    hosts = []
    _ips = instance.get('public_ips', []) + instance.get('private_ips', [])
    ips = [_ip for _ip in _ips if ipvfour_validator(_ip)]
    for i_p in ips:
        if scan_port(log=log, oper=i_p, port=specs.get('port', '22')):
            hosts.append(i_p)
    return hosts


def ret_size(conn, specs):
    size = [
        sz for sz in conn.list_sizes()
        if str(sz.id) == str(specs.get('size_id'))
    ]
    if not size:
        raise tribble.NoSizeFound('Size not found')
    else:
        return size[0]


def ret_image(conn, specs):
    image = [
        im for im in conn.list_images()
        if str(im.id) == str(specs.get('image_id'))
    ]
    if not image:
        raise tribble.NoImageFound('Image not found')
    else:
        return image[0]
