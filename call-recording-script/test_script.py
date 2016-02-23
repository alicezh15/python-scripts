import base64;
import httplib2;
import json;
 
GWS_BASE_URI = "http://s-usw1-htcc.genhtcc.com:80/api/v2" 
ADMIN_USERNAME = "voice_2126_admin"
ADMIN_PASSWORD = "voice_2126_admin"

X_CSRF_HEADER = "x-csrf-header"
X_CSRF_TOKEN = "x-csrf-token"

jsessionid = None
csrfHeaderName = None
csrfTokenValue = None

http = httplib2.Http(".cache")    
 
def create_request_headers():
    request_headers = dict()
    request_headers["Content-Type"] = "application/json"
#     request_headers["Authorization"] = "Basic " + base64.b64encode(ADMIN_USERNAME + ":" + ADMIN_PASSWORD)

    if jsessionid:
        request_headers["Cookie"] = jsessionid;
        print ("Using JSESSIONID %s" % jsessionid)

    if csrfHeaderName and csrfTokenValue:
        print ("Adding csrf header [%s] with value [%s]..." % (csrfHeaderName, csrfTokenValue))
        print ()
        request_headers[csrfHeaderName] = csrfTokenValue
    else:
        print ("No csrf token, skipping...")
        print ()

    return request_headers
 
def post(uri, content):
    request_headers = create_request_headers()
    body = json.dumps(content, sort_keys=True, indent=4)
 
    print ("POST %s (%s/%s)..." % (uri, ADMIN_USERNAME, ADMIN_PASSWORD))
    print (body)
    print ()   
 
    response_headers, response_content = http.request(uri, "POST", body = body, headers = request_headers, auth=(ADMIN_USERNAME,ADMIN_PASSWORD))
    status = response_headers["status"]
 
    ugly_response = json.loads(response_content)
    pretty_response = json.dumps(ugly_response, sort_keys=True, indent=4)    
 
    print ("Response: %s" % (status))
    print ("%s" % (pretty_response))
    print    ()
 
    return response_headers, ugly_response

def get(uri):

    global csrfHeaderName
    global csrfTokenValue
    global jsessionid
    
    request_headers = create_request_headers()
    print ("GET %s (%s/%s)..." % (uri, ADMIN_USERNAME, ADMIN_PASSWORD))
    print    ()

    response_headers, response_content = http.request(uri, "GET", headers = request_headers)
    status = response_headers["status"]
    if response_headers["set-cookie"]:
        cookiestr = response_headers["set-cookie"]
        jsessionid = cookiestr.split(";")[0]
        print ("Set JSESSIONID %s..." % jsessionid)
    
    ugly_response = json.loads(response_content)
    pretty_response = json.dumps(ugly_response, sort_keys=True, indent=4)    
    
    print ("Response: %s" % (status))
    print ("%s" % (pretty_response))
    print    ()

    if X_CSRF_HEADER in response_headers:
        csrfHeaderName = response_headers[X_CSRF_HEADER]
        print ("Saved csrf header name [%s]" % csrfHeaderName)

    if X_CSRF_TOKEN in response_headers:
        csrfTokenValue = response_headers[X_CSRF_TOKEN]
        print ("Saved csrf token value [%s]" % csrfTokenValue)
        print ()
    
    return response_headers, ugly_response   
 
def check_response(response_headers, expected_code):
    if response_headers["status"] != expected_code:
        print ("Request failed.")
        exit(-1)
 
def test_call_recording():
    uri = "http://s-usw1-htcc.genhtcc.com:80/internal-api/contact-centers/e11057c0-2702-11e4-aadb-d123a5caa27d/recordings"   

    payload = {"region": "us", "eventHistory": [], "id": "CSSTASTSST4HJ4NQ8C2QBHU2IC0000CM", "mediaFiles": [{"stopTime": "2014-12-03T18:31:26Z", "size": "24768", "duration": "6.192", "callUUID": "CSSTASTSST4HJ4NQ8C2QBHU2IC0000CM", "accessgroups": [], "type": "audio/mpeg3", "mediaDescriptor": {"storage": "awsS3", "data": {"bucket": "gvp-callrecording"}, "path": "Environment1/callrec.01840147-10010BF9.141203133120.mp3"}, "startTime": "2014-12-03T13:31:20Z", "partitions": [], "ivrprofile": "DefaultApplication", "tenant": "Environment1", "masks": [], "parameters": {"id": "CSSTASTSST4HJ4NQ8C2QBHU2IC0000CM"}, "mediaId": "callrec.01840147-10010BF9.141203133120.mp3"}], "dialedPhoneNumber": "9557", "ccid": "abcdef", "callerPhoneNumber": "alchoi4"}

    response_headers, response_content = post(uri, payload)
    check_response(response_headers, "200")
 
def getToken():
    uri = "%s/diagnostics/version" % (GWS_BASE_URI)

    response_headers, response_content = get(uri)
    check_response(response_headers, "200")

if __name__ == "__main__":
  
    getToken()
    test_call_recording()
