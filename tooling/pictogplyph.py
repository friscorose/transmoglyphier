from rich_pixels import Pixels
from rich_pixels import Renderer
from rich.console import Console

import string
import PIL.Image
import PIL.ImageDraw

class StrToPixels( Pixels ):

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
        
        segments = Pixels._segments_from_image(r_image, (8,12), renderer=None)

        return Pixels.from_segments(segments)



cons = Console()
for char in string.ascii_uppercase:
    pixels = StrToPixels.from_string(char, 85)
    cons.print( pixels )
    cons.print( "\n" )
