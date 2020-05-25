from simplekml import *


def fixed_str(self):
    """
    Monkey Patched Function
    This patch fixes a bug in simplekml version 1.2.7

    In the original code, angles are added to the buffer as shown below.
    This gives the data the wrong tag name and results in the data being
    wrongly printed like a tuple.
        for angle in self.gxangles:
            buf.append("<gx:angle>{0}</gx:angle>".format(angle))

    This has been corrected to:
        for angle in self.gxangles:
            angle_str = ' '.join(map(str, angle))
            buf.append("<gx:angles>{0}</gx:angles>".format(angle_str))
    """
    buf = ['<gx:Track>']
    for when in self.whens:
        buf.append("<when>{0}</when>".format(when))
    for angle in self.gxangles:
        angle_str = ' '.join(map(str, angle))
        buf.append("<gx:angles>{0}</gx:angles>".format(angle_str))
    for gxcoord in self.gxcoords:
        buf.append(
            ("<gx:coord>{0}</gx:coord>".format(gxcoord.__str__().replace(
                ',', ' '))))
    buf.append(super(GxTrack, self).__str__())
    buf.append('</gx:Track>')
    return "".join(buf)


GxTrack.__str__ = fixed_str
