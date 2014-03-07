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


def ret_size(conn, specs):
    """Return a size object matched by the side ID.

    :param conn: ``object``
    :param specs: ``dict``
    :return: ``object``
    """
    size = [
        sz for sz in conn.list_sizes()
        if str(sz.id) == str(specs.get('size_id'))
    ]
    if not size:
        size = str(specs.get('size_id'))
        raise tribble.NoSizeFound('Size ID %s not found' % size)
    else:
        return size[0]


def ret_image(conn, specs):
    """Return an Image object matched by the image ID.

    :param conn: ``object``
    :param specs: ``dict``
    :return: ``object``
    """
    image = [
        im for im in conn.list_images()
        if str(im.id) == str(specs.get('image_id'))
    ]
    if not image:
        image = str(specs.get('image_id'))
        raise tribble.NoImageFound('Image ID %s not found' % image)
    else:
        return image[0]
