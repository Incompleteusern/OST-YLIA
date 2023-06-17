# OTIS Solution Tex: Yet Lousily Instatiated Automatically

I don't know why I did this.

A rather crude Proof of Concept.

Main script is `gen.py` which takes in `DNY-not-ntconstruct.tex` and turns it into `out-DNY-not-ntconstruct.tex`
Von source files are local to me.

From a high point of view, the Parser chooses among a list of SubParsers to extract certain data,
then the Writer uses that data to write the new file.

This does not handle type hints or spacing well at all.