import gotocat as gc
import gTranRec as gtr
import pandas as pd
import numpy as np
from .gf_tools import UTC2date

class event():
    """
    Use event.Query() to create event class object.
    Event class object including:
    1. self.target: target name of the event
    2. self.image_table: table including all information for the images of the event
    3. self.dates: dates of follow ups
    """
    def __init__(self, target, image_table, dates, phase):
        self.target = target 
        self.image_table = image_table  # table containing all follow-up observations
        self.dates = dates  # list of the follow-up dates
        self.phase = phase  # which phase to look for

    @classmethod
    def Query(cls, target, day=None, phase=4):
        """
        Parameters:
        -----------
        target: str
            target name of the event e.g. LVC_S190901ap
        day: None / int
            which day of observations
        phase: int
            GOTO phase
        
        Return:
        -----------
        event class object
        """
        # connect with GOTO database
        g4 = gc.GOTOdb(phase=phase)

        # query all images for the events
        image_table = g4.query("""SELECT obsdate, filename, target FROM image WHERE target LIKE '{}%' 
                        AND filename LIKE '%median.fits' ORDER BY obsdate ASC""".format(target))

        # drop duplicated images
        image_table = image_table.drop_duplicates(subset="filename", keep="first")

        # create useful columns
        image_table['date'] = [UTC2date(str(d)) for d in image_table.obsdate]
        image_table['tile'] = [t.split("_")[-1] for t in image_table.target]
        image_table['UT'] = [fn.split("_")[1][:3] for fn in image_table.filename]
        image_table = image_table.reset_index().drop("index",axis=1)

        # get all observation dates
        dates = image_table.date.unique()

        if day == None:
            # return all observations on all follow-up dates if 'day' = None
            return cls(target, image_table, dates, phase)
        else:
            try:
                # return the images taken on the given follow-up day for given 'day'
                day_mask = image_table.date == dates[day-1]  
                image_table = image_table[day_mask].reset_index().drop("index",axis=1)
                return cls(target, image_table, dates, phase)
            except:
                # return empty table if error occurs
                col = ['obsdate', 'filename', 'target', 'date', 'tile', 'UT']
                image_table = pd.DataFrame(columns=col)
                print("No observations have been taken on the {} day.".format(day)) 
                return cls(target, image_table, dates, phase)

    def GetTemplate(self):
        # define first follow-up date
        first_date = self.dates[0]

        g = gc.GOTOdb(phase=self.phase)

        temp_df = pd.DataFrame(columns=["temp_obsdate", "temp_filename", "temp_target", "temp_date"])
        temp_obsdate, temp_filename, temp_target, temp_date = [], [], [], []

        for img in self.image_table.iterrows():
            query_cmd = """SELECT obsdate, filename, target FROM image WHERE target
                        LIKE '%{}' AND filename LIKE '%{}-median.fits' ORDER BY obsdate DESC""".format(img[1]["tile"], img[1]["UT"])
            temp_search = g.query(query_cmd)
            
            if temp_search.shape[0] != 0:
                temp_search['date'] = [UTC2date(str(d)) for d in temp_search['obsdate']]
                temp_search = temp_search[temp_search['date'] < first_date]
                if temp_search.shape[0] != 0:
                    temp_obsdate.append(temp_search.obsdate.values[0])
                    temp_filename.append(temp_search.filename.values[0])
                    temp_target.append(temp_search.target.values[0])
                    temp_date.append(temp_search.date.values[0])
                else:
                    temp_obsdate.append('NaN')
                    temp_filename.append('NaN')
                    temp_target.append('NaN')
                    temp_date.append('NaN')
            else:
                print("No {}({}) images could be found in database.".format(img[1]["tile"],img[1]["UT"]))

        temp_df['temp_obsdate'] = temp_obsdate
        temp_df['temp_filename'] = temp_filename
        temp_df['temp_target'] = temp_target
        temp_df['temp_date'] = temp_date

        self.image_table = self.image_table.join(temp_df)
