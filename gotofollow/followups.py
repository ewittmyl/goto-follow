import gotocat as gc
import gTranRec as gtr
import pandas as pd
import numpy as np
from .gf_tools import UTC2date, query_db
from . import config
from datetime import datetime


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
        # only select UT 1-4
        # if image_table.shape[0] != 0:
        #     image_table = image_table[image_table.UT<'UT5']
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
        obsdate_fmt = "%Y-%m-%d %H:%M:%S"

        all_temp_paths = getattr(config, 'TEMP_PATH')

        self.image_table['temp_obsdate'] = 'nan'
        self.image_table['temp_filename'] = 'nan'
        self.image_table['temp_path'] = 'nan'
        g = gc.GOTOdb(phase=self.phase)

        for img in self.image_table.iterrows():
            try:
                temp_search = query_db(tile=img[1]["tile"], ut=img[1]["UT"], first_date=first_date, conn=g, hardware_config='new')
            except:
                g = gc.GOTOdb(phase=self.phase)
                temp_search = query_db(tile=img[1]["tile"], ut=img[1]["UT"], first_date=first_date, conn=g, hardware_config='new')
            
            if not temp_search.empty:
                self.image_table.at[img[0], 'temp_filename'] = temp_search.iloc[0].filename
                self.image_table.at[img[0], 'temp_obsdate'] = temp_search.iloc[0].obsdate
                # self.image_table.at[img[0], 'temp_path'] = all_temp_paths[]                    
            else:
                try:
                    temp_search = query_db(tile=img[1]["tile"], ut=img[1]["UT"], first_date=first_date, conn=g, hardware_config='old')
                except:
                    g = gc.GOTOdb(phase=self.phase)
                    temp_search = query_db(tile=img[1]["tile"], ut=img[1]["UT"], first_date=first_date, conn=g, hardware_config='old')
                if not temp_search.empty:
                    self.image_table.at[img[0], 'temp_filename'] = temp_search.iloc[0].filename
                    self.image_table.at[img[0], 'temp_obsdate'] = temp_search.iloc[0].obsdate
                    # self.image_table.at[img[0], 'temp_path'] = all_temp_paths[]       
