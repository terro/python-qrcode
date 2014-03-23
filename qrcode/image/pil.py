# Try to import PIL in either of the two ways it can be installed.
try:
    from PIL import Image, ImageDraw
except ImportError:
    import Image
    import ImageDraw

import base64
import cStringIO
import qrcode.image.base

class PilImage(qrcode.image.base.BaseImage):
    """
    PIL image builder, default format is PNG.
    """
    kind = "PNG"

    def new_image(self, background, **kwargs):
        img = Image.new("RGB", (self.pixel_size, self.pixel_size), background)
        self._idr = ImageDraw.Draw(img)
        return img

    def drawrect(self, row, col, color):
        box = self.pixel_box(row, col)
        self._idr.rectangle(box, fill=color)

    def drawpartialrect(self, row, col, color, pos):
        box = self.pixel_box(row, col)
        box = (box[0][0], box[0][1], box[1][0]+1, box[1][1]+1)
        if pos == 0:
            sq = ((box[0]+box[2])/2, (box[1]+box[3])/2, box[2], box[3])
        elif pos == 1:
            sq = (box[0], (box[1]+box[3])/2, (box[0]+box[2])/2, box[3])
        elif pos == 2:
            sq = (box[0], box[1], (box[0]+box[2])/2, (box[1]+box[3])/2)
        elif pos == 3:
            sq = ((box[0]+box[2])/2, box[1], box[2], (box[1]+box[3])/2)
        self._idr.rectangle(sq, fill=color)

    def drawpie(self, row, col, color, back, pos, offset1=0, offset2=0):
        self.drawpartialrect(row, col, back, pos)
        box = self.pixel_box(row, col)
        box = (box[0][0]+offset1, box[0][1]+offset2, box[1][0]+1, box[1][1]+1)
        self._idr.pieslice(box, 90*pos, 90*(pos+1), fill=color)

    def drawround(self, row, col, color):
        box = self.pixel_box(row, col)
        box = (box[0][0], box[0][1], box[1][0]+1, box[1][1]+1)
        self._idr.ellipse(box, fill=color)

    def save(self, stream, kind=None):
        if kind is None:
            kind = self.kind
        self._img.save(stream, kind)

    def add_logo(self, logo):
        image_string = cStringIO.StringIO(base64.b64decode(logo))
        img = Image.open(image_string)
        new_size = int(self.pixel_size / 6.2) * 2
        img = img.resize((new_size, new_size))
        center = self.pixel_size / 2
        self._img.paste(img, (center - new_size/2, center - new_size/2, center + new_size/2, center + new_size/2))

    def __getattr__(self, name):
        return getattr(self._img, name)
