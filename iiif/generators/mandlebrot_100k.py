"""Image generator for Mandlebrot set.

Ref: <http://www.karlsims.com/julia.html>
"""

import cmath


class PixelGen(object):
    """Pixel generation classfor Mandlebrot set."""

    def __init__(self):
        """Set size."""
        self.scale = 25000.0
        self.xoffset = self.scale * 2.5
        self.yoffset = self.scale * 2
        self.sz = int(self.scale * 4 + 1)
        # Define maximum number of iterations and scale color
        # accordingly to give red=255 at that number
        self.max_iter = 50
        self.shade_factor = int(255 / (self.max_iter + 1))
        # Default constanc
        self.c = complex(0, 0)

    @property
    def size(self):
        """Image size property."""
        return (self.sz, self.sz)

    @property
    def background_color(self):
        """Background color property."""
        return (255, 255, 255)

    def set_c(self, z):
        """Set constant for Mandlebrot iteration.

        The initial coordinate z is passed in and for the
        Mandlebrot set we set c=z. For a particular julia
        set we give c a constant value
        """
        self.c = z

    def color(self, n):
        """Color of pixel that reached limit after n iterations.

        Returns a color tuple for use with PIL, tending toward
        red as we tend toward self.max_iter iterations.
        """
        red = int(n * self.shade_factor)
        if (red > 255):
            red = 255
        return (red, 50, 100)

    def mpixel(self, z, n=0):
        """Iteration in Mandlebrot coordinate z."""
        z = z * z + self.c
        if (abs(z) > 2.0):
            return self.color(n)
        n += 1
        if (n > self.max_iter):
            return None
        return self.mpixel(z, n)

    def pixel(self, ix, iy):
        """Return color for a pixel.

        Does translation from image coordinates (ix,iy) into
        the complex plane coordinate z = x+yi, and then calls
        self.mpixel(z) to find the color at point z.
        """
        x = (ix - self.xoffset + 0.5) / self.scale
        y = (iy - self.yoffset + 0.5) / self.scale
        z = complex(x, y)
        self.set_c(z)
        return self.mpixel(z)
