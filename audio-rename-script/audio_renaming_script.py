from __future__ import print_function
import config as cfg
import os
import shutil
import logging

logging.basicConfig(level=logging.INFO)

basefolder = cfg.config['basefolder']
name_delim = cfg.config['filename_delimiter']
keep_common = cfg.config['keep_common']

# Construct common if True
logging.info("Basefolder: " + basefolder + "    Delimiter: " + name_delim)

# Output new audio mapping to file
f = open(os.path.join(basefolder, "audio_rename_table.csv"), 'w')
print("Old Name,New Name", file=f)

# Renaming audio
for root, dirs, files in os.walk(basefolder):
    for name in files:
        if name.endswith((".wav")):
            path_concat = (os.path.join(root, name)).replace("\\", "/")
            name_changed = path_concat.replace(basefolder+"/", "").replace("/", name_delim);
            logging.info(name_changed)
            # Output to file
            print(path_concat + "," + name_changed, file=f)
            os.rename(path_concat, os.path.join(basefolder, name_changed))

f.close()

logging.info("Cleaning up directory")

# Cleaning up
for old_dir in filter(lambda d: os.path.isdir(os.path.join(basefolder, d)), os.listdir(basefolder)):
    shutil.rmtree(os.path.join(basefolder, old_dir).replace("\\", "/"))
    logging.info(old_dir + " directory removed")
