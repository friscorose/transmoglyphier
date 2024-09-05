from __future__ import annotations

from rich.segment import Segment
from rich.style import Style

from textual.strip import Strip
from textual.widgets import Static

import string
import json
import math

#from pkgutil import get_data as LoadGlyphs
from importlib import resources as glyphsource

#from textual import log
#log("stuff")

class EnGlyph( Static ):
    """Renders a wXh unicode glyph 'font' for input token characters."""
    DEFAULT_CSS = """
    EnGlyph {
        height: 3;
    }
	""" 

    def __init__( self, *args, **kwargs ) -> None:
        super().__init__( *args, **kwargs )
        self.load_glyphs()

    def _load_jFace(self, Face, Family) -> None:
        jFace = False
        face_path = 'glyphs/' + Family + "/" + Face + ".json"
        glyph_assets = glyphsource.files()
        glyph_face = glyph_assets.joinpath( "assets", face_path ).read_bytes()
        jFace = json.loads( glyph_face )
        return jFace

    #def load_glyphs(self, Face="seven_segment", Family="box/sans") -> None:
    def load_glyphs(self, Face: str="basic_latin", Family: str="box/sans") -> None:
        self.GLYPHS = self._load_jFace( Face, Family )
        fallback = self.GLYPHS.get('block', Face).replace(" ", "_")
        if fallback != Face:
            faces = self._load_jFace( fallback, Family )
            if faces:
                for key in faces['character'].keys():
                    if key not in self.GLYPHS['character']:
                        self.GLYPHS['character'][key] = faces['character'][key]

    def __str__(self) -> RenderableType:
        self.g_string = ""
        for y in range(3):
            for seg in self.render_line( y ):
                self.g_string += seg[0]
            self.g_string += "\n"
        return self.g_string

    def render_line(self, row:int ) -> Strip:
        """Engine to layout glyph strings in supercell

        Renders:
            2D list of glyphs.
        """

        try:
            bbox_height = self.GLYPHS['fixed lines']
            bbox_width = self.GLYPHS['fixed columns']
            bbox_align = self.GLYPHS['align']
            bbox_tracking = self.GLYPHS['tracking']
            bbox_monospace = self.GLYPHS['monospace']
            faces_data = self.GLYPHS['character']
        except:
            raise Exception("missing required glyph face data")

        last_token = " "
        segments = []

        for token in self._renderable.plain:
            #https://gist.github.com/Jonty/6705090 would be better
            if ord( token ) > 32 and ord( token ) < 127:
                default = {"glyph":["┌┬┐","├"+token+"┤","└┴┘"]}
            else:
                index = "{0:04x}".format( ord(token) )
                default = {"glyph":[index[0]+"┬"+index[1],"├ ┤",index[2]+"┴"+index[3]]}
            face = faces_data.get(token, default)
            Thint = face.get('tracking', bbox_tracking)
            bbox_apairs = self.GLYPHS.get('adjacent pairs',[])
            Mhint = face.get('monospace', bbox_monospace)
            Hhint = face.get('lines', bbox_height)
            Whint = face.get('columns', bbox_width)
            Ahint = face.get('align', bbox_align)
            glyph = face.get('glyph', face )
            if isinstance( glyph, dict ):
                    glyph = glyph.get('normal', glyph )

            #determine horizontal glyph placement in supercell
            if Mhint:
                if Ahint[0] == "left":
                    l_pad = 0
                    r_pad = bbox_width - Whint
                elif Ahint[0] == "right":
                    l_pad = bbox_width - Whint
                    r_pad = 0
                else:
                    pad = (bbox_width - Whint)/2.0
                    if last_token == " ":
                        l_pad = math.ceil(pad)
                        r_pad = math.floor(pad)
                    else:
                        l_pad = math.floor(pad)
                        r_pad = math.ceil(pad)
            else:
                l_pad = r_pad = 0

            #determine horizontal kerning and tracking adjustment
            if last_token+token not in bbox_apairs and Thint > 0:
                last_face = faces_data.get(last_token, {})
                Khint = face.get('kerning', True)
                last_Khint = last_face.get('kerning', True)
                last_Whint = last_face.get('columns', bbox_width)
                if last_Khint and Khint:
                    wedge = math.ceil( Thint )
                else:
                    wedge = math.ceil( Thint - last_Whint )
                if wedge > 0:
                    if Ahint[0] == "left":
                        r_pad += wedge
                    else:
                        l_pad += wedge

            #determine vertical glyph placement in supercell
            if Hhint == bbox_height:
                t_pad = b_pad = 0
            else:
                if Ahint[1] == "top":
                    t_pad = 0
                    b_pad = bbox_height - Hhint
                elif Ahint[1] == "bottom":
                    t_pad = bbox_height - Hhint
                    b_pad = 0
                else:
                    pad = (bbox_height - Hhint)/2.0
                    t_pad = math.ceil(pad)
                    b_pad = math.floor(pad)

            #construct line of glyph supercell sequence
            if row < t_pad or row >= t_pad+Hhint:
                g_datum = " "*Whint
            else:
                g_datum = glyph[row - t_pad] 
            s_row = Segment(" "*l_pad + g_datum + " "*r_pad )
            segments.append( s_row )

            last_token = token
            #process next token or loop finished

        return Strip( segments )

