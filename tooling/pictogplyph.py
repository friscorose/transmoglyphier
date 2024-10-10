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
        self.mono = kwargs.pop('mono', False)
        self.x_pixels = kwargs.pop( 'x_pixels', 2 )
        self.y_pixels = kwargs.pop( 'y_pixels', 4 )
        self.pips = kwargs.pop( 'pips', False )
        super().__init__( *args, **kwargs )

    def render( self, image: Image, resize: tuple[int, int] | None) -> list[Segment]:
        target_width = resize[0] if resize else image.size[0]
        while target_width % self.x_pixels != 0:
            target_width += 1

        target_height = resize[1] if resize else image.size[1]
        while target_height % self.y_pixels != 0:
            target_height += 1

        if image.size[0] != target_width or image.size[1] != target_height:
            resize = (target_width, target_height)

        return super().render(image, resize)

    def _get_intensity( self, pixel: GetPixel ) -> int:
        """calculate intensity approximation of an RGBA PIL getpixel.
           https://en.wikipedia.org/wiki/Grayscale"""
        r,g,b,a = pixel
        return int( (0.2126*r + 0.7152*g + 0.0722*b)*a/255 )

    def _get_range(self, height: int) -> range:
        return range(0, height, self.y_pixels)
    
    def _get_cellpix( self, x: int, y: int, get_pixel: GetPixel ) -> list:
        #pixlist index is the power of 2 for the pixel bit offset
        pixlist = []
        for y_idx in range( self.y_pixels ):
            for x_idx in range( self.x_pixels ):
                pixlist.append( get_pixel((x + x_idx, y + y_idx)) )
        return pixlist

    def _get_color(self, pixel: tuple ) -> str | None:
        r, g, b, a = pixel
        return f"rgb({r},{g},{b})" if a > 0 else None

    def _get_glyph_info( self, x: int, y: int, get_pixel: GetPixel ) -> list:
        offset = 0
        fg_color = "default"
        bg_color = "default"
        brightlist = []
        darklist = []
        colors = []
        
        """ Process current cell pixels for brightness (intensity) bilevel 'coloring'. """
        celllist = self._get_cellpix(x,y,get_pixel)
        for exp, pixel in enumerate( celllist ):
            if self._get_intensity( pixel ) > self.weight:
                brightlist.append( pixel )
                offset += 2**exp
            else:
                darklist.append( pixel )

        if darklist:
            """ Simple RGB component averaging of background pixels, is this good?"""
            bg_color = self._get_color( tuple( [int(sum(y) / len(y)) for y in zip(*darklist)] ) )
            if brightlist:
                fg_color = self._get_color( tuple( [int(sum(y) / len(y)) for y in zip(*brightlist)] ) )
        elif not self.mono:
            """ All bright condition, reprocess cell for dominant 2 color pattern.
                A possibly better approach here would be use adjacent cells in a
                Floyd-Steinberg esque 2-color dithering downsampling."""
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

        if fg_color is not None:
            colors.append( fg_color )
        else:
            colors.append( "default" )
        if bg_color is not None:
            colors.append( bg_color )
        else:
            colors.append( "default" )
        style = Style.parse(" on ".join(colors)) 
        return( offset, style )

