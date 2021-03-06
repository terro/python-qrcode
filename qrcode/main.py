from qrcode import constants, util
from qrcode.image.base import BaseImage

import six


def make(data=None, **kwargs):
    qr = QRCode(**kwargs)
    qr.add_data(data)
    return qr.make_image()


class QRCode:

    def __init__(self, version=None,
                 error_correction=constants.ERROR_CORRECT_H,
                 box_size=16, border=2,
                 image_factory=None,
                 foreground="black",
                 background="white",
                 probe_in="black",
                 probe_out="black",
                 style="default",
                 logo=None):
        self.version = version and int(version)
        self.error_correction = int(error_correction)
        self.box_size = int(box_size)
        # Spec says border should be at least four boxes wide, but allow for
        # any (e.g. for producing printable QR codes).
        self.border = int(border)
        self.image_factory = image_factory
        self.foreground = foreground
        self.background = background
        self.probe_in = probe_in
        self.probe_out = probe_out
        self.style = style
        self.logo = logo
        if image_factory is not None:
            assert issubclass(image_factory, BaseImage)
        self.clear()

    def clear(self):
        """
        Reset the internal data.
        """
        self.modules = None
        self.modules_count = 0
        self.data_cache = None
        self.data_list = []

    def add_data(self, data, optimize=20):
        """
        Add data to this QR Code.

        :param optimize: Data will be split into multiple chunks to optimize
            the QR size by finding to more compressed modes of at least this
            length. Set to ``0`` to avoid optimizing at all.
        """
        if isinstance(data, util.QRData):
            self.data_list.append(data)
        else:
            if optimize:
                self.data_list.extend(util.optimal_data_chunks(data))
            else:
                self.data_list.append(util.QRData(data))
        self.data_cache = None

    def make(self, fit=True):
        """
        Compile the data into a QR Code array.

        :param fit: If ``True`` (or if a size has not been provided), find the
            best fit for the data to avoid data overflow errors.
        """
        if fit or not self.version:
            self.best_fit(start=self.version)
        self.makeImpl(False, self.best_mask_pattern())

    def makeImpl(self, test, mask_pattern):
        self.modules_count = self.version * 4 + 17
        self.modules = [None] * self.modules_count

        for row in range(self.modules_count):

            self.modules[row] = [None] * self.modules_count

            for col in range(self.modules_count):
                self.modules[row][col] = None   # (col + row) % 3

        self.setup_position_probe_pattern(0, 0)
        self.setup_position_probe_pattern(self.modules_count - 7, 0)
        self.setup_position_probe_pattern(0, self.modules_count - 7)
        self.sutup_position_adjust_pattern()
        self.setup_timing_pattern()
        self.setup_type_info(test, mask_pattern)

        if self.version >= 7:
            self.setup_type_number(test)

        if self.data_cache is None:
            self.data_cache = util.create_data(
                self.version, self.error_correction, self.data_list)
        self.map_data(self.data_cache, mask_pattern)

    def setup_position_probe_pattern(self, row, col):
        for r in range(-1, 8):

            if row + r <= -1 or self.modules_count <= row + r:
                continue

            for c in range(-1, 8):

                if col + c <= -1 or self.modules_count <= col + c:
                    continue

                if (0 <= r <= 6 and (c == 0 or c == 6)
                        or (0 <= c <= 6 and (r == 0 or r == 6))):
                    self.modules[row + r][col + c] = (True, constants.POSITION_PROBE_OUT)
                elif 2 <= r <= 4 and 2 <= c <= 4:
                    self.modules[row + r][col + c] = (True, constants.POSITION_PROBE_IN)
                else:
                    self.modules[row + r][col + c] = (False, constants.DATA)

    def best_fit(self, start=None):
        """
        Find the minimum size required to fit in the data.
        """
        self.data_cache, self.version = (
            util.BestFit(self.error_correction, self.data_list)
            .data_and_version(start))
        return self.version

    def best_mask_pattern(self):
        """
        Find the most efficient mask pattern.
        """
        min_lost_point = 0
        pattern = 0

        for i in range(8):
            self.makeImpl(True, i)

            lost_point = util.lost_point(self.modules)

            if i == 0 or min_lost_point > lost_point:
                min_lost_point = lost_point
                pattern = i

        return pattern

    def print_tty(self, out=None):
        """
        Output the QR Code to a TTY (potentially useful for debugging).

        If the data has not been compiled yet, make it first.
        """
        if out is None:
            import sys
            out = sys.stdout

        if not out.isatty():
            raise OSError("Not a tty")

        if self.data_cache is None:
            self.make()

        modcount = self.modules_count
        out.write("\x1b[1;47m" + (" " * (modcount * 2 + 4)) + "\x1b[0m\n")
        for r in range(modcount):
            out.write("\x1b[1;47m  \x1b[40m")
            for c in range(modcount):
                if self.modules[r][c][0]:
                    out.write("  ")
                else:
                    out.write("\x1b[1;47m  \x1b[40m")
            out.write("\x1b[1;47m  \x1b[0m\n")
        out.write("\x1b[1;47m" + (" " * (modcount * 2 + 4)) + "\x1b[0m\n")
        out.flush()

    def make_image(self, image_factory=None, **kwargs):
        """
        Make an image from the QR Code data.

        If the data has not been compiled yet, make it first.
        """
        if self.data_cache is None:
            self.make()

        if image_factory is not None:
            assert issubclass(image_factory, BaseImage)
        else:
            image_factory = self.image_factory
            if image_factory is None:
                # Use PIL by default
                from qrcode.image.pil import PilImage
                image_factory = PilImage

        im = image_factory(
            self.border, self.modules_count, self.box_size, self.background, **kwargs)
        for r in range(self.modules_count):
            for c in range(self.modules_count):
                if self.modules[r][c][0]:
                    if self.modules[r][c][1] == constants.DATA:
                        self.draw_block(im, r, c, self.foreground)
                    elif self.modules[r][c][1] == constants.POSITION_PROBE_IN:
                        self.draw_block(im, r, c, self.probe_in)
                    elif self.modules[r][c][1] == constants.POSITION_PROBE_OUT:
                        self.draw_block(im, r, c, self.probe_out)
                elif self.style == 'water':
                    self.drawwater_inverse(im, r, c)
        if self.logo:
            im.add_logo(self.logo)
        return im

    def draw_block(self, im, r, c, color):
        if self.style == 'default':
            im.drawrect(r, c, color)
        elif self.style == 'round':
            im.drawround(r, c, color)
        elif self.style == 'water':
            self.drawwater(im, r, c, color)

    def drawwater_inverse(self, im, r, c):
        n = self.modules_count
        color = self.foreground
        if 0 <= r < 7 and (0 <= c < 7 or n - 7 <= c < n)\
           or n - 7 <= r < n and 0 <= c < 7:
            color = self.probe_out
        if self.occupy(r-1, c) and self.occupy(r, c-1):
            im.drawpie(r, c, self.background, color, 2, offset1=2, offset2=2)
        if self.occupy(r-1, c) and self.occupy(r, c+1):
            im.drawpie(r, c, self.background, color, 3, offset2=2)
        if self.occupy(r+1, c) and self.occupy(r, c-1):
            im.drawpie(r, c, self.background, color, 1, offset1=2)
        if self.occupy(r+1, c) and self.occupy(r, c+1):
            im.drawpie(r, c, self.background, color, 0)

    def occupy(self, r, c):
        n = self.modules_count
        return 0 <= c < n and 0 <= r < n and self.modules[r][c][0]

    def drawwater(self, im, r, c, color):
        if self.occupy(r, c-1) or self.occupy(r-1, c) or self.occupy(r-1, c-1):
            im.drawpartialrect(r, c, color, 2)
        else:
            im.drawpie(r, c, color, self.background, 2)
        if self.occupy(r, c+1) or self.occupy(r-1, c) or self.occupy(r-1, c+1):
            im.drawpartialrect(r, c, color, 3)
        else:
            im.drawpie(r, c, color, self.background, 3)
        if self.occupy(r, c-1) or self.occupy(r+1, c) or self.occupy(r+1, c-1):
            im.drawpartialrect(r, c, color, 1)
        else:
            im.drawpie(r, c, color, self.background, 1)
        if self.occupy(r, c+1) or self.occupy(r+1, c) or self.occupy(r+1, c+1):
            im.drawpartialrect(r, c, color, 0)
        else:
            im.drawpie(r, c, color, self.background, 0)

    def setup_timing_pattern(self):
        for r in range(8, self.modules_count - 8):
            if self.modules[r][6] is not None:
                continue
            self.modules[r][6] = ((r % 2 == 0), constants.DATA)

        for c in range(8, self.modules_count - 8):
            if self.modules[6][c] is not None:
                continue
            self.modules[6][c] = ((c % 2 == 0), constants.DATA)

    def sutup_position_adjust_pattern(self):
        pos = util.pattern_position(self.version)

        for i in range(len(pos)):

            for j in range(len(pos)):

                row = pos[i]
                col = pos[j]

                if self.modules[row][col] is not None:
                    continue

                for r in range(-2, 3):

                    for c in range(-2, 3):

                        if (r == -2 or r == 2 or c == -2 or c == 2 or
                                (r == 0 and c == 0)):
                            self.modules[row + r][col + c] = (True, constants.DATA)
                        else:
                            self.modules[row + r][col + c] = (False, constants.DATA)

    def setup_type_number(self, test):
        bits = util.BCH_type_number(self.version)

        for i in range(18):
            mod = (not test and ((bits >> i) & 1) == 1)
            self.modules[i // 3][i % 3 + self.modules_count - 8 - 3] = (mod, constants.DATA)

        for i in range(18):
            mod = (not test and ((bits >> i) & 1) == 1)
            self.modules[i % 3 + self.modules_count - 8 - 3][i // 3] = (mod, constants.DATA)

    def setup_type_info(self, test, mask_pattern):
        data = (self.error_correction << 3) | mask_pattern
        bits = util.BCH_type_info(data)

        # vertical
        for i in range(15):

            mod = (not test and ((bits >> i) & 1) == 1)

            if i < 6:
                self.modules[i][8] = (mod, constants.DATA)
            elif i < 8:
                self.modules[i + 1][8] = (mod, constants.DATA)
            else:
                self.modules[self.modules_count - 15 + i][8] = (mod, constants.DATA)

        # horizontal
        for i in range(15):

            mod = (not test and ((bits >> i) & 1) == 1)

            if i < 8:
                self.modules[8][self.modules_count - i - 1] = (mod, constants.DATA)
            elif i < 9:
                self.modules[8][15 - i - 1 + 1] = (mod, constants.DATA)
            else:
                self.modules[8][15 - i - 1] = (mod, constants.DATA)

        # fixed module
        self.modules[self.modules_count - 8][8] = ((not test), constants.DATA)

    def map_data(self, data, mask_pattern):
        inc = -1
        row = self.modules_count - 1
        bitIndex = 7
        byteIndex = 0

        mask_func = util.mask_func(mask_pattern)

        data_len = len(data)

        for col in six.moves.xrange(self.modules_count - 1, 0, -2):

            if col <= 6:
                col -= 1

            col_range = (col, col-1)

            while True:

                for c in col_range:

                    if self.modules[row][c] is None:

                        dark = False

                        if byteIndex < data_len:
                            dark = (((data[byteIndex] >> bitIndex) & 1) == 1)

                        if mask_func(row, c):
                            dark = not dark

                        self.modules[row][c] = (dark, constants.DATA)
                        bitIndex -= 1

                        if bitIndex == -1:
                            byteIndex += 1
                            bitIndex = 7

                row += inc

                if row < 0 or self.modules_count <= row:
                    row -= inc
                    inc = -inc
                    break

    def get_matrix(self):
        """
        Return the QR Code as a multidimensonal array, including the border.

        To return the array without a border, set ``self.border`` to 0 first.
        """
        if self.data_cache is None:
            self.make()

        if not self.border:
            return self.modules

        width = len(self.modules) + self.border*2
        code = [[False]*width] * self.border
        x_border = [False]*self.border
        for module in self.modules:
            tmp = map(lambda x: x[0], module)
            code.append(x_border + tmp + x_border)
        code += [[False]*width] * self.border

        return code