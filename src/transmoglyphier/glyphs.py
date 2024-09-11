from __future__ import annotations

from rich.console import Console
from rich.segment import Segment
from rich.style import Style

from textual.strip import Strip
from textual.widgets import Static

import string
import json
import math

#from pkgutil import get_data as LoadGlyphs
from importlib import resources as glyphsource

from textual import log
#log("stuff")

class EnGlyph( Static ):
    """Renders a wXh unicode glyph 'font' for input token characters."""
    DEFAULT_CSS = """
    EnGlyph {
        height: 3;
    }
	""" 

    def __init__( self, *args, **kwargs ) -> None:
        self.Face = kwargs.pop('Face', "basic_latin")
        self.Family = kwargs.pop('Family', "block/sans")
        super().__init__( *args, **kwargs )
        self._cache = None
        self.load_glyphs(self.Face, self.Family)

    def render_line(self, row:int ) -> Strip:
        if self._cache != self._renderable:
            self._prechunk()
        return self._strips[ row ]

    def _load_jFace(self, Face, Family) -> None:
        jFace = False
        face_path = 'glyphs/' + Family + "/" + Face + ".json"
        glyph_assets = glyphsource.files()
        try:
            glyph_face = glyph_assets.joinpath( "assets", face_path ).read_bytes()
            jFace = json.loads( glyph_face )
            self.Face = Face
            self.Family = Family
        finally:
            return jFace

    #def load_glyphs(self, Face="seven_segment", Family="block/sans") -> None:
    def load_glyphs(self, Face: str, Family: str) -> None:
        self.GLYPHS = self._load_jFace( Face, Family )
        fallback = self.GLYPHS.get('block', Face).replace(" ", "_")
        if fallback != Face:
            faces = self._load_jFace( fallback, Family )
            if faces:
                for key in faces['character'].keys():
                    if key not in self.GLYPHS['character']:
                        self.GLYPHS['character'][key] = faces['character'][key]

    def __str__(self) -> RenderableType:
        a_string = ""
        for y in range(3):
            for seg in self.render_line( y ):
                log( repr(seg[0]) )
                a_string += seg[0]
            a_string += "\n"
        return a_string

    def _chunks_to_strips(self) -> None:
        chunk_list = self._chunk_list
        lines = [[] for i in range(1, len(chunk_list[0])+1)]
        for chunk in chunk_list:
            #log( "Chunks: "+repr( chunk ) )
            for n, seg in enumerate( chunk ):
                #log( "Chunk Seg: "+str(n)+", "+repr( seg ) )
                lines[n].append( seg )
                #log( "Line n: "+str(n)+", "+repr( lines[n] ) )
        self._strips = []
        #log( "Lines: "+repr( lines ) )
        for line in lines:
            self._strips.append( Strip(line) )


    def _prechunk(self):
        """A chunk list is useful for inline styling, line wrapping
        and word splits of glyph based text"""
        self._last_token = " "
        a_con = Console()
        self._chunk_list = []
        for seg in a_con.render(renderable=self._renderable): 
            self._chunk_list.append( self.en_glyph(seg[0], seg[1]) )
            #log( type(seg), repr( seg ) )
        #Discard the trailing newline automatically added by render()
        self._chunk_list.pop()
        self._chunks_to_strips()

    def en_glyph(self, text: str, style: StyleType = "" ) -> list:
        """Engine to layout glyph strings in supercell

        Returns a vertical pile of segments (chunk) that are the 2D
        block of glyphs representing the input text.
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

        g_strings: list[str] = ['']*bbox_height
        chunk = []

        for token in text:
            #https://gist.github.com/Jonty/6705090 would be better
            if ord( token ) > 32 and ord( token ) < 127:
                default = {"glyph":["┌┬┐","├"+token+"┤","└┴┘"]}
            else:
                index = "{0:04x}".format( ord(token) )
                default = {"glyph":[index[0]+"┬"+index[1],"├ ┤",index[2]+"┴"+index[3]]}
            face = faces_data.get(token, default)
            Thint = face.get('tracking', bbox_tracking)
            #Special char pairs that have no proportional spacing 
            bbox_apairs = self.GLYPHS.get('adjacent pairs',[])
            #determine if the glyphs are placed in fixed width 
            Mhint = face.get('monospace', bbox_monospace)
            #Determine vertical number of cells for the glyphs
            Hhint = face.get('lines', bbox_height)
            #The nominal max width of a glyph
            Whint = face.get('columns', bbox_width)
            Ahint = face.get('align', bbox_align)
            glyph = face.get('glyph', face )
            if isinstance( glyph, dict ):
                if self.styles.text_style.bold:
                    glyph = glyph.get('bold', glyph )
                else:
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
                    if self._last_token == " ":
                        l_pad = math.ceil(pad)
                        r_pad = math.floor(pad)
                    else:
                        l_pad = math.floor(pad)
                        r_pad = math.ceil(pad)
            else:
                l_pad = r_pad = 0

            #determine horizontal kerning and tracking adjustment
            if self._last_token+token not in bbox_apairs and Thint > 0:
                last_face = faces_data.get(self._last_token, {})
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
            for row, row_str in enumerate( g_strings ):
                if row < t_pad or row >= t_pad+Hhint:
                    g_datum = " "*Whint
                else:
                    g_datum = glyph[row - t_pad] 
                g_strings[row] += " "*l_pad + g_datum + " "*r_pad

            self._last_token = token
            #process next token or loop finished

        assert len(g_strings) == bbox_height, "Too many rows in glyph stack!"
        for g_string in g_strings:
            chunk.append( Segment(g_string, style) )

        assert len(chunk) == bbox_height, "Too many segments in chunk!"
        #log( repr(chunk) )
        return chunk

