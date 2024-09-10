import string

from rich.text import Text

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Input

from glyphs import EnGlyph


class DigitApp(App[None]):
    DEFAULT_CSS = """
    Vertical {
        border-title-align: center;
        border: solid white;
    }
    """
    CSS_PATH = "transmoglyphier.tcss"

    test_string = "[red]He[/red]llo [blue]Wo[/blue][green]rld[/green]"
    test_list = [
        "The Five Boxing Wizards Jump Quickly",
        #"Xian Xylene Xenon xri xat xes xi",
        string.ascii_lowercase,
        string.ascii_uppercase,
        string.digits,
        string.punctuation,
        test_string
        ]

    def compose(self) -> ComposeResult:
        self.input = Input(self.test_string) 
        self.table = DataTable(zebra_stripes=True)
        self.t_glyph = EnGlyph( self.test_string, Family="box/serif", id="test_glyphs")
        #yield EnGlyph( "Hello", Face="seven_segment", id="test_glyphs")
        with (vertical := Vertical()):
            vertical.border_title = self.test_string
            with Horizontal():
                yield Button("↻", id="cycle_glyphs")
                yield self.t_glyph
            with Horizontal():
                yield Button("Test", id="render_str")
                yield self.input
            with Horizontal():
                yield Button("Face", id="set_face")
                yield EnGlyph( self.t_glyph.Face, id="face_type")
        yield Label( "Unicode Explorer" )
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

    def show_tests( self ) -> None:
        if self.input.value not in self.test_list:
            self.test_list.append( self.input.value )
        self.query_one("Vertical").border_title = self.input.value
        self.t_glyph.update(self.input.value)

    @on( Button.Pressed )
    def do_button_act( self, event ) -> None:
        if event.button.id == "render_str":
            self.show_tests()

        elif event.button.id == "cycle_glyphs":
            self.input.value = self.test_list.pop(0)
            self.show_tests()

        elif event.button.id == "set_face":
            self.t_glyph.load_glyphs( Face="deco", Family="box/art" )
            self.query_one("#face_type").update( self.t_glyph.Face )
            self.show_tests()


app = DigitApp()
if __name__ == "__main__":
    app.run()
