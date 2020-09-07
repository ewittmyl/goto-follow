import os
import pkg_resources

DATA_PATHS = '/export/'
IMG_PATHS = ['/export/' + s + '/gotophoto/storage/pipeline/' for s in os.listdir('/export/')]
IMG_PATHS = [s for s in os.listdir(s) if os.path.exists(s)]