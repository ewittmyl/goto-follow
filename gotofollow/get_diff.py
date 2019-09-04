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
from .gf_tools import date_dir

class generate_report():
    """
    Generating reports for follow-up images. 
    1. TemplateComparing():
        using images taken before the trigger as templates
    2. FollowupComparing():
        using specific day of follow-up images as templates
    """
    @staticmethod
    def TemplateComparing(target, day=1, download=True, score=0.5, thresh='1.5', xmatch=['ned','mp','glade'], near_galaxy=True):
        
        # read GLADE
        cat = gtr.read_glade()

        # create table includes all images on a particular day of follow ups
        table = event.GetTemplate(target=target, day=day)

        # create list to include all processed images
        done_images = [fn.split("_report")[0]+"-median.fits" for fn in os.listdir("./") if 'report' in fn]
        if len(done_images) != 0:
            # print out all processed images if some images are done before
            print("Following images have been processed already:")
            print(done_images)
            # filter out done images in table
            done_mask = table.science_filename.isin(done_images)
            table = table[~done_mask]

            if table.shape[0] == 0:
                # return if science-template table is empty
                print("All images are processed!")
                return 
        else:
            # none images are done before
            if table.shape[0] == 0:
                # return if science-template table is empty
                print("SCIENCE-TEMPLATE table is empty!")
                with open("log.txt", "a+") as f:
                        f.write("Error: Empty SCIENCE-TEMPLATE table for {} day {} observations!!!".format(target, day))
                return 

        if download:
            # download files if download is True
            PASS_PATH = pkg_resources.resource_filename('gotofollow', 'PASSWORD')
            # read gotohead authorization
            with open(PASS_PATH, "r") as f:
                text = f.read().split("\n")
                username = text[0]
                password = text[1]

            for img in table.iterrows():

                # filename of science image
                sci_fn = img[1]["science_filename"]

                # download the science image from gotohead
                print("Downloading SCIENCE: {}".format(sci_fn))
                gtr.pull(username, password, sci_fn)
                
                if os.path.isfile("./" + sci_fn):
                    # keep going if the science image is downloaded
                    pass
                else:
                    # skip the loop if the science image cannot be downloaded
                    print("SCIENCE {} cannot be downloaded...".format(sci_fn))
                    with open("log.txt", "a+") as f:
                        f.write("Error: SCIENCE {} cannot be downloaded...\n".format(sci_fn))
                    continue
                
                try:
                    # use template inside FITS to run GTR
                    print("Extract TEMPLATE and DIFFERENCE from SCIENCE FITS + Run GTR...")
                    gtr.main(sci_fn,
                            det_thresh='1.5',
                            algorithm='rf',
                            cutoff_score=score,
                            on_science=True,
                            xmatch=xmatch,
                            filter_known=['mp', 'ned'],
                            glade_cat=cat.copy(),
                            near_galaxy=near_galaxy,
                            inspect=True)
                    # compress DIFFERENCE
                    os.system("fpack DIFFERENCE_{}".format(sci_fn))
                    # remove all images other than compressed DIFFERENCE image
                    os.system("rm -rf *.fits")
                except:
                    # download most recent observation as the template
                    print("No TEMPLATE and DIFFERENCE in SCIENCE {}...".format(sci_fn))
                    with open("log.txt", "a+") as f:
                            f.write("Warning: No TEMPLATE and DIFFERENCE in SCIENCE {}. Download most recent observation as TEMPLATE...\n".format(sci_fn))
                    
                    # filename of template image
                    temp_fn = img[1]["template_filename"]

                    # download the TEMPLATE FITS
                    print("Downloading latest observation as the TEMPLATE: {}".format(temp_fn))
                    gtr.pull(username, password, temp_fn)

                    if os.path.isfile("./" + temp_fn):
                        # run RB classifier
                        print("Run GTR...")
                        try:
                            gtr.main(sci_fn,
                                    template=temp_fn,
                                    det_thresh='1.5',
                                    algorithm='rf',
                                    cutoff_score=score,
                                    on_science=True,
                                    xmatch=xmatch,
                                    filter_known=['mp', 'ned'],
                                    glade_cat=cat.copy(),
                                    near_galaxy=near_galaxy,
                                    inspect=True)
                            # compress DIFFERENCE
                            os.system("fpack diff_{}".format(sci_fn))
                        except RuntimeError:
                            output = sci_fn.split("-median")[0] + "_report.pdf"
                            os.system("touch {}".format(output))
                        # remove all images other than compressed DIFFERENCE image
                        os.system("rm -rf *.fits")
                    else:
                        # skip this loop if TEMPLATE cannot be downloaded
                        print("TEMPLATE {} cannot be downloaded...".format(temp_fn))
                        with open("log.txt", "a+") as f:
                            f.write("Error: TEMPLATE {} cannot be downloaded...\n".format(temp_fn))
                        # remove all images other than compressed DIFFERENCE image
                        os.system("rm -rf *.fits")
                        continue
        else:
            # copy image to current directory if download is False
            IMG_PATH = getattr(config, 'FILE_PATH')

            for img in table.iterrows():
                # obsdate of science image
                sci_date = img[1]["science_date"]
                # filename of science image
                sci_fn = img[1]["science_filename"]
                
                print("Copying SCIENCE {} from 'IMG_PATH'...".format(sci_fn))

                # copying SCIENCE
                if os.path.isfile(IMG_PATH+sci_date+"/"+sci_fn):
                    os.system("cp "+IMG_PATH+sci_date+"/"+sci_fn+" .")
                if os.path.isfile(IMG_PATH+sci_date+"/final/"+sci_fn):
                    os.system("cp "+IMG_PATH+sci_date+"/final/"+sci_fn+" .")

                if os.path.isfile("./" + sci_fn):
                    # keep going if SCIENCE can be copied
                    pass
                else:
                    # skip this loop if SCIENCE cannot be copied
                    print("SCIENCE {} cannot be copied...".format(sci_fn))
                    with open("log.txt", "a+") as f:
                        f.write("Error: SCIENCE {} cannot be copied...\n".format(sci_fn))
                    continue
                
                try:
                    # extract TEMPLATE and DIFFERENCE image from SCIENCE image + run RB classifier
                    print("Extract TEMPLATE and DIFFERENCE from SCIENCE FITS + Run GTR...")
                    gtr.main(sci_fn,
                                template=None,
                                det_thresh='1.5',
                                algorithm='rf',
                                cutoff_score=score,
                                on_science=True,
                                xmatch=xmatch,
                                filter_known=['mp', 'ned'],
                                glade_cat=cat.copy(),
                                near_galaxy=near_galaxy,
                                inspect=True)
                    # compress DIFFERENCE
                    os.system("fpack DIFFERENCE_{}".format(sci_fn))
                    # remove all images other than compressed DIFFERENCE image
                    os.system("rm -rf *.fits")

                except:
                    # download most recent observation as the template
                    print("No TEMPLATE and DIFFERENCE in SCIENCE {}...".format(sci_fn))
                    with open("log.txt", "a+") as f:
                            f.write("Warning: No TEMPLATE and DIFFERENCE in SCIENCE {}. Copy most recent observation as TEMPLATE...\n".format(sci_fn))
                    # obsdate of template image
                    temp_date = img[1]["template_date"]
                    # filename of template image
                    temp_fn = img[1]["template_filename"]
                
                    # copy TEMPLATE from IMG_PATH
                    print("Copying latest observation as the TEMPLATE: {}".format(temp_fn))
                    if os.path.isfile(IMG_PATH+temp_date+"/"+temp_fn):
                        os.system("cp "+IMG_PATH+temp_date+"/"+temp_fn+" .")
                    if os.path.isfile(IMG_PATH+temp_date+"/final/"+temp_fn):
                        os.system("cp "+IMG_PATH+temp_date+"/final/"+temp_fn+" .")

                    if os.path.isfile("./" + temp_fn):
                        # run RB classifier
                        print("Run GTR...")
                        try:
                            gtr.main(sci_fn,
                                    template=temp_fn,
                                    det_thresh='1.5',
                                    algorithm='rf',
                                    cutoff_score=score,
                                    on_science=True,
                                    xmatch=xmatch,
                                    filter_known=['mp', 'ned'],
                                    glade_cat=cat.copy(),
                                    near_galaxy=near_galaxy,
                                    inspect=True)
                            # compress DIFFERENCE
                            os.system("fpack diff_{}".format(sci_fn))
                        except RuntimeError:
                            output = sci_fn.split("-median")[0] + "_report.pdf"
                            os.system("touch {}".format(output))
                        # remove all images other than compressed DIFFERENCE image
                        os.system("rm -rf *.fits")                    
                    else:
                        # skip this loop if SCIENCE cannot be downloaded
                        print("TEMPLATE {} cannot be copied...".format(temp_fn))
                        with open("log.txt", "a+") as f:
                            f.write("Error: TEMPLATE {} cannot be copied...\n".format(temp_fn))
                        os.system("rm -rf *.fits")
                        continue

                # clear record for SCIENCE and TEMPLATE
                temp_date, temp_fn, sci_date, sci_fn = "", "", "", ""    

    @staticmethod
    def FollowupComparing(target, early_day=1, late_day=2, download=True, score=0.5, thresh='1.5', xmatch=['ned','mp','glade'], near_galaxy=True):
        
        # read GLADE catalog
        cat = gtr.read_glade()

        # get followup images taken on early_day
        early_obs = event.Query(target=target, day=early_day)
        # give prefix for early_obs table columns
        early_obs.image_table.columns = "early_" + early_obs.image_table.columns

        if late_day:  # observation day you want to compare with the 'early_day'
    
            # get followup images taken on late_day
            late_obs = event.Query(target=target, day=late_day)
            # give prefix for early_obs table columns
            late_obs.image_table.columns = "late_" + late_obs.image_table.columns

            # merge obs table on tile and UT
            df = pd.merge(early_obs.image_table, late_obs.image_table, how="inner", left_on=["early_tile","early_UT"], right_on=["late_tile","late_UT"]) 
            
            # drop row without 'late_day' observations
            df.dropna(subset=['late_filename'], inplace=True)

        else: 
            # compare early_day obs with the next obs if late_day is not given
            
            # connect to database via `goto_cat`
            g4 = gc.GOTOdb(phase=4)

            # create empty df for 'late_obs'
            late_obs = pd.DataFrame(columns=["late_obsdate", "late_filename", "late_target"])

            for d in early_obs.iterrows():  # query for each 'early_day' observation to find the next observation
                obs_list = g4.query("""SELECT obsdate, filename, target FROM image WHERE target LIKE '%{}' 
                                AND filename LIKE '%{}-median.fits' ORDER BY 
                                obsdate ASC""".format(d[1]["early_target"], d[1]["early_UT"]))
                obs_list.columns = 'late_' + obs_list.columns
                obs_list = obs_list.drop_duplicates(subset="late_filename", keep="first")

                # selection the observations beyond the 'early_day' observation
                mask_obsdate = obs_list['late_obsdate'] > d[1]['early_obsdate']
                obs_list = obs_list[mask_obsdate]

                if obs_list.shape[0] != 0:
                    # if there exists observation(s) beyond 'early_day' observations
                    late_obs = late_obs.append(obs_list.iloc[0,:])  # pick the first observation beyond 'early_day'
                else:
                    # if no observation beyond 'early_day' observations
                    # create a row filled NaN
                    no_late_obs = pd.DataFrame(np.nan, index=[1], columns=late_obs.columns)
                    late_obs = late_obs.append(no_late_obs)
            
            # join both 'early_day' and 'late_day' table together
            late_obs = late_obs.reset_index().drop("index",axis=1)
            df = early_obs.join(late_obs)

            # drop row without 'late_day' observations
            df.dropna(subset=['late_filename'], inplace=True)

            df['late_date'] = [date_dir(str(d)) for d in df.late_obsdate]

        done_fn = [fn.split("_report")[0]+"-median.fits" for fn in os.listdir("./") if 'report' in fn]

        if len(done_fn) != 0:
            # print out all processed images if some images are done before
            print("Following images have been processed already:")
            print(done_fn)
            # filter out done images in table
            done_mask = df.early_filename.isin(done_fn)
            df = df[~done_mask]

            if df.shape[0] == 0:
                # return if science-template table is empty
                print("All images are processed!")
                return 
        else:
            # none images are done before
            if df.shape[0] == 0:
                # return if science-template table is empty
                print("SCIENCE-TEMPLATE table is empty!")
                with open("log.txt", "a+") as f:
                        f.write("Error: Empty SCIENCE-TEMPLATE table!!!")
                return

        if download: 
            # download files if download is True
            PASS_PATH = pkg_resources.resource_filename('gotofollow', 'PASSWORD')
            # read gotohead authorization
            with open(PASS_PATH, "r") as f:
                text = f.read().split("\n")
                username = text[0]
                password = text[1]
   
            for img in df.iterrows():

                # filename of template image
                temp_fn = img[1]["late_filename"]
                # filename of science image
                sci_fn = img[1]["early_filename"]

                # download early day image
                print("Downloading early image: {}".format(sci_fn))
                gtr.pull(username, password, sci_fn)
                
                # download late day image
                print("Downloading late image: {}".format(temp_fn))
                gtr.pull(username, password, temp_fn)

        
                if os.path.isfile("./" + sci_fn) and os.path.isfile("./" + temp_fn):
                    # run RB classifier if both early and late images exist
                    print("Running GTR...")
                    try:
                        gtr.main(sci_fn,
                                template=temp_fn,
                                det_thresh='1.5',
                                algorithm='rf',
                                cutoff_score=score,
                                on_science=True,
                                xmatch=xmatch,
                                filter_known=['mp', 'ned'],
                                glade_cat=cat.copy(),
                                near_galaxy=near_galaxy,
                                inspect=True)
                        # compress DIFFERENCE
                        os.system("fpack diff_{}".format(sci_fn))
                    except RuntimeError:
                        output = sci_fn.split("-median")[0] + "_report.pdf"
                        os.system("touch {}".format(output))
                    # remove all images other than compressed DIFFERENCE image
                    os.system("rm -rf *.fits")                    
                else:
                    print("Image is missing...")
                    os.system("rm -rf *fits")

        else:
            # copy image to current directory if download is False
            IMG_PATH = getattr(config, 'FILE_PATH')

            for img in df.iterrows():
                # obsdate of template image
                temp_date = img[1]["late_date"]
                # filename of template image
                temp_fn = img[1]["late_filename"]
                # obsdate of science image
                sci_date = img[1]["early_date"]
                # filename of science image
                sci_fn = img[1]["early_filename"]

                print("Copying early image '{}' from 'IMG_PATH'...".format(sci_fn))

                # copy early image from IMG_PATH
                if os.path.isfile(IMG_PATH+sci_date+"/"+sci_fn):
                    os.system("cp "+IMG_PATH+sci_date+"/"+sci_fn+" .")
                if os.path.isfile(IMG_PATH+sci_date+"/final/"+sci_fn):
                    os.system("cp "+IMG_PATH+sci_date+"/final/"+sci_fn+" .")
                
                # copy late image from IMG_PATH
                print("Copying late image '{}' from 'IMG_PATH'...".format(temp_fn))

                if os.path.isfile(IMG_PATH+temp_date+"/"+temp_fn):
                    os.system("cp "+IMG_PATH+temp_date+"/"+temp_fn+" .")
                if os.path.isfile(IMG_PATH+temp_date+"/final/"+temp_fn):
                    os.system("cp "+IMG_PATH+temp_date+"/final/"+temp_fn+" .")
                    
                if os.path.isfile("./" + sci_fn) and os.path.isfile("./" + temp_fn):
                    # run RB classifier if both early and late images exist
                    print("Running GTR...")
                    try:
                        gtr.main(sci_fn,
                                template=temp_fn,
                                det_thresh='1.5',
                                algorithm='rf',
                                cutoff_score=score,
                                on_science=True,
                                xmatch=xmatch,
                                filter_known=['mp', 'ned'],
                                glade_cat=cat.copy(),
                                near_galaxy=near_galaxy,
                                inspect=True)
                        # compress DIFFERENCE
                        os.system("fpack diff_{}".format(sci_fn))
                    except RuntimeError:
                        output = sci_fn.split("-median")[0] + "_report.pdf"
                        os.system("touch {}".format(output))
                    # remove all images other than compressed DIFFERENCE image
                    os.system("rm -rf *.fits")                    
                else:
                    print("Image is missing...")
                    os.system("rm -rf *fits")
