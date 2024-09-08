import string
from itertools import cycle

from rich.text import Text

from textual.app import App, ComposeResult
from textual.widgets import Button, DataTable, Label, TextArea

from glyphs import EnGlyph

test_strings = cycle(
    [
        "The Five Boxing Wizards Jump Quickly",
        string.ascii_lowercase,
        string.ascii_uppercase,
        string.digits,
        string.punctuation
    ]
)
class DigitApp(App[None]):
    CSS_PATH = "transmoglyphier.tcss"

    def next_test(self) -> None:
        glyphed = self.query_one( "#test_str" )
        next_string =  next(test_strings)
        glyphed.update( next_string )

    def on_click(self) -> None:
        self.next_test()

    def compose(self) -> ComposeResult:
        test_string = "[red]He[/red]llo [blue]Wo[/blue][green]rld[/green]"
        #yield EnGlyph( "Hello", Face="seven_segment", id="test_str")
        yield EnGlyph( test_string, id="test_str")
        yield Label( test_string )
        yield DataTable( zebra_stripes=True )
        yield TextArea( test_string )

    def on_mount(self) -> None:
        table = self.query_one("DataTable")
        header = ("name", "glyph", "Dec", "\\uJSON") 
        table.add_columns( *header )
        for ucp in range( 128 ):
            char = chr( ucp )
            #if char in string.printable:
            if char in string.ascii_uppercase:
                label = Text( char, style="#B0FC38 italic")
                glyph = str( EnGlyph(char) )
                row = ("name", glyph, ucp, "\\u{0:04x}".format(ucp) )
                table.add_row(*row, height=3, label=label)

app = DigitApp()
if __name__ == "__main__":
    app.run()
