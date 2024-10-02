from rich_pixels import Pixels, Renderer
from typing import Callable, Tuple

from rich.console import Console
from rich.segment import Segment
from rich.style import Style

from PIL import Image, ImageDraw, ImageFont
import string


RGBA = Tuple[int, int, int, int]
GetPixel = Callable[[Tuple[int, int]], RGBA]

class CellRenderer( Renderer ):
    def __init__( self, *args, **kwargs ) -> None:
        self.weight = kwargs.pop('Weight', 96)
        self.x_pixels = kwargs.pop( 'x_pixels', 2 )
        self.y_pixels = kwargs.pop( 'y_pixels', 4 )
        super().__init__( *args, **kwargs )

    def render( self, image: Image, resize: tuple[int, int] | None) -> list[Segment]:
        target_width = resize[0] if resize else image.size[0]
        if target_width % self.x_pixels != 0:
            target_width += 1

        target_height = resize[1] if resize else image.size[1]
        while target_height % self.y_pixels != 0:
            target_height += 1

        if image.size[0] != target_width or image.size[1] != target_height:
            resize = (target_width, target_height)

        return super().render(image, resize)

    def _get_intensity( self, pixel: GetPixel ) -> int:
        """calculate intensity approximation of an RGB PIL getpixel.
           https://en.wikipedia.org/wiki/Grayscale"""
        r,g,b,a = pixel
        return int( (0.2126*r + 0.7152*g + 0.0722*b)*a/255 )

    def _get_range(self, height: int) -> range:
        return range(0, height, self.y_pixels)
    
    def _get_cellpix( self, x: int, y: int, get_pixel: GetPixel ) -> list:
        #pixlist index is the power of 2 for the pixel bit offset
        pixlist = []
        for y_idx in range( self.y_pixels ):
            pixlist.append( get_pixel((x    , y + y_idx)) )
            pixlist.append( get_pixel((x + 1, y + y_idx)) )
        return pixlist

    def _get_color(self, pixel: tuple ) -> str | None:
        r, g, b, a = pixel
        return f"rgb({r},{g},{b})" if a > 0 else None

    def _get_glyph_info( self, x: int, y: int, get_pixel: GetPixel ) -> list:
        style = None
        offset = 0
        brightlist = []
        darklist = []
        colors = []
        for exp, pixel in enumerate( self._get_cellpix(x, y, get_pixel) ):
            if self._get_intensity( pixel ) > self.weight:
                brightlist.append( pixel )
                offset += 2**exp
            else:
                darklist.append( pixel )

        if darklist:
            bg_color = self._get_color( tuple( [int(sum(y) / len(y)) for y in zip(*darklist)] ) )
        else:
            bg_color = "default"
        if brightlist:
            fg_color = self._get_color( tuple( [int(sum(y) / len(y)) for y in zip(*brightlist)] ) )
        else:
            fg_color = "default"
        colors.append( fg_color or "" )
        colors.append( bg_color or "" )
        style = Style.parse(" on ".join(colors)) 
        return( offset, style )

    def _get_glyph_info2( self, x: int, y: int, get_pixel: GetPixel ) -> list:
        style = None
        colors = []
        offset = 0
        celllist = self._get_cellpix(x,y,get_pixel)
        cellimg = Image.new( 'RGBA', (self.x_pixels, self.y_pixels) )
        cellimg.putdata( celllist )
        cellbiimg = cellimg.convert( 'P', dither=None, colors=2 )
        palette = cellbiimg.getpalette()
        cellbilist = list( cellbiimg.getdata() )
        #print( list(cellimg.getdata()) )
        #print( cellbilist )
        #print( list(palette) )
        for exp, pixel in enumerate( cellbilist ):
            if pixel:
                offset += 2**exp
        bg_color = self._get_color( (palette[0], palette[1], palette[2], 255) )
        fg_color = self._get_color( (palette[3], palette[4], palette[5], 255) )
        colors.append( fg_color or "" )
        colors.append( bg_color or "" )
        style = Style.parse(" on ".join(colors)) 
        return( offset, style )

    def _get_glyph_info3( self, x: int, y: int, get_pixel: GetPixel ) -> list:
        style = None
        offset = 0
        brightlist = []
        darklist = []
        colors = []
        
        celllist = self._get_cellpix(x,y,get_pixel)
        for exp, pixel in enumerate( celllist ):
            if self._get_intensity( pixel ) > self.weight:
                brightlist.append( pixel )
                offset += 2**exp
            else:
                darklist.append( pixel )

        if darklist:
            bg_color = self._get_color( tuple( [int(sum(y) / len(y)) for y in zip(*darklist)] ) )
            if brightlist:
                fg_color = self._get_color( tuple( [int(sum(y) / len(y)) for y in zip(*brightlist)] ) )
            else:
                fg_color = "default"
        else:
            """All bright condition, reprocess cell for dominant 2 color pattern """
            offset = 0
            cellimg = Image.new( 'RGBA', (self.x_pixels, self.y_pixels) )
            cellimg.putdata( celllist )
            cellbiimg = cellimg.convert( 'P', dither=None, colors=2 )
            palette = cellbiimg.getpalette()
            cellbilist = list( cellbiimg.getdata() )
            for exp, pixel in enumerate( cellbilist ):
                if pixel:
                    offset += 2**exp
            bg_color = self._get_color( (palette[0], palette[1], palette[2], 255) )
            fg_color = self._get_color( (palette[3], palette[4], palette[5], 255) )

            
        colors.append( fg_color or "" )
        colors.append( bg_color or "" )
        style = Style.parse(" on ".join(colors)) 
        return( offset, style )

