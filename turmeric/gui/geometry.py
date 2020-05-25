from collections import namedtuple

class Point(namedtuple('Point','x y')):
    def __init__(self, x,y):
        self.__x = int(x)
        self.__y = int(y)

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, i):
        self.__x = int(i)

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, i):
        self.__y = int(i)

