import os
import pkg_resources

DATA_PATHS = '/export/'
# IMG_PATHS = ['/export/' + s + '/gotophoto/storage/pipeline/' for s in os.listdir('/export/')]
# IMG_PATHS = [s for s in IMG_PATHS if os.path.exists(s)]

TEMP_PATH = {
    'TEMPL_0020':'/export/{}/gotophoto/storage/template_images/'.format('gotodata2'),
    'TEMPL_0021':'/export/{}/gotophoto/storage/template_images/'.format('gotodata2'),
    'TEMPL_0023':'/export/{}/gotophoto/storage/template_images/'.format('gotodata3'),
    'TEMPL_0024':'/export/{}/gotophoto/storage/template_images/'.format('gotodata3'),
}

hardware_config = {
    'start_time':'2020-08-10 12:00:00',
    'UT1':'UT6',
    'UT2':'UT2',
    'UT3':'UT3',
    'UT4':'UT7',
    'UT5':'UT5',
    'UT6':'UT4',
    'UT7':'UT1',
    'UT8':'UT8'
}

phase = 4