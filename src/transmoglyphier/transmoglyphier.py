import string

from rich.text import Text

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.strip import Strip
from textual.widgets import Static, Header, Footer, Button, DataTable, Label, Input

from glyphs import EnGlyph

class Glyphograph( Static ):
    def render_line( self ) -> Strip:
        pass

class Transmoglyphier(App[None]):
    DEFAULT_CSS = """
    Vertical {
        border-title-align: center;
        border: solid white;
    }
    #cruizer {
        border: solid blue;
        width: 33%;
    }
    """
    CSS_PATH = "transmoglyphier.tcss"

    test_string = "[red]He[/red]llo [blue]Wo[/blue][green]rld[/green]"
    test_list = [
        string.ascii_uppercase,
        string.ascii_lowercase,
        string.digits,
        string.punctuation,
        "The Five Boxing Wizards Jump Quickly",
        #"Xian Xylene Xenon xri xat xes xi",
        test_string
        ]

    def compose(self) -> ComposeResult:
        self.input = Input(self.test_string) 
        self.table = DataTable(zebra_stripes=True)
        self.t_glyph = EnGlyph( self.test_string, Family="block/serif", id="test_glyphs")
        #yield EnGlyph( "Hello", Face="seven_segment", id="test_glyphs")
        yield Header()
        with (vertical := Vertical( id="testing" )):
            vertical.border_title = self.test_string
            with Horizontal():
                yield Button("↻", id="cycle_glyphs")
                yield self.t_glyph
            with Horizontal():
                yield Button("Test", id="render_str")
                yield self.input
            with Horizontal():
                yield Button("Face", id="set_face")
                yield EnGlyph( self.t_glyph.Face, Family="block/serif", id="face_type")
                yield Button("Family", id="set_family")
                yield EnGlyph( self.t_glyph.Family, Family="block/serif", id="family_type")
        with Vertical( id="cruizer" ):
            yield Button( "Code Pt Cruizer", id="select_blocks" )
            yield self.table

    def on_mount(self) -> None:
        header = ("name", "Dec", "\\uJSON") 
        self.table.add_columns( *header )
        for ucp in range( 128 ):
            char = chr( ucp )
            if char in string.printable:
                label = Text( char, style="#B0FC38 italic")
                row = ("name", ucp, "\\u{0:04x}".format(ucp) )
                self.table.add_row(*row, height=3, label=label)

    def toggle_choose_blocks_panel( self ) -> None:
        pass

    def toggle_test_panel( self ) -> None:
        pass

    def show_tests( self ) -> None:
        if self.input.value not in self.test_list:
            self.test_list.append( self.input.value )
        self.query_one("#testing").border_title = self.input.value
        self.t_glyph.update(self.input.value)

    @on( Button.Pressed )
    def do_button_act( self, event ) -> None:
        if event.button.id == "render_str":
            self.show_tests()

        elif event.button.id == "cycle_glyphs":
            self.input.value = self.test_list.pop(0)
            self.show_tests()

        elif event.button.id == "set_face":
            self.t_glyph.load_glyphs( Face="deco_caps", Family="block/art" )
            self.query_one("#face_type").update( self.t_glyph.Face )
            self.query_one("#family_type").update( self.t_glyph.Family )
            self.show_tests()

        elif event.button.id == "select_blocks":
            self.toggle_choose_blocks_panel()


app = Transmoglyphier()
if __name__ == "__main__":
    app.run()