class OctantCellRenderer( CellRenderer ):
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
        offset, style = self._get_glyph_info(x, y, get_pixel) 

        if self.pips:
            glyph_lut="⠀⠁⠈⠉⠂⠃⠊⠋⠐⠑⠘⠙⠒⠓⠚⠛⠄⠅⠌⠍⠆⠇⠎⠏⠔⠕⠜⠝⠖⠗⠞⠟⠠⠡⠨⠩⠢⠣⠪⠫⠰⠱⠸⠹⠲⠳⠺⠻⠤⠥⠬⠭⠦⠧⠮⠯⠴⠵⠼⠽⠶⠷⠾⠿⡀⡁⡈⡉⡂⡃⡊⡋⡐⡑⡘⡙⡒⡓⡚⡛⡄⡅⡌⡍⡆⡇⡎⡏⡔⡕⡜⡝⡖⡗⡞⡟⡠⡡⡨⡩⡢⡣⡪⡫⡰⡱⡸⡹⡲⡳⡺⡻⡤⡥⡬⡭⡦⡧⡮⡯⡴⡵⡼⡽⡶⡷⡾⡿⢀⢁⢈⢉⢂⢃⢊⢋⢐⢑⢘⢙⢒⢓⢚⢛⢄⢅⢌⢍⢆⢇⢎⢏⢔⢕⢜⢝⢖⢗⢞⢟⢠⢡⢨⢩⢢⢣⢪⢫⢰⢱⢸⢹⢲⢳⢺⢻⢤⢥⢬⢭⢦⢧⢮⢯⢴⢵⢼⢽⢶⢷⢾⢿⣀⣁⣈⣉⣂⣃⣊⣋⣐⣑⣘⣙⣒⣓⣚⣛⣄⣅⣌⣍⣆⣇⣎⣏⣔⣕⣜⣝⣖⣗⣞⣟⣠⣡⣨⣩⣢⣣⣪⣫⣰⣱⣸⣹⣲⣳⣺⣻⣤⣥⣬⣭⣦⣧⣮⣯⣴⣵⣼⣽⣶⣷⣾⣿"
        else:
            glyph_lut=" 𜺨𜺫🮂𜴀▘𜴁𜴂𜴃𜴄▝𜴅𜴆𜴇𜴈▀𜴉𜴊𜴋𜴌🯦𜴍𜴎𜴏𜴐𜴑𜴒𜴓𜴔𜴕𜴖𜴗𜴘𜴙𜴚𜴛𜴜𜴝𜴞𜴟🯧𜴠𜴡𜴢𜴣𜴤𜴥𜴦𜴧𜴨𜴩𜴪𜴫𜴬𜴭𜴮𜴯𜴰𜴱𜴲𜴳𜴴𜴵🮅𜺣𜴶𜴷𜴸𜴹𜴺𜴻𜴼𜴽𜴾𜴿𜵀𜵁𜵂𜵃𜵄▖𜵅𜵆𜵇𜵈▌𜵉𜵊𜵋𜵌▞𜵍𜵎𜵏𜵐▛𜵑𜵒𜵓𜵔𜵕𜵖𜵗𜵘𜵙𜵚𜵛𜵜𜵝𜵞𜵟𜵠𜵡𜵢𜵣𜵤𜵥𜵦𜵧𜵨𜵩𜵪𜵫𜵬𜵭𜵮𜵯𜵰𜺠𜵱𜵲𜵳𜵴𜵵𜵶𜵷𜵸𜵹𜵺𜵻𜵼𜵽𜵾𜵿𜶀𜶁𜶂𜶃𜶄𜶅𜶆𜶇𜶈𜶉𜶊𜶋𜶌𜶍𜶎𜶏▗𜶐𜶑𜶒𜶓▚𜶔𜶕𜶖𜶗▐𜶘𜶙𜶚𜶛▜𜶜𜶝𜶞𜶟𜶠𜶡𜶢𜶣𜶤𜶥𜶦𜶧𜶨𜶩𜶪𜶫▂𜶬𜶭𜶮𜶯𜶰𜶱𜶲𜶳𜶴𜶵𜶶𜶷𜶸𜶹𜶺𜶻𜶼𜶽𜶾𜶿𜷀𜷁𜷂𜷃𜷄𜷅𜷆𜷇𜷈𜷉𜷊𜷋𜷌𜷍𜷎𜷏𜷐𜷑𜷒𜷓𜷔𜷕𜷖𜷗𜷘𜷙𜷚▄𜷛𜷜𜷝𜷞▙𜷟𜷠𜷡𜷢▟𜷣▆𜷤𜷥█"
                                                                                     
        return Segment( glyph_lut[offset], style )

class SextantCellRenderer( CellRenderer ):
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
       
        if self.pips:
            glyph_lut = " 𜹑𜹒𜹓𜹔𜹕𜹖𜹗𜹘𜹙𜹚𜹛𜹜𜹝𜹞𜹟𜹠𜹡𜹢𜹣𜹤𜹥𜹦𜹧𜹨𜹩𜹪𜹫𜹬𜹭𜹮𜹯𜹰𜹱𜹲𜹳𜹴𜹵𜹶𜹷𜹸𜹹𜹺𜹻𜹼𜹽𜹾𜹿𜺀𜺁𜺂𜺃𜺄𜺅𜺆𜺇𜺈𜺉𜺊𜺋𜺌𜺍𜺎𜺏"
        else:
            glyph_lut = " 🬀🬁🬂🬃🬄🬅🬆🬇🬈🬉🬊🬋🬌🬍🬎🬏🬐🬑🬒🬓▌🬔🬕🬖🬗🬘🬙🬚🬛🬜🬝🬞🬟🬠🬡🬢🬣🬤🬥🬦🬧▐🬨🬩🬪🬫🬬🬭🬮🬯🬰🬱🬲🬳🬴🬵🬶🬷🬸🬹🬺🬻█"
                                                                                     
        return Segment( glyph_lut[offset], style )

class QuadrantCellRenderer( CellRenderer ):
    """ Render to Block Quadtant in Symbols for Legacy Computing Unicode block """

    def __init__( self, *args, **kwargs ) -> None:
        super().__init__( *args, **kwargs )
        self.y_pixels = kwargs.pop( 'y_pixels', 2 )

    def _render_line(
            self, *, line_index: int, width: int, get_pixel: GetPixel
            ) -> list[Segment]:
        line = []
        for x in range(0, width, self.x_pixels):
            line.append(self._render_sextantcell(x=x, y=line_index, get_pixel=get_pixel))
        return line

    def _render_sextantcell(self, *, x: int, y: int, get_pixel: GetPixel) -> Segment:
        offset, style = self._get_glyph_info(x, y, get_pixel) 
       
        if self.pips:
            glyph_lut = " 𜰡𜰢𜰣𜰤𜰥𜰦𜰧𜰨𜰩𜰪𜰫𜰬𜰭𜰮𜰯"
        else:
            glyph_lut = " ▘▝▀▖▌▞▛▗▚▐▜▄▙▟█"
                                                                                     
        return Segment( glyph_lut[offset], style )