class OctantcellRenderer( CellRenderer ):
    """ Render to Block Octant in Unicode 16.0: Extend to braille glyphs? """
    def __init__( self, *args, **kwargs ) -> None:
        super().__init__( *args, **kwargs )
        self.y_pixels = kwargs.pop( 'y_pixels', 4 )

    def _render_line(
            self, *, line_index: int, width: int, get_pixel: GetPixel
            ) -> list[Segment]:
        line = []
        for x in range(0, width, self.x_pixels):
            line.append(self._render_octantcell(x=x, y=line_index, get_pixel=get_pixel))
        return line

    def _render_octantcell(self, *, x: int, y: int, get_pixel: GetPixel) -> Segment:
        offset, style = self._get_glyph_info3(x, y, get_pixel) 

        glyph_lut=" 𜺨𜺫🮂𜴀▘𜴁𜴂𜴃𜴄▝𜴅𜴆𜴇𜴈▀𜴉𜴊𜴋𜴌🯦𜴍𜴎𜴏𜴐𜴑𜴒𜴓𜴔𜴕𜴖𜴗𜴘𜴙𜴚𜴛𜴜𜴝𜴞𜴟🯧𜴠𜴡𜴢𜴣𜴤𜴥𜴦𜴧𜴨𜴩𜴪𜴫𜴬𜴭𜴮𜴯𜴰𜴱𜴲𜴳𜴴𜴵🮅𜺣𜴶𜴷𜴸𜴹𜴺𜴻𜴼𜴽𜴾𜴿𜵀𜵁𜵂𜵃𜵄▖𜵅𜵆𜵇𜵈▌𜵉𜵊𜵋𜵌▞𜵍𜵎𜵏𜵐▛𜵑𜵒𜵓𜵔𜵕𜵖𜵗𜵘𜵙𜵚𜵛𜵜𜵝𜵞𜵟𜵠𜵡𜵢𜵣𜵤𜵥𜵦𜵧𜵨𜵩𜵪𜵫𜵬𜵭𜵮𜵯𜵰𜺠𜵱𜵲𜵳𜵴𜵵𜵶𜵷𜵸𜵹𜵺𜵻𜵼𜵽𜵾𜵿𜶀𜶁𜶂𜶃𜶄𜶅𜶆𜶇𜶈𜶉𜶊𜶋𜶌𜶍𜶎𜶏▗𜶐𜶑𜶒𜶓▚𜶔𜶕𜶖𜶗▐𜶘𜶙𜶚𜶛▜𜶜𜶝𜶞𜶟𜶠𜶡𜶢𜶣𜶤𜶥𜶦𜶧𜶨𜶩𜶪𜶫▂𜶬𜶭𜶮𜶯𜶰𜶱𜶲𜶳𜶴𜶵𜶶𜶷𜶸𜶹𜶺𜶻𜶼𜶽𜶾𜶿𜷀𜷁𜷂𜷃𜷄𜷅𜷆𜷇𜷈𜷉𜷊𜷋𜷌𜷍𜷎𜷏𜷐𜷑𜷒𜷓𜷔𜷕𜷖𜷗𜷘𜷙𜷚▄𜷛𜷜𜷝𜷞▙𜷟𜷠𜷡𜷢▟𜷣▆𜷤𜷥█"
                                                                                     
        return Segment( glyph_lut[offset], style )

