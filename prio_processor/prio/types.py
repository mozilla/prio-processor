import click


class ByteStringType(click.ParamType):
    name = "byte-string"

    def convert(self, value, param, ctx):
        try:
            return bytes(value, "utf-8")
        except:
            self.fail("{} cannot be encoded into a bytestring".format(value))


BYTE_STRING = ByteStringType()
