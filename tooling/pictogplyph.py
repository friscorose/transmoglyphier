from rich_pixels import Pixels, Renderer
from typing import Callable, Tuple

from rich.console import Console
from rich.segment import Segment
from rich.style import Style

from PIL import Image, ImageDraw, ImageFont
import string


RGBA = Tuple[int, int, int, int]
GetPixel = Callable[[Tuple[int, int]], RGBA]

class OctantcellRenderer( Renderer ):
    """ Render to Block Octant in Unicode 16.0: Extend to braille glyphs? """

    def render( self, image: Image, resize: tuple[int, int] | None) -> list[Segment]:
        target_width = resize[0] if resize else image.size[0]
        if target_width % 2 != 0:
            target_width += 1

        target_height = resize[1] if resize else image.size[1]
        while target_height % 4 != 0:
            target_height += 1

        if image.size[0] != target_width or image.size[1] != target_height:
            resize = (target_width, target_height)

        return super().render(image, resize)

    def _get_range(self, height: int) -> range:
        return range(0, height, 4)

    def _render_line(
            self, *, line_index: int, width: int, get_pixel: GetPixel
            ) -> list[Segment]:
        line = []
        for x in range(0, width, 2):
            line.append(self._render_octantcell(x=x, y=line_index, get_pixel=get_pixel))
        return line

    def _get_intensity( self, pixel: GetPixel ) -> int:
        """calculate intensity approximation of an RGB PIL getpixel.
           https://en.wikipedia.org/wiki/Grayscale"""
        r,g,b,a = pixel
        return int( (0.2126*r + 0.7152*g + 0.0722*b)*a/255 )

    def _render_octantcell(self, *, x: int, y: int, get_pixel: GetPixel) -> Segment:
        weight = 126
        style = Style.parse("white on black")

        #Bit bang lookup table offset for BLOCK OCTANT-0 through BLOCK OCTANT-8 (equivalents)
        offset  = 2**0 if self._get_intensity( get_pixel((x  ,y  )) ) >  weight else 0
        offset += 2**1 if self._get_intensity( get_pixel((x+1,y  )) ) >  weight else 0
        offset += 2**2 if self._get_intensity( get_pixel((x  ,y+1)) ) >  weight else 0
        offset += 2**3 if self._get_intensity( get_pixel((x+1,y+1)) ) >  weight else 0
        offset += 2**4 if self._get_intensity( get_pixel((x  ,y+2)) ) >  weight else 0
        offset += 2**5 if self._get_intensity( get_pixel((x+1,y+2)) ) >  weight else 0
        offset += 2**6 if self._get_intensity( get_pixel((x  ,y+3)) ) >  weight else 0
        offset += 2**7 if self._get_intensity( get_pixel((x+1,y+3)) ) >  weight else 0
        
        glyph_lut=" 𜺨𜺫🮂𜴀▘𜴁𜴂𜴃𜴄▝𜴅𜴆𜴇𜴈▀𜴉𜴊𜴋𜴌🯦𜴍𜴎𜴏𜴐𜴑𜴒𜴓𜴔𜴕𜴖𜴗𜴘𜴙𜴚𜴛𜴜𜴝𜴞𜴟🯧𜴠𜴡𜴢𜴣𜴤𜴥𜴦𜴧𜴨𜴩𜴪𜴫𜴬𜴭𜴮𜴯𜴰𜴱𜴲𜴳𜴴𜴵🮅𜺣𜴶𜴷𜴸𜴹𜴺𜴻𜴼𜴽𜴾𜴿𜵀𜵁𜵂𜵃𜵄▖𜵅𜵆𜵇𜵈▌𜵉𜵊𜵋𜵌▞𜵍𜵎𜵏𜵐▛𜵑𜵒𜵓𜵔𜵕𜵖𜵗𜵘𜵙𜵚𜵛𜵜𜵝𜵞𜵟𜵠𜵡𜵢𜵣𜵤𜵥𜵦𜵧𜵨𜵩𜵪𜵫𜵬𜵭𜵮𜵯𜵰𜺠𜵱𜵲𜵳𜵴𜵵𜵶𜵷𜵸𜵹𜵺𜵻𜵼𜵽𜵾𜵿𜶀𜶁𜶂𜶃𜶄𜶅𜶆𜶇𜶈𜶉𜶊𜶋𜶌𜶍𜶎𜶏▗𜶐𜶑𜶒𜶓▚𜶔𜶕𜶖𜶗▐𜶘𜶙𜶚𜶛▜𜶜𜶝𜶞𜶟𜶠𜶡𜶢𜶣𜶤𜶥𜶦𜶧𜶨𜶩𜶪𜶫▂𜶬𜶭𜶮𜶯𜶰𜶱𜶲𜶳𜶴𜶵𜶶𜶷𜶸𜶹𜶺𜶻𜶼𜶽𜶾𜶿𜷀𜷁𜷂𜷃𜷄𜷅𜷆𜷇𜷈𜷉𜷊𜷋𜷌𜷍𜷎𜷏𜷐𜷑𜷒𜷓𜷔𜷕𜷖𜷗𜷘𜷙𜷚▄𜷛𜷜𜷝𜷞▙𜷟𜷠𜷡𜷢▟𜷣▆𜷤𜷥█"
                                                                                     
        return Segment( glyph_lut[offset], style )

