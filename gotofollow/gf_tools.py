from . import config
import os

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
        print("Finding {} in {}".format(filename, path))
        for root, dirs, files in os.walk(path):
            if date in dirs:
                abs_path = os.path.join(root, date)
                abs_path = '/final/'.join([abs_path, filename])
                return abs_path
    return 0