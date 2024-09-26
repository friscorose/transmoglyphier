from rich_pixels import Pixels
from rich_pixels import Renderer
from rich_pixels import HalfcellRenderer

from rich.console import Console
from rich.segment import Segment
from rich.style import Style

import string
import PIL.Image
import PIL.ImageDraw

from typing import Callable, Tuple

RGBA = Tuple[int, int, int, int]
GetPixel = Callable[[Tuple[int, int]], RGBA]

class StrToPixels( Pixels ):

    @staticmethod
    def from_12string(
            input: str = "A",
            weight: int = 100,
            ) -> Pixels:

        image = PIL.Image.new(mode="RGB", size=(16,24) )
        glyph = PIL.ImageDraw.Draw( image )
        glyph.text( (0,-2), input, fill=(255,255,255), font_size=18 )
        fn = lambda x : 255 if x > weight else 0
        r_image = image.convert('L').point(fn, mode='1')
        
        segments = Pixels._segments_from_image(r_image, (8,12), renderer=HalfcellRenderer() )

        return Pixels.from_segments(segments)

    @staticmethod
    def from_string(
            input: str = "A",
            weight: int = 100,
            ) -> Pixels:

        image = PIL.Image.new(mode="RGB", size=(16,24) )
        glyph = PIL.ImageDraw.Draw( image )
        glyph.text( (0,-2), input, fill=(255,255,255), font_size=18 )
        fn = lambda x : 255 if x > weight else 0
        r_image = image.convert('L').point(fn, mode='1')
        
        segments = Pixels._segments_from_image(image, (8,12), renderer=SextantcellRenderer() )

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
        """calculate intensity approximation of an RGB PIL getpixel"""
        r,g,b,a = pixel
        return int( (0.2126*r + 0.7152*g + 0.0722*b)*a/255 )

    def _render_sextantcell(self, *, x: int, y: int, get_pixel: GetPixel) -> Segment:
        weight = 50
        style = Style.parse("white on black")
        block_sextant_base_UCP = 0x1FB00 - 0x1
        glyph_offset = 0
        #cons.print( get_pixel((x,y)) )

        #BLOCK SEXTANT-1 (+ 0 or 1)
        glyph_offset += 2**0 if self._get_intensity( get_pixel((x  ,y  )) ) >  weight else 0
        #BLOCK SEXTANT-2 (+ 0 or 2)
        glyph_offset += 2**1 if self._get_intensity( get_pixel((x+1,y  )) ) >  weight else 0
        #BLOCK SEXTANT-3 (+ 0 or 4)
        glyph_offset += 2**2 if self._get_intensity( get_pixel((x  ,y+1)) ) >  weight else 0
        #BLOCK SEXTANT-4 (+ 0 or 8)
        glyph_offset += 2**3 if self._get_intensity( get_pixel((x+1,y+1)) ) >  weight else 0
        #BLOCK SEXTANT-5 (+ 0 or 16)
        glyph_offset += 2**4 if self._get_intensity( get_pixel((x  ,y+2)) ) >  weight else 0
        #BLOCK SEXTANT-6 (+ 0 or 32)
        glyph_offset += 2**5 if self._get_intensity( get_pixel((x+1,y+2)) ) >  weight else 0
        
        if glyph_offset == 0:
            #special case for no pixels active, glyph -> " " 0x20
            glyph = chr( 0x20 )
        elif glyph_offset == 21:
            #special case for BLOCK SEXTANT-135, glyph -> "▌" 0x258C
            glyph = chr( 0x258C )
        elif glyph_offset == 42:
            #special case for BLOCK SEXTANT-246, glyph -> "▐" 0x2590
            glyph = chr( 0x2590 )
        elif glyph_offset == 127:
            #special case for BLOCK SEXTANT-123456, glyph -> "█" 0x2588
            glyph = chr( 0x2588 )
        else:
            if glyph_offset >= 21:
                glyph_offset -= 1
            if glyph_offset >= 42:
                glyph_offset -= 1
            glyph = chr( block_sextant_base_UCP + glyph_offset )
        
        #cons.print( glyph + str(glyph_offset) )
        return Segment( glyph, style )


cons = Console()
#pixels = StrToPixels.from_12string("A", 85)
#cons.print( pixels )
#cons.print( "\n" )
#pixels = StrToPixels.from_string("A", 85)
#cons.print( pixels )
#cons.print( "\n" )

for char in string.ascii_uppercase:
    pixels = StrToPixels.from_string(char, 85)
    cons.print( pixels )
    cons.print( "\n" )
