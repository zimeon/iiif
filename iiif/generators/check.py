"""Image generator for 3x3 check pattern with self-similar repeat."""

def _num(x,y):
    """PRIVATE function to return cell number in 3x3 square, 1..9."""
    return(x+3*y+1)

class PixelGen(object):
    """Pixel generation class."""

    def __init__(self):
        """Set size."""
        self.sz = 3**9 #19k
        #self.sz = 3**10 #54k

    @property
    def size(self):
        """Image size property."""
        return (self.sz,self.sz)

    @property
    def background_color(self):
        """Background color property."""
        return (255,255,255)

    def pixel(self,x,y,size=None,red=0):
        """Return color for a pixel.

        The paremeter size is used to recursively follow down to smaller
        and smaller middle squares (number 5). The paremeter red is used
        to shade from black to red going toward the middle of the figure.
        """
        if (size is None):
            size = self.sz
        # Have we go to the smallest element?
        if (size<=3):
            if (_num(x,y)%2):
                return (red,0,0)
            else:
                return None
        divisor = size//3
        n = _num(x//divisor,y//divisor)
        if (n==5):
            # Middle square further divided
            return self.pixel(x%divisor,y%divisor,divisor,red+30)
        elif (n%2):
            return (red,0,0)
        else:
            return None
