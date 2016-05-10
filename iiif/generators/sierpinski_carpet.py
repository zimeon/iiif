"""Image generator for a Sierpinski Carpet.

See for example <https://en.wikipedia.org/wiki/Sierpinski_carpet>
"""


def _middle(x, y):
    """PRIVATE function to return True is x==1 and y==1.

    x,y in {0,1,2}, returns True if x==1 and y==1, the middle of the
    nine squares in a 3x3 square
    """
    return (x == 1 and y == 1)


class PixelGen(object):
    """Pixel generation class."""

    def __init__(self):
        """Set size."""
        self.sz = 3**8

    @property
    def size(self):
        """Image size property."""
        return (self.sz, self.sz)

    @property
    def background_color(self):
        """Background color property."""
        return (255, 255, 255)

    def pixel(self, x, y, size=None):
        """Return color for a pixel."""
        if (size is None):
            size = self.sz
        # Have we go to the smallest element?
        if (size <= 3):
            if (_middle(x, y)):
                return (None)
            else:
                return (0, 0, 0)
        divisor = size // 3
        if (_middle(x // divisor, y // divisor)):
            return None
        return self.pixel(x % divisor, y % divisor, divisor)
