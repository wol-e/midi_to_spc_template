import mido
import numpy as np
import pandas as pd

from tqdm import tqdm

from .functions import midi_note_value_to_western, midi_msg_to_dict

import time

class MidiFile(mido.MidiFile):
    def __init__(self, filename=None, file=None, type=1, ticks_per_beat=480,
                 charset='latin1', debug=False, clip=False):
        
        super().__init__(filename, file, type, ticks_per_beat,
                         charset, debug, clip)
        
    def to_pandas(self, include_meta=True, sustain=False):
    
        _df = pd.DataFrame()
        
        for i, track in tqdm(enumerate(self.tracks)):
            
            _dict = {}
            
            for j, msg in enumerate(track):
                if not include_meta and msg.is_meta:
                    continue
                
                msg = midi_msg_to_dict(msg)

                msg['track'] = i
     
                _dict[j] = msg
                #_df = _df.append(msg, ignore_index=True)
            
            df_j = pd.DataFrame.from_dict(_dict, "index")
            
            _df = _df.append(df_j)
        
        _df = _df.reset_index()
        
        # add column with western note names
        def note_map(note):
            if np.isnan(note):
                return np.nan

            else:
                return midi_note_value_to_western(note)

        _df["note_name"] = _df["note"].apply(note_map)
        
        # adding absolute times
        def get_timing(midifile):
            track0 = self.tracks[0]
            for msg in track0:

                # get clocks per click
                if str(msg).split()[2] == "time_signature":
                    clocks_per_click = int(str(msg).split()[5].split("=")[1])

                # get initial tempo
                if str(msg).split()[2] == "set_tempo":
                    tempo = int(str(msg).split()[3].split("=")[1])
                    break

            return(tempo, clocks_per_click, )
        
        tempo, cpc = get_timing(self)

        _df['total_time'] = _df.groupby('track')['time'].transform(pd.Series.cumsum)
        _df['total_time_seconds'] = _df['total_time'].apply(lambda x: mido.tick2second(x, cpc, tempo))
        
        # adding column for duration of notes
        _df["duration"] = np.nan

        # TODO: speed this one up
        for i in tqdm(_df[_df["type_1"] == "note_on"].index):
            total_time, note, track, channel = _df[["total_time", "note", "track", "channel"]].iloc[i].values

            _df.loc[i, "duration"] = _df[
                (_df["total_time"] > total_time) & (_df["note"] == note) &
                (_df["track"] == track) & (_df["channel"] == channel)
            ]["total_time"].iloc[0] - total_time

        _df["duration_seconds"] = _df['duration'].apply(lambda x: mido.tick2second(x, cpc, tempo))


        if sustain:
            pass # TODO: implement

        return _df

    def to_addmusick_txt(self):
        raise NotImplementedError
