------------------------------------------------------------------------
Installation Instructions
------------------------------------------------------------------------
AWS S3:
- Create AWS key, secret key if doesn't already have one
Ensure that the keys have full read/write permission inside the bucket!
- Create call-recording bucket on S3
------------------------------------------------------------------------
*HTCC: manual configuration

(Use REST client)

- Check if call recording table exist for given contact center:
	GET <HTCC host>/api/v2/ops/contact-centers/<Contact Center ID>/recording-tables
	
- If doesn't exists, forcefully create the call-recording column family:
	POST <HTCC host>/api/v2/ops/contact-centers/ <Contact Center ID>/recordings
	Request body: 
		{"operationName":"createCRCF"}
		
- Setup Credential for your Contact-Center AWS S3 storage:
Make sure not to mix up AWS secretKey and accessKey(shorter one)!
	PUT <HTCC host>/api/v2/ops/contact-centers/<CCID>/settings/recordings
	{
	 	"store": [
	           {
	          	 "awsS3": {
	                            "accessKey": "<AWSAccessKey>", 
	                            "secretKey": "<AwsSecretKey>", 
	                            "bucketName": "<bucket-name>"
	                    }
	                }
	           ]
	}
	
- Retrieve crRegion on HTCC for "region" in config
Recordings require a matching region on HTCC in order to be submitted properly
- Retrieve CCID for config

*For all HTCC requests, make sure to include in Headers: Authentication (user/password), X-CSRF-TOKEN, Content-Type:application/json.

------------------------------------------------------------------------
Python:

Requires Python 2.6 or above ("python -V" to check)

Install pip:
yum install -y python-pip

Installs boto.s3, AWS S3 Python API package:
sudo pip install boto
	- if already exists, do an update

Install requests package if doesn't exist:
pip install requests
------------------------------------------------------------------------

Unpack script.
Edit configuration file. See below

------------------------------------------------------------------------
Execution Instruction
------------------------------------------------------------------------

Single run:
python <python script path> --config <config.ini path>


Cronjob:

Set cronjob as super/root user:
 sudo crontab -e

Running every 5min:
 */5 * * * * /usr/bin/python <python script path> --config <config.ini path>
 e.g.:
 */5 * * * * /usr/bin/python /home/ec2-user/pythontest/callrec_upload.py --config /home/ec2-user/pythontest/config.ini


------------------------------------------------------------------------
Configuration
------------------------------------------------------------------------
Config file: .ini
All following are required parameters

[Recording]
basefolder=[call recording base folder]

[S3Key]
awskeyid=[AWS Access Key]
awssecretkey=[AWS Secret Key]
s3bucket=[S3 bucket name]

[HTCC]
htccurl=[HTCC host url. e.g: http://s-usw1-htcc.genhtcc.com:80]
region=[crRegion on HTCC]
username=[htcc authentication username]
password=[htcc authentication password]

-------------------------------------------------------------------------

Description

Script scans for .mp3 starting from basefolder.
Parse meta data based on folder name structure.
Uploads audio files to S3.
Submits meta data along with S3 file location info to HTCC.
Cleans up, removes audio, deletes any empty folders.

Sample meta data submitted to HTCC:
{
	"eventHistory": [],
	"mediaFiles": [{
		"mediaDescriptor": {
			"path": "18bae11b-3028-4844-aba1-ac47bad457f0/callrec.008E0149-12132920.141216184241.mp3",
			"data": {
				"bucket": "gvp-callrecording"
			},
			"storage": "awsS3"
		},
		"accessgroups": [],
		"parameters": {
			"connId": "00710255fc5bacfe",
			"id": "01I6E87G24A6B45KKSC362LAES000781"
		},
		"size": "153504",
		"duration": "38.376",
		"partitions": [],
		"stopTime": "2014-12-16T23:43:19Z",
		"type": "audio/mp3",
		"ivrprofile": "IVRAppDefault",
		"mediaId": "callrec.008E0149-12132920.141216184241.mp3",
		"startTime": "2014-12-16T18:42:41Z",
		"tenant": "Environment",
		"masks": [],
		"callUUID": "01I6E87G24A6B45KKSC362LAES000781"
	}],
	"dialedPhoneNumber": "+18489993333",
	"id": "01I6E87G24A6B45KKSC362LAES000781",
	"callerPhoneNumber": "+16172640431",
	"ccid": "18bae11b-3028-4844-aba1-ac47bad457f0",
	"region": "usw1"
}
