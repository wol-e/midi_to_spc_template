midi_to_spc_template
--------

You can use this package to do some for work for you when you want to create an SPC file for a Super Mario World
song port. Specifically, from an midi input file you can generate a .txt file that is compatible with AddmusicK,
thank you very much.

Midi reading and parsing is based on the mido library.

    >>> import midi_to_spc_template as m
    >>> elise = m.MidiFile("src/data/midi_examples/fuer_elise.mid")
    >>> elise_spc_template = elise.to_spc_template()
    >>> print(elise_spc_template)
