from pathlib import Path
from PIL import Image, ImageTk
from xml.dom import minidom
from tkinter import CENTER

from .controlpoint import Controlpoint
from .geometry import Point

class Component(object):
    __tag__ = 'component'

    def __init__(self, canvas, name, rootdir=''):
        self.canvas = canvas
        self.name = name
        root = Path(rootdir).joinpath(str(self.name))
        png = str(root)+'.png'
        svg = str(root)+'.svg'

        print(F"Creating Component `{self.name}' from files at `{rootdir}': img `{png}'")
        self.img = Image.open(png).convert("RGBA")
        print(F"Created {self.img} for Image")
        self.photoimg = ImageTk.PhotoImage(self.img)
        print(F"Created ImageTk.PhotoImage {self.photoimg} for PhotoImage")

        doc = minidom.parse(svg)
        self.controlpoints = { c.getAttribute('id') : 
                Controlpoint(self, c.getAttribute('id'), Point(c.getAttribute('cx'),c.getAttribute('cy'))) 
                for c in doc.getElementsByTagName('circle') if c.getAttribute('class') == 'node'}

        self.position = Point(0,0)

        self.__tag = str(self.photoimg)

    def newComponentConstructor(self):
        def newInit(obj, comp_id):
            obj.canvas = self.canvas
            obj.name = self.name
            obj.img = self.img
            obj.photoimg = self.photoimg
            obj.controlpoints = self.controlpoints
            obj.position = self.position
            obj.comp_id = comp_id
            obj.__tag = str(comp_id)

        return type(f"{self.name}Component", (Component,), {
            '__init__' : newInit,
            'img' : self.img,
            'photoimg' : self.photoimg
            })

    @property
    def tag(self):
        return self.__tag;

    def draw(self, p):
        self.position = p
        self.img_id = self.canvas.create_image(p.x, p.y, anchor=CENTER, image=self.photoimg, tags=(self.__class__.__tag__,'noparent',self.tag))
        for k,c in self.controlpoints.items():
            c.canvas_id = self.canvas.create_circle(
                    c.position.x + self.position.x - self.img.size[0]/2, c.position.y + self.position.y - self.img.size[1]/2 , c.radius,
                    tags=(c.__class__.__tag__,self.tag,c.tag), fill=c.colour)
        return self.comp_id

    def rotate(self, step):
        step %= 4
        degrees = 90*step
        self.photoimg = ImageTk.PhotoImage(self.img.rotate(degrees))
        self.canvas.delete(self.img_id)
        self.draw(self.position)

