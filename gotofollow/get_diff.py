from .followups import event
import gTranRec as gtr
import os
import pkg_resources
import pandas as pd
import gotocat as gc
import numpy as np
from datetime import date
from datetime import timedelta
from astropy.io import fits
from astropy.io.fits import getdata, update, getheader
from . import config
from .gf_tools import UTC2date, find

file_path = '/export/'

class GenerateReports():

    @staticmethod
    def TemplateComparing(target, day=1, score=0.85, near_galaxy=True, filter_known=True, phase=4):
        # obtain image table for followup images and get their template
        print("Query all follow-up images for {} taken on day {}...".format(target, day))
        event_cls = event.Query(target, day=day, phase=phase)
        event_cls.GetTemplate()
        if event_cls.image_table.shape[0] == 0:
            # terminate the run if the image table is empty
            print("Image table is empty.")
            return

        # define all processed images which will be skipped in this run
        processed_img = [''.join([fn.split("_report")[0],".fits"]) for fn in os.listdir("./") if 'report' in fn]
        if len(processed_img) != 0:
            print("Skip processing below processed images...")
            print(processed_img)
            # filter out the processed images in the image table
            processed_mask = event_cls.image_table['filename'].isin(processed_img)
            event_cls.image_table = event_cls.image_table[~processed_mask]
            print("Processing below images...")
            print(event_cls.image_table['filename'].values)
            
            if event_cls.image_table.shape[0] == 0:
                print("All images are processed.")
                return
        
        for img in event_cls.image_table.iterrows():
            sci_fn = img[1]['filename']
            sci_date = img[1]['date']
            sci_path = find(sci_date, sci_fn)

            # get image path in gotohead
            if sci_path != 0:
                print("Copying science {} to the current directory from {}".format(sci_fn, sci_path))
                os.system('cp {} .'.format(sci_path))
            else:
                print("Science {} cannot be copied to the current directory.".format(sci_fn))
                sci_date, sci_fn = "", ""
                pass
            

            try:
                print("Running GTR on {}...".format(sci_fn))
                gtr.main(sci_fn, template=None, thresh=score, near_galaxy=near_galaxy, filter_known=filter_known, report=True)
                os.system("fpack {}".format(sci_fn))
                os.system("rm -rf *.fits")
            except:
                print("GTR cannot be ran on {}...".format(sci_fn))
                os.system("rm -rf *.fits")
                sci_date, sci_fn = "", ""
                pass

            sci_date, sci_fn = "", ""

        # define all processed images which will be skipped in this run
        processed_img = [''.join([fn.split("_report")[0],".fits"]) for fn in os.listdir("./") if 'report' in fn]
        if len(processed_img) != 0:
            print("Skip processing below processed images...")
            print(processed_img)
            # filter out the processed images in the image table
            processed_mask = event_cls.image_table['filename'].isin(processed_img)
            event_cls.image_table = event_cls.image_table[~processed_mask]
            print("Processing below images...")
            print(event_cls.image_table['filename'].values)
            
            if event_cls.image_table.shape[0] == 0:
                print("All images are processed.")
                return

        for img in event_cls.image_table.iterrows():
            # define useful information for both science and template images in order to be copied to the current directory
            sci_fn = img[1]['filename']
            sci_date = img[1]['date']
            temp_fn = img[1]['temp_filename']
            temp_date = img[1]['temp_date']
            sci_path = find(sci_date, sci_fn)
            temp_path = find(temp_date, temp_fn)
            if sci_path != 0:
                print("Copying science {} to the current directory from {}".format(sci_fn, sci_path))
                os.system('cp {} .'.format(sci_path))
                if temp_path != 0:
                    print("Copying template {} to the current directory from {}".format(temp_fn, temp_path))
                    os.system('cp {} .'.format(temp_path))
                else:
                    print("Template {} cannot be copied to the current directory.".format(temp_fn))
                    os.system('rm -rf *.fits')
                    sci_path, sci_fn, temp_path, temp_fn = "", "", "", ""
                    pass
            else:
                print("Science {} cannot be copied to the current directory.".format(sci_fn))
                sci_path, sci_fn, temp_path, temp_fn = "", "", "", ""
                pass

            try:
                print("Running GTR on {}...".format(sci_fn))
                gtr.main(sci_fn, template=temp_fn, thresh=score, near_galaxy=near_galaxy, filter_known=filter_known, report=True)
                os.system("fpack {}".format(sci_fn))
                os.system("rm -rf *.fits")
            except:
                print("GTR cannot be ran on {}...".format(sci_fn))
                os.system("rm -rf *.fits")
                sci_date, sci_fn, temp_date, temp_fn = "", "", "", ""
                pass
            sci_date, sci_fn, temp_date, temp_fn = "", "", "", ""
        

    @staticmethod
    def FollowupComparing(target, sci_day=1, temp_day=None, score=0.69, near_galaxy=True, filter_known=True, phase=4):     
        # get followup images taken on sci_day
        sci_obs = event.Query(target, day=sci_day, phase=phase)

        # give prefix for early_obs table columns
        sci_obs.image_table.columns = "sci_" + sci_obs.image_table.columns

        if sci_obs.shape[0] == 0:
            print("Science table is empty.")
            return

        if temp_day:
            # get followup images taken on temp_day
            temp_obs = event.Query(target, day=temp_day, phase=phase)
            # give prefix for temp_obs table columns
            temp_obs.image_table.columns = "temp_" + temp_obs.image_table.columns

            # merge obs table on tile and UT
            df = pd.merge(sci_obs.image_table, temp_obs.image_table, how="inner", left_on=["sci_tile","sci_UT"], right_on=["temp_tile","temp_UT"]) 
                
            # drop row without 'temp_day' observations
            df.dropna(subset=['temp_filename'], inplace=True)

            if df.shape[0] == 0:
                print("Image table is empty.")
                return

        else:
            # compare sci_day obs with the next obs if temp_day is not given
            # connect to database via `goto_cat`
            g4 = gc.GOTOdb(phase=phase)

            # create empty df for 'temp_obs'
            temp_obs = pd.DataFrame(columns=["temp_obsdate", "temp_filename", "temp_target"])

            for d in sci_obs.iterrows():
                obs_list = g4.query("""SELECT obsdate, filename, target FROM image WHERE target LIKE '%{}' 
                                AND filename LIKE '%{}-median.fits' ORDER BY 
                                obsdate ASC""".format(d[1]["sci_target"], d[1]["sci_UT"]))
                obs_list.columns = 'temp_' + obs_list.columns
                obs_list = obs_list.drop_duplicates(subset="temp_filename", keep="first")

                # selection the observations beyond the 'sci_day' observation
                mask_beyond_firstobs = obs_list['temp_obsdate'] > d[1]['sci_obsdate']
                obs_list = obs_list[mask_beyond_firstobs]

                if obs_list.shape[0] != 0:
                    # if there exists observation(s) beyond 'early_day' observations
                    temp_obs = temp_obs.append(obs_list.iloc[0,:])  # pick the first observation beyond 'sci_day'
                else:
                    # if no observation beyond 'sci_day', create a rwo filled with NaN
                    no_temp_obs = pd.DataFrame(np.nan, index=[1], columns=temp_obs.columns)
                    temp_obs = temp_obs.append(no_temp_obs)

                # join both 'sci_day' and 'temp_day' table together
                temp_obs = temp_obs.reset_index().drop("index",axis=1)
                df = sci_obs.join(latetemp_obs_obs)

                # drop row without 'temp_day' observations
                df.dropna(subset=['temp_filename'], inplace=True)

                df['temp_date'] = [UTC2date(str(d)) for d in df.temp_obsdate]

            if df.shape[0] == 0:
                print("Image table is empty.")
                return

            # define all processed images which will be skipped in this run
            processed_img = [''.join([fn.split("_report")[0],"-median.fits"]) for fn in os.listdir("./") if 'report' in fn]

            if len(processed_img) != 0:
                print("Skip processing processed images...")
                # filter out the processed images in the image table
                processed_mask = df.sci_filename.isin(processed_img)
                df = df[~processed_mask]

                if df.shape[0] == 0:
                    # return if science-template image table is empty
                    print("All images are processed!")
                    return 


        for img in df.iterrows():
            # define useful information for both science and template images in order to be copied to the current directory
            sci_fn = img[1]['sci_filename']
            sci_date = img[1]['date']
            temp_fn = img[1]['temp_filename']
            temp_date = img[1]['temp_date']
            sci_path = find(sci_date, sci_fn)
            temp_path = find(temp_date, temp_fn)
            
            if sci_path != 0:
                print("Copying science {} to the current directory from {}".format(sci_fn, sci_path))
                os.system('cp {} .'.format(sci_path))
                if temp_path != 0:
                    print("Copying template {} to the current directory from {}".format(temp_fn, temp_path))
                    os.system('cp {} .'.format(temp_path))
                else:
                    print("Template {} cannot be copied to the current directory.".format(temp_fn))
                    os.system('rm -rf *.fits')
                    sci_path, sci_fn, temp_path, temp_fn = "", "", "", ""
                    pass
            else:
                print("Science {} cannot be copied to the current directory.".format(sci_fn))
                sci_path, sci_fn, temp_path, temp_fn = "", "", "", ""
                pass

            try:
                print("Running GTR on {}...".format(sci_fn))
                gtr.main(sci_fn, template=temp_fn, thresh=score, near_galaxy=near_galaxy, filter_known=filter_known, report=True)
                os.system("fpack {}".format(sci_fn))
                os.system("rm -rf *.fits")
            except:
                print("GTR cannot be ran on {}...".format(sci_fn))
                os.system("rm -rf *.fits")
                sci_date, sci_fn, temp_date, temp_fn = "", "", "", ""
                pass
            sci_date, sci_fn, temp_date, temp_fn = "", "", "", ""

