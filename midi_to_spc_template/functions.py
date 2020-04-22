def midi_note_value_to_western(midi_val: int):
    """
    Returns western note name of midi value. Octaves too low for western naming system will have negative numbers.
    Notes for black keys are referred to always with a sharp # from the lower white key.
    
    >>> midi_note_value_to_western(60)
    >>> "C4"
    
    >>> midi_note_value_to_western(60)
    >>> "C#4"
    
    >>> midi_note_value_to_western(0)
    >>> "C-1"
    """
    midi_val = int(midi_val)
    
    assert midi_val >= 0, f"encountert invalid midi note value: {midi_val} (allowed values range from 0 to 128)"
    
    assert midi_val <= 128, f"encountert invalid midi note value: {midi_val} (allowed values range from 0 to 128)"
    
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    return (notes * 12)[midi_val] + str((midi_val - 12) // 12)

def midi_msg_to_dict(msg):
    """
    Returns dict from midi message. 
    
    >>> midi_msg_to_dict(some_midi_msg)
    >>> {'type_1': 'note_on', 'channel': 0, 'note': 76, 'velocity': 120, 'time': 0}
    """
    
    msg = str(msg)
    
    if msg[0] == "<":
        msg = msg[1:-1]

    msg_list = msg.split()
    
    msg_dict = {}
    msg_dict["type_1"] = msg_list[0]
    del msg_list[0]

    if msg_dict["type_1"] == "meta":
        msg_dict["type_2"] = msg_list[0]
        msg_dict["type_3"] = msg_list[1]
        del msg_list[:2]
    
    def try_int(char):
        try:
            cast = int(char)
        except (ValueError):
            cast = str(char)
        return(cast)
    
    if msg_dict["type_1"] == "meta":
        if msg_dict["type_3"] in ["sequencer_specific", "track_name"]:
            return(msg_dict)
    
    else:
        msg_dict.update({item.split('=')[0]: try_int(item.split('=')[1]) for item in msg_list})
    
    return(msg_dict)