class SextantcellRenderer( Renderer ):
    """ Render to Block Sextant in Symbols for Legacy Computing Unicode block """

    def render( self, image: Image, resize: tuple[int, int] | None) -> list[Segment]:
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

        return super().render(image, resize)

    def _get_range(self, height: int) -> range:
        return range(0, height, 3)

    def _render_line(
            self, *, line_index: int, width: int, get_pixel: GetPixel
            ) -> list[Segment]:
        line = []
        for x in range(0, width, 2):
            line.append(self._render_sextantcell(x=x, y=line_index, get_pixel=get_pixel))
        return line

    def _get_intensity( self, pixel: GetPixel ) -> int:
        """calculate intensity approximation of an RGB PIL getpixel.
           https://en.wikipedia.org/wiki/Grayscale"""
        r,g,b,a = pixel
        return int( (0.2126*r + 0.7152*g + 0.0722*b)*a/255 )

    def _render_sextantcell(self, *, x: int, y: int, get_pixel: GetPixel) -> Segment:
        weight = 126
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
                                                                                     
        return Segment( glyph_lut[offset], style )

class StrToPixels( Pixels ):
    """Extend Pixels to enable user specified font based string rendering with some PIL transforms"""

    @staticmethod
    def from_string(
            phrase: str = "",
            pic_renderer: Renderer = SextantcellRenderer(), 
            pic_rotate: float = 0.0,
            font_size: int = 11,
            font_path: str = "./DepartureMono-Regular.otf"
            ) -> Pixels:

        font = ImageFont.truetype( font_path, size=font_size )
        l,t,r,b = font.getbbox( phrase )
        pane = Image.new( '1', (r,b) )
        canvas = ImageDraw.Draw( pane )
        mask = [x for x in font.getmask(phrase, mode='1')]
        pane.putdata(mask)
        if pic_rotate != 0:
            pane = pane.rotate(pic_rotate, Image.NEAREST, expand = 1)
            l,t,r,b = pane.getbbox()
        segments = Pixels._segments_from_image(pane, (r,b), renderer=pic_renderer )

        return Pixels.from_segments(segments)

#Test Code Playground
if __name__ == "__main__":
    cons = Console()

    for char in string.ascii_uppercase:
        pixels = StrToPixels.from_string(char, pic_renderer=OctantcellRenderer())
        cons.print( pixels )
    print( "(Normal terminal font for comparison :-)\n" )
    cons.print( StrToPixels.from_string( "Hello World", pic_renderer=OctantcellRenderer() ) )
    cons.print( Pixels.from_image_path("./textual_logo_light.png", resize=(64,40), renderer=OctantcellRenderer()) )