class SextantcellRenderer( CellRenderer ):
    """ Render to Block Sextant in Symbols for Legacy Computing Unicode block """

    def __init__( self, *args, **kwargs ) -> None:
        super().__init__( *args, **kwargs )
        self.y_pixels = kwargs.pop( 'y_pixels', 3 )

    def _render_line(
            self, *, line_index: int, width: int, get_pixel: GetPixel
            ) -> list[Segment]:
        line = []
        for x in range(0, width, self.x_pixels):
            line.append(self._render_sextantcell(x=x, y=line_index, get_pixel=get_pixel))
        return line

    def _render_sextantcell(self, *, x: int, y: int, get_pixel: GetPixel) -> Segment:
        offset, style = self._get_glyph_info(x, y, get_pixel) 
       
        glyph_lut = " 🬀🬁🬂🬃🬄🬅🬆🬇🬈🬉🬊🬋🬌🬍🬎🬏🬐🬑🬒🬓▌🬔🬕🬖🬗🬘🬙🬚🬛🬜🬝🬞🬟🬠🬡🬢🬣🬤🬥🬦🬧▐🬨🬩🬪🬫🬬🬭🬮🬯🬰🬱🬲🬳🬴🬵🬶🬷🬸🬹🬺🬻█"
                                                                                     
        return Segment( glyph_lut[offset], style )

class StrToPixels( Pixels ):
    """Extend Pixels to enable user specified font based string rendering with some PIL transforms"""

    @staticmethod
    def from_string(
            phrase: str = "",
            style: str | Style | None = "white on black",
            pic_renderer: Renderer = SextantcellRenderer(), 
            pic_rotate: float = 0.0,
            font_size: int = 11,
            font_path: str = "./DepartureMono-Regular.woff"
            ) -> Pixels:

        if isinstance( style, str ):
            style = Style.parse( style )

        font = ImageFont.truetype( font_path, size=font_size )
        l,t,r,b = font.getbbox( phrase )
        pane = Image.new( '1', (r,b) )
        canvas = ImageDraw.Draw( pane )
        mask = [x for x in font.getmask(phrase, mode='1')]
        pane.putdata(mask)
        if pic_rotate != 0:
            pane = pane.rotate(pic_rotate, Image.NEAREST, expand = 1)
        segments = Pixels._segments_from_image(pane, renderer=pic_renderer )
        restyle_segments = []
        for segment in segments:
            restyle_segments.append( Segment(segment[0], style) )

        return Pixels.from_segments(restyle_segments)

#Test Code Playground
if __name__ == "__main__":
    cons = Console()

#    for char in string.ascii_uppercase:
#        pixels = StrToPixels.from_string(char, pic_renderer=OctantcellRenderer())
#        cons.print( pixels )
    print( "(Normal terminal font for comparison :-)\n" )
    cons.print( StrToPixels.from_string( "Hello Arctic", style="green on blue", font_size=12, font_path="/usr/share/fonts/truetype/terminus/TerminusTTF-4.46.0.ttf" , pic_renderer=OctantcellRenderer() ) )
    cons.print( Pixels.from_image_path("./north-pole.png", resize=(64,56), renderer=OctantcellRenderer()) )
    cons.print( StrToPixels.from_string( "Hello Grace", style="yellow on black", font_size=12, font_path="/usr/share/fonts/truetype/terminus/TerminusTTF-4.46.0.ttf" , pic_renderer=OctantcellRenderer() ) )
    cons.print( Pixels.from_image_path("./240px-Grace_M._Hopper.jpg", resize=(72,64), renderer=OctantcellRenderer()) )
#    cons.print( StrToPixels.from_string( "No Downunder", style="yellow on blue", pic_rotate=180, pic_renderer=SextantcellRenderer() ) )
