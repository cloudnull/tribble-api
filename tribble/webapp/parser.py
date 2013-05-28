from flask.ext.restful import reqparse

def schematics(json):
    def string(value):
        if not isinstance(value, str):
            raise ValueError("%s is not String" % value)
        return value

    def integer(value):
        if not isinstance(value, int):
            raise ValueError("%s is not Integer" % value)
        return value

    parser = reqparse.RequestParser()
    parser.add_argument('', type=string)
    parser.add_argument('', type=integer)
    args = parser.parse_args()
