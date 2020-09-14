from . import config
import os
import gotocat as gc

def UTC2date(time_string):

    import datetime
    
    time_string = time_string.split(".")[0]

    # convert time string to datetime object
    time_stamp = datetime.datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S")
    
    # define noon datetime object
    noon_time = datetime.time(12, 00, 00)
    
    # define timedelta for subtracting correction
    dt = datetime.timedelta(days=1)
    
    if (time_stamp.time() > noon_time):
        # datetime remains unchanged if time > noon
        pass
    elif (time_stamp.time() < noon_time):
        # datetime subtracted by 1 day if time < noon
        time_stamp = time_stamp - dt
    
    date_string = str(time_stamp.date())
    
    return date_string

def find(date, filename):
    abs_path = ""
    IMG_PATHS = getattr(config, 'IMG_PATHS')
    for path in IMG_PATHS:
        abs_path = os.path.join(path, date)
        if os.path.exists(abs_path):
            if 'final' in os.listdir(abs_path):
                abs_path = os.path.join(abs_path, 'final')
            if filename in os.listdir(abs_path):
                abs_path = os.path.join(abs_path, filename)
                return abs_path
            else:
                return 'nan'

def query_db(tile, ut, first_date, conn, hardware_config='new'):
    all_temp_paths = getattr(config, 'TEMP_PATH')
    ut_conv = getattr(config, 'hardware_config')
    cmd = "SELECT obsdate, filename, target, instrument FROM image WHERE ("
    for i, t in enumerate(all_temp_paths):
        cmd += "target LIKE '{}%{}'".format(t, tile)
        if i == len(all_temp_paths)-1:
            if hardware_config == 'new':
                cmd += ") AND instrument='{}' AND obsdate > '2020-08-10 12:00:00'".format(ut)
            elif hardware_config == 'old':
                if first_date < '2020-08-10':  
                    cmd += ") AND instrument='{}' AND obsdate < '2020-08-10 12:00:00'".format(ut)
                else:
                    cmd += ") AND instrument='{}' AND obsdate < '2020-08-10 12:00:00'".format(ut_conv[ut])
            else:
                raise KeyError("Argument 'hardware_config' can only be 'new' or 'old'.")
        else:
            cmd += " or "

    temp_search = conn.query(cmd)
    if not temp_search.empty:
        temp_search['date'] = [UTC2date(str(d)) for d in temp_search['obsdate']]
        sub_temp_df = temp_search[temp_search.date < first_date]
        if not sub_temp_df.empty:
            sub_temp_df = sub_temp_df.sort_values("obsdate", ascending=False)
        return sub_temp_df
        
    else:
        return temp_search