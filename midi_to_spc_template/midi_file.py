import mido
import numpy as np
import pandas as pd
import warnings
import pprint

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
        
        for i, track in enumerate(self.tracks):
            
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

    def to_addmusick(self, file=None, print_output=False, return_string=True, author="", title="", game="", length="auto", comment=""):
        if file is None:
            warnings.warn("Warning: No file path given, output will not be saved to file")
        
        df_tracks = self.to_pandas()
        
        bpm = 180 # TODO: change to use the tempo form midi file
        seconds_per_beat = 60 / bpm
        smw_time = int(round(bpm * 256 / 625, 0)) # smw time formula: t = BPM * 256 / 625

        # helper function to 
        def get_smw_note_duration(duration, quarter_duration):
            """
            param duration: duration of the note you want to get the smw duration notation for
            param quarter_duration: duration of a quarter note in your unit system
            
            >>> get_smw_note_duration(6, 4)
            >>> 4. # returns a dotted quarter since 6 is 1.5 times as long as 4 (no matter what th eunits are)
            """
            
            ratio_map = {8: "1^1", 6: "1.", 4: "1", 3: "2.", 2: "2", 1.5: "4.", 1: "4", .75: "8.", .5: "8",
                         .375: "16.", .25: "16", .125: "32",
                        .0625: "64", .0317: "128"}  # TODO: Add more granularity

            ratio = duration / quarter_duration

            closest_ratio = min(ratio_map, key=lambda x: abs(x - ratio))

            return ratio_map[closest_ratio]
        

        def smw_note_name(note_name):
            smw_note = "o" + note_name[-1] + note_name[0].lower()
            if note_name[1] == "#":
                smw_note += "+"

            return smw_note
        
        df_tracks = df_tracks[df_tracks["type_1"] == "note_on"][
            ["track", "channel", "note", "note_name", "time", "total_time","total_time_seconds",
             "duration", "duration_seconds"]].sort_values(by=["track", "channel", "total_time"])
        
        df_tracks["end_total_seconds"] = df_tracks["total_time_seconds"] + df_tracks["duration_seconds"]
        df_tracks["smw_note_name"] = df_tracks["note_name"].apply(smw_note_name)
        df_tracks["smw_note_duration"] = df_tracks["duration_seconds"].apply(
            lambda x: get_smw_note_duration(x, seconds_per_beat))
        
        header = f"""
        #amk 2

        #SPC
        {{
            #author "{author}"
            #title "{title}"
            #game "{game}"
            #length "{length}"
            #comment "{comment}"
        }}

        """
        
        channel_strings = {}

        # the 0th channel string has some specifics
        channel_strings[0] = f"""
        #0 w255 t{smw_time}

        @9 ; piano

        v255 
        """

        # template for adding further channels
        add_channel_template = f"""
        #channel_number

        @9 ; piano

        v255 
        """
        
        for i, (track, channel) in enumerate(df_tracks[["track", "channel"]].drop_duplicates().values):

            channel_data = df_tracks.copy()[(df_tracks["track"] == track) & (df_tracks["channel"] == channel)][
                ["total_time_seconds", "duration_seconds", "end_total_seconds",
                 "smw_note_name", "smw_note_duration"]
            ].reset_index(drop=True)

            channel_string = add_channel_template.replace("channel_number", str(i + 1))

            channel_string += (channel_data.loc[0, "smw_note_name"] +
                               channel_data.loc[0, "smw_note_duration"] + " ")
            
            for ix in channel_data.index[1:]:
                if channel_data.loc[ix, "total_time_seconds"] >= channel_data.loc[ix - 1, "end_total_seconds"]:
                    channel_string += (channel_data.loc[ix, "smw_note_name"] +
                               channel_data.loc[ix, "smw_note_duration"] + " ")

            channel_strings[i + 1] = channel_string
        
        amk_txt = header
        
        for i in channel_strings.keys():
            amk_txt = amk_txt + "\n" + channel_strings[i]
        
        if not file is None:
            with open(file, "w") as text_file:
                print(addmusick_txt, file=text_file)

        if print_output:
            pp = pprint.PrettyPrinter()
            pp.pprint(amk_txt)
            
        if return_string:
            return(amk_txt)
        