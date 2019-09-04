import gotocat as gc
import gTranRec as gtr
import pandas as pd
import numpy as np
from .gf_tools import date_dir

class event():
    """
    Use event.Query() to create event class object.
    Event class object including:
    1. self.target: target name of the event
    2. self.image_table: table including all information for the images of the event
    3. self.dates: dates of follow ups
    """
    def __init__(self, target, image_table, dates):
        self.target = target 
        self.image_table = image_table  # table containing all follow-up observations
        self.dates = dates  # list of the follow-up dates

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
        image_table['date'] = [date_dir(str(d)) for d in image_table.obsdate]
        image_table['tile'] = [t.split("_")[-1] for t in image_table.target]
        image_table['UT'] = [fn.split("_")[1][:3] for fn in image_table.filename]

        # get all observation dates
        dates = image_table.date.unique()

        if day == None:
            # return all observations on all follow-up dates if 'day' = None
            return cls(target, image_table, dates)
        else:
            try:
                # return the images taken on the given follow-up day for given 'day'
                day_mask = image_table.date == dates[day-1]  
                image_table = image_table[day_mask].reset_index().drop("index",axis=1)
                return cls(target, image_table, dates)
            except:
                # return empty table if error occurs
                col = ['obsdate', 'filename', 'target', 'date', 'tile', 'UT']
                image_table = pd.DataFrame(columns=col)
                print("No observations have been taken on the {} day.".format(day)) 
                return cls(target, image_table, dates)

    @staticmethod
    def GetTemplate(target, day=1):
        """
        This standalone function returns a complete table including follow-up
        images and the template of them.
        
        Parameters:
        -----------
        target: str
            target name of the event e.g. LVC_S190901ap
        day: int
            which day of observations

        Returns:
        -----------
        pandas dataframe including all information of science images and the templates
        """
        event_class = event.Query(target, day=day)

        # get first obs date
        first_date = event_class.dates[0]

        # define table of all follow-up observations of the 'day'
        images_of_the_day = event_class.image_table
        images_of_the_day.columns = "science_" + images_of_the_day.columns

        g4 = gc.GOTOdb(phase=4)

        # define empty template table
        templates = pd.DataFrame(columns=["template_obsdate","template_filename","template_target"])

        # query the database to get the last observation before the first follow-up date for all follow-up images
        for img in images_of_the_day.iterrows():
            temp_images = g4.query("""SELECT obsdate, filename, target FROM image WHERE target LIKE '%{}' 
                             AND filename LIKE '%{}-median.fits' ORDER BY obsdate ASC""".format(img[1]["science_tile"],
                                                                                               img[1]["science_UT"]))

            # add prefix on the columns indicating those images would be the template
            temp_images.columns = "template_" + temp_images.columns
            temp_images['template_date'] = [date_dir(str(d)) for d in temp_images['template_obsdate']]

            # only select those template taken before the first date of follow up
            mask_before_trigger = temp_images['template_date'] < first_date
            temp_images = temp_images[mask_before_trigger]

            if temp_images.shape[0] != 0:
                temp_images = temp_images.iloc[-1,:]  # select the last one before the first date of follow up as the template
                templates = templates.append(temp_images)
            else:
                no_temp = pd.DataFrame(np.nan, index=[1], columns=["template_filename","template_date","template_obsdate","template_target"])
                templates = templates.append(no_temp)

        templates = templates.reset_index().drop("index",axis=1)

        # join the science and the template table together
        result = images_of_the_day.join(templates)
        useful_col = ["science_filename","science_date","science_obsdate","science_target",
                      "template_filename","template_date","template_obsdate","template_target"]
        
        result = result[useful_col]
        return result
