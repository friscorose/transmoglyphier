from rich_pixels import Pixels
from rich_pixels import Renderer
from rich_pixels import HalfcellRenderer

from rich.console import Console
from rich.segment import Segment
from rich.style import Style

import string
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

from typing import Callable, Tuple

RGBA = Tuple[int, int, int, int]
GetPixel = Callable[[Tuple[int, int]], RGBA]

class StrToPixels( Pixels ):

    @staticmethod
    def from_string(
            phrase: str = "A",
            font_path: str = "./DepartureMono-Regular.woff"
            ) -> Pixels:

        font = PIL.ImageFont.truetype( font_path, size=11 )
        l,t,r,b = font.getbbox( phrase )
        pane = PIL.Image.new( '1', (r,b) )
        canvas = PIL.ImageDraw.Draw( pane )
        mask = [x for x in font.getmask(phrase, mode='1')]
        pane.putdata(mask)
        segments = Pixels._segments_from_image(pane, (r,b), renderer=SextantcellRenderer() )

        return Pixels.from_segments(segments)

class SextantcellRenderer( Renderer ):
    """ Render to Block Sextant in Symbols for Legacy Computing Unicode block """

    def render( self, image: PIL.Image, resize: tuple[int, int] | None) -> list[Segment]:
        target_height = resize[1] if resize else image.size[1]
        if target_height % 3 != 0:
            target_height += 1
            if target_height % 3 != 0:
                target_height += 1

        target_width = resize[0] if resize else image.size[0]
        if target_width % 2 != 0:
            target_width += 1

        if image.size[0] != target_width or image.size[1] != target_height:
            resize = (target_width, target_height)

        #cons.print( "renderer" )
        #not perfect... maybe
        return super().render(image, resize)

    def _get_range(self, height: int) -> range:
        return range(0, height, 3)

    def _render_line(
            self, *, line_index: int, width: int, get_pixel: GetPixel
            ) -> list[Segment]:
        #cons.print( "render line of "+str(width) )
        line = []
        for x in range(0, width, 2):
           # cons.print( "render line of "+str(width) + " at " + str( x ) )
            line.append(self._render_sextantcell(x=x, y=line_index, get_pixel=get_pixel))
        return line

    def _get_intensity( self, pixel: GetPixel ) -> int:
        """calculate intensity approximation of an RGB PIL getpixel.
           https://en.wikipedia.org/wiki/Grayscale"""
        r,g,b,a = pixel
        return int( (0.2126*r + 0.7152*g + 0.0722*b)*a/255 )

    def _render_sextantcell(self, *, x: int, y: int, get_pixel: GetPixel) -> Segment:
        weight = 10
        style = Style.parse("white on black")

        #BLOCK SEXTANT-1 (+ 0 or 1)
        offset  = 2**0 if self._get_intensity( get_pixel((x  ,y  )) ) >  weight else 0
        #BLOCK SEXTANT-2 (+ 0 or 2)
        offset += 2**1 if self._get_intensity( get_pixel((x+1,y  )) ) >  weight else 0
        #BLOCK SEXTANT-3 (+ 0 or 4)
        offset += 2**2 if self._get_intensity( get_pixel((x  ,y+1)) ) >  weight else 0
        #BLOCK SEXTANT-4 (+ 0 or 8)
        offset += 2**3 if self._get_intensity( get_pixel((x+1,y+1)) ) >  weight else 0
        #BLOCK SEXTANT-5 (+ 0 or 16)
        offset += 2**4 if self._get_intensity( get_pixel((x  ,y+2)) ) >  weight else 0
        #BLOCK SEXTANT-6 (+ 0 or 32)
        offset += 2**5 if self._get_intensity( get_pixel((x+1,y+2)) ) >  weight else 0
        
        glyph_lut = " 🬀🬁🬂🬃🬄🬅🬆🬇🬈🬉🬊🬋🬌🬍🬎🬏🬐🬑🬒🬓▌🬔🬕🬖🬗🬘🬙🬚🬛🬜🬝🬞🬟🬠🬡🬢🬣🬤🬥🬦🬧▐🬨🬩🬪🬫🬬🬭🬮🬯🬰🬱🬲🬳🬴🬵🬶🬷🬸🬹🬺🬻█"
                                                                                     
        #cons.print( glyph_lut[offset] + str(offset) )
        return Segment( glyph_lut[offset], style )

#
cons = Console()
#pixels = StrToPixels.from_12string("A", 85)
#cons.print( pixels )
#cons.print( "\n" )
#pixels = StrToPixels.from_string("A", 85)
#cons.print( pixels )
#cons.print( "\n" )

for char in string.ascii_uppercase:
    pixels = StrToPixels.from_string(char)
    cons.print( pixels )
    cons.print( "\n" )
cons.print( StrToPixels.from_string( "Hello World" ) )
print( "(Normal terminal font for comparison :-)" )
