from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.exception import S3ResponseError
import argparse
import configparser 
import sys
import datetime, time
import requests
import json
import os
import logging

logging.basicConfig(level=logging.DEBUG)


def extractmeta(basefolder, file, fname):
    meta = dict()
    
    bf_name = basefolder.replace('\\', '/')
    tokens = file.replace(bf_name + '/', '').split('/')
    tenant_ivr_ccid = tokens[0].split('_')
    tenantname = tenant_ivr_ccid[0]
    ivr = tenant_ivr_ccid[1]
    ccid = tenant_ivr_ccid[2]
    cuuid_ani_dnis_connid = tokens[1].split('_')
    calluuid = cuuid_ani_dnis_connid[0]
    ani = cuuid_ani_dnis_connid[1]
    dnis = cuuid_ani_dnis_connid[2]
    connid = cuuid_ani_dnis_connid[3]
    gvpsid = tokens[2]
    timeString = fname.split('.')[2]
    timestamp = time.strptime(timeString, '%y%m%d%H%M%S')
    
    meta['timestamp'] = timestamp
    meta['calluuid'] = calluuid
    meta['tenantname'] = tenantname
    meta['ivr'] = ivr
    meta['ccid'] = ccid
    meta['connid'] = connid
    meta['ani'] = ani.replace('+', '')
    meta['dnis'] = dnis.replace('+', '')
    
    logging.debug('Uploading file: '+ file + ', tenant: ' + tenantname 
                  + ', ani: ' + ani + ', dnis: ' + dnis + ', ccid: ' + ccid)
    
    return meta

def create_headercookies(htccurl):
    pingurl = htccurl + '/api/v2/me'
    
    headers = dict()
    headers['content-type'] = 'application/json'
    try:
        # GET CSRF token
        htccresp = requests.get(pingurl, auth=(username, password))
        csrfHeader = htccresp.headers['X-CSRF-HEADER']
        csrfToken = htccresp.headers['X-CSRF-TOKEN']
        headers[csrfHeader] = csrfToken
    except KeyError as ex:
        logging.info('CSRF token not found in headers. CSRF feature not enabled? Skipping CSRF token')

    cookie = dict()
    
    for c in htccresp.cookies:
        cookie[c.name] = c.value
#         if c.name == 'JSESSIONID':
#                     cookie[c.name] = c.value

    return headers, cookie

def posthtccmeta(file, fname, metaList, s3path):
    meta_list = []
    
    htcc_meta = dict()
    media_file = dict()
    
    # mediaDescriptor
    starttime = time.strftime('%Y-%m-%dT%H:%M:%SZ', metaList['timestamp'])
    duration = os.path.getsize(file) * 8/ 32000
    endtime = datetime.datetime.utcfromtimestamp(time.mktime(metaList['timestamp']) + duration).strftime('%Y-%m-%dT%H:%M:%SZ')
    size = os.path.getsize(file)
    
    media_descr = {
                   'storage': 'awsS3',
                   'path': s3path,
                   'data': { 'bucket': s3bucket}
                   }
    
    parameters = {
                  'id': metaList['calluuid'],
                  'connId': metaList['connid']
                  }

    media_file['mediaId'] = fname
    media_file['type'] = 'audio/mp3'
    media_file['duration'] = str(duration)
    media_file['tenant'] = metaList['tenantname']
    media_file['ivrprofile'] = metaList['ivr']
    media_file['size'] = str(size)
    media_file['masks'] = []
    media_file['partitions'] = []
    media_file['accessgroups'] = []
    media_file['startTime'] = starttime
    media_file['stopTime'] = endtime
    media_file['callUUID'] = metaList['calluuid']
    media_file['parameters'] = parameters
    media_file['mediaDescriptor'] = media_descr

    htcc_meta['id'] = metaList['calluuid']
    htcc_meta['ccid'] = metaList['ccid']
    htcc_meta['region'] = region
    htcc_meta['callerPhoneNumber'] = metaList['ani']
    htcc_meta['dialedPhoneNumber'] = metaList['dnis']
    htcc_meta['mediaFiles'] = []
    htcc_meta['mediaFiles'].append(media_file)
    htcc_meta['eventHistory'] = []
    meta_list.append(htcc_meta)
    
    logging.debug(json.dumps(htcc_meta))
    
    metaurl = htccurl + '/internal-api/contact-centers/' + metaList['ccid'] + '/recordings'

    headers, cookie = create_headercookies(htccurl)
    
    response = requests.post(metaurl, data=json.dumps(htcc_meta), auth=(username, password), headers=headers, cookies=cookie)
    logging.info('Response status: ' + str(response.status_code) + response.text)

    if (response.status_code == 200):
        return True;
    
    return False;