class ToPixels( Pixels ):
    """Extend Pixels to enable user specified font based string rendering with some PIL transforms"""

    @staticmethod
    def from_string(
            phrase: str = "",
            style: str | Style | None = "default on default",
            renderer: Renderer = OctantCellRenderer(), 
            font_size: int = 11,
            font_path: str = "./DepartureMono-Regular.woff"
            ) -> Pixels:

        if isinstance( style, str ):
            style = Style.parse( style )

        font = ImageFont.truetype( font_path, size=font_size )
        l,t,r,b = font.getbbox( phrase )
        pane = Image.new( '1', (r,b) )
        mask = [x for x in font.getmask(phrase, mode='1')]
        print( (r,b) )
        print( mask )
        pane.putdata(mask)
        #pane.show()
        segments = Pixels._segments_from_image(pane, renderer=renderer )
        restyle_segments = []
        for segment in segments:
            restyle_segments.append( Segment(segment[0], style) )

        return Pixels.from_segments(restyle_segments)

#Test Code Playground
if __name__ == "__main__":
    cons = Console()

    #char = ""
    #for point in range( 0x2800, 0x2900 ): #octant pips (braille, not row major)
    #for point in range( 0x1CE50, 0x1CE90 ): #sextant pips
    #for point in range( 0x1CC21, 0x1CC30 ): #quadrant pips
    #    char += chr( point )
    #print( char )

    #for char in string.ascii_uppercase:
    #    pixels = ToPixels.from_string(char, renderer=SextantCellRenderer())
    #    cons.print( pixels )
    
    #print( "(Normal terminal font for comparison :-)\n" )
    #print( "Octant green digits in Terminus TTF\n" )
    #cons.print( ToPixels.from_string( string.digits, style="green on default", font_size=12, font_path="/usr/share/fonts/truetype/terminus/TerminusTTF-4.46.0.ttf", renderer=OctantCellRenderer(mono=True) ) )
    #print( "Octant pips(braille) green digits in Terminus TTF\n" )
    #cons.print( ToPixels.from_string( string.digits, style="green on default", font_size=12, font_path="/usr/share/fonts/truetype/terminus/TerminusTTF-4.46.0.ttf", renderer=OctantCellRenderer(mono=True, pips=True) ) )
    #print( "Sextant green digits in Terminus TTF\n" )
    #cons.print( ToPixels.from_string( string.digits, style="green on default", font_size=12, font_path="/usr/share/fonts/truetype/terminus/TerminusTTF-4.46.0.ttf", renderer=SextantCellRenderer(mono=True) ) )
    #print( "Sextant pips green digits in Terminus TTF\n" )
    #cons.print( ToPixels.from_string( string.digits, style="green on default", font_size=12, font_path="/usr/share/fonts/truetype/terminus/TerminusTTF-4.46.0.ttf", renderer=SextantCellRenderer(mono=True, pips=True) ) )
    #print( "Quadrant green digits in Terminus TTF\n" )
    #cons.print( ToPixels.from_string( string.digits, style="green on default", font_size=12, font_path="/usr/share/fonts/truetype/terminus/TerminusTTF-4.46.0.ttf", renderer=QuadrantCellRenderer(mono=True) ) )
    #print( "Quadrant pips green digits in Terminus TTF\n" )
    #cons.print( ToPixels.from_string( string.digits, style="green on default", font_size=12, font_path="/usr/share/fonts/truetype/terminus/TerminusTTF-4.46.0.ttf", renderer=QuadrantCellRenderer(mono=True, pips=True) ) )
    #print( "Blue digits in DepartureMono  WOFF\n" )
    #cons.print( ToPixels.from_string( string.digits, style="blue on default" ) )

    #cons.print( Pixels.from_image_path("./textual_logo_light.png", resize=(42,42), renderer=BrailleCellRenderer(mono=True)) )
    cons.print( ToPixels.from_string( "8.1", style="green on blue", font_size=12, font_path="/usr/share/fonts/truetype/terminus/TerminusTTF-4.46.0.ttf" ) )
    #cons.print( Pixels.from_image_path("./north-pole.png", resize=(64,64), renderer=OctantCellRenderer()) )
    #cons.print( ToPixels.from_string( "Hello Grace", style="yellow on default" ) )
    #cons.print( Pixels.from_image_path("./240px-Grace_M._Hopper.jpg", resize=(80,80), renderer=OctantCellRenderer()) )
    #cons.print( ToPixels.from_string( "Transmoglyphier", style="red on yellow", font_size=12, font_path="/usr/share/fonts/truetype/terminus/TerminusTTF-4.46.0.ttf"  ) )
    #cons.print( Pixels.from_image_path("./Transmogrifier_zap.webp", resize=(90,90), renderer=OctantCellRenderer()) )
    #cons.print( ToPixels.from_string( "♙♘♗♖♕♔ ", font_size=32, font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", renderer=OctantCellRenderer(mono=True) ) )
    #cons.print( ToPixels.from_string( "♚♛♜♝♞♟ ", font_size=32, font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", renderer=OctantCellRenderer(mono=True) ) )

