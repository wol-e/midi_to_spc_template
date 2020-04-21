import mido

class MidiFile(mido.MidiFile):
    def __init__(self, filename=None, file=None, type=1, ticks_per_beat=480,
                 charset='latin1', debug=False, clip=False):
        
        super().__init__(filename, file, type, ticks_per_beat,
                         charset, debug, clip)
        
    def to_pandas(self):
        raise NotImplementedError
    
    def to_addmusick_txt(self):
        raise NotImplementedError
