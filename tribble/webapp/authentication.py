from flask import request, redirect
from tribble.appsetup.start import LOG
from tribble.db.models import CloudAuth
from tribble.webapp import not_found


def cloudauth():
    """
    Authenticates a user with the Cloud System they are attempting to operate
    with. If authentication is successful, then the system will allow the user
    to deploy through the application to the provider.
    """
    from tribble.appsetup.start import LOG
    from tribble.webapp import pop_ts

    def decode(cipher, key, psw):
        """
        Attempt a decode of a password found in the database.
        This is a place holder currently pw is in Plane text
        """
        from tribble.appsetup import rosetta
        password = rosetta.decrypt(password=key,
                                   ciphertext=cipher)
        if password == psw:
            return True
        else:
            return False
    if request.method == 'HEAD':
        msg = 'Method Not Implemented'
        return not_found(message=msg, error=400)
    _rh = request.headers
    if not all([('x-user' in _rh),
                ('x-secretkey' in _rh),
                ('x-password' in _rh)]):
        return not_found(message='No Credentials Provided'), 401
    else:
        obj = CloudAuth.query.filter(CloudAuth.dcuser == _rh['x-user']).first()
        if obj:
            scrt = decode(cipher=obj.dcsecret,
                          key=_rh['x-secretkey'],
                          psw=_rh['x-password'])
            if not scrt:
                msg = 'No Valid Credentials Provided'
                return not_found(message=msg, error=401)
        else:
            msg = ('Verify x-user, x-secret, and x-password headers are present'
                   ' and correct')
            err = 401
            LOG.critical('Failed Authentication ==> Headers %s => Error Code %s'
                         % (_rh, err))
            return not_found(message=msg, error=err)