def main():
    # Command-line configs
    parser = argparse.ArgumentParser(description='Specify configuration file for call recording including AWS S3, htcc, recording location info.')    
    parser.add_argument('--config', dest='config', required=True,
                       help='config file path')    
    args = parser.parse_args()
    
    config = args.config
    
    cfgParser = configparser.ConfigParser()
    cfgParser.read(config)
    
    try:
        global basefolder
        basefolder = cfgParser.get('Recording', 'basefolder');
        # HTCC
        global htccurl 
        htccurl = cfgParser.get('HTCC', 'htccurl')
        global username 
        username = cfgParser.get('HTCC', 'username')
        global region 
        region = cfgParser.get('HTCC', 'region')
        global password 
        password = cfgParser.get('HTCC', 'password')                
        # S3Key 
        global s3bucket
        s3bucket = cfgParser.get('S3Key', 's3bucket')
        global AWS_ACCESS_KEY_ID 
        AWS_ACCESS_KEY_ID = cfgParser.get('S3Key', 'awskeyid')
        global AWS_SECRET_ACCESS_KEY
        AWS_SECRET_ACCESS_KEY = cfgParser.get('S3Key', 'awssecretkey')
    except:
        logging.error('Error in config. Exit.')
        sys.exit(2)

    # S3 settings
    conn = S3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
      
    try:
        callrec_bucket = conn.get_bucket(s3bucket, validate=False)
    except S3ResponseError:
        callrec_bucket = conn.create_bucket(s3bucket)
    
    # Upload each recording
    for root, dirs, files in os.walk(basefolder):
        for fname in files:      
            if fname.endswith(('.mp3')):
                file = (os.path.join(root, fname)).replace('\\', '/')
                
                metaList = extractmeta(basefolder, file, fname)

                # Create new S3 object. Upload to S3
                obj_key = Key(callrec_bucket)
                recording_std_fname = metaList['calluuid'] + '_-_' + metaList['ani'] + '_' + metaList['dnis'] + '_' + time.strftime('%Y-%m-%d_%H-%M-%S', metaList['timestamp']) + '_-_-_' + metaList['ccid'] + '.mp3'
                obj_key.key = metaList['ccid'] + "/" + recording_std_fname
                obj_key.set_contents_from_filename(str(file))
                obj_key.get_contents_to_filename(str(file))
                obj_key.set_acl('public-read')      # TO-DO: public access?
    #             audio_url = obj_key.generate_url(expires_in=0, query_auth=False)
                
                # Post to HTCC
                postSuccess = posthtccmeta(file, recording_std_fname, metaList, obj_key.key)
                
                if postSuccess:
                    os.remove(file)
                if not os.listdir(root):
                    os.rmdir(root)
                    
    logging.info('Cleaning up folders')

    for root, dirs, files in os.walk(basefolder, topdown=False):
        for dirName in dirs:
            folder = (os.path.join(root, dirName)).replace('\\', '/')
            try:
                if not os.listdir(folder):
                    os.rmdir(folder)
            except OSError as ex:
                logging.error('Failed to clean up folders properly')

                
    logging.info('Audio upload completed')
 
    
if __name__ == '__main__':
    exit_code = 0
    run_time = main()
#     if run_time > 60:
#         exit_code = 60
    sys.exit(exit_code)   

