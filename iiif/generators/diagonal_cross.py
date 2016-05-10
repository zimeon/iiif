"""Image generator for fractal diagonal cross."""


def _not_diagonal(x, y):
    """PRIVATE function to return element in 3x3 square is diagonal.

    x,y in {0,1,2}, returns 1 if x,y is not corner or middle
    """
    return((x + 3 * y) % 2)


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
            if (_not_diagonal(x, y)):
                return None
            else:
                return (0, 0, 0)
        divisor = size // 3
        if (_not_diagonal(x // divisor, y // divisor)):
            return None
        return self.pixel(x % divisor, y % divisor, divisor)
