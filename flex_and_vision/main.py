
# [START app]
from datetime import datetime
import logging
import os
import io
import simplejson

from flask import Flask, redirect, render_template, request

from google.cloud import datastore
from google.cloud import storage
from google.cloud import vision


CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET')


app = Flask(__name__)


@app.route('/')
def homepage():
    return render_template('homepage.html')


@app.route('/upload_photo', methods=['GET', 'POST'])
def upload_photo():
    photo = request.files['file']

    # Create a Cloud Storage client.
    storage_client = storage.Client()

    # Get the bucket that the file will be uploaded to.
    bucket = storage_client.get_bucket(CLOUD_STORAGE_BUCKET)

    # Create a new blob and upload the file's content.
    blob = bucket.blob(photo.filename)
    blob.upload_from_string(
            photo.read(), content_type=photo.content_type)

    # Make the blob publicly viewable.
    blob.make_public()

    # Create a Cloud Vision client.
    id_text_list = []
    client = vision.ImageAnnotatorClient

    # Use the Cloud Vision client to detect text for our image.
    source_uri = 'gs://{}/{}'.format(CLOUD_STORAGE_BUCKET, blob.name)
    #print(source_uri)
    
    image = vision.types.Image(source=vision.types.ImageSource(gcs_image_uri=source_uri))
    #print(dir(image))
    client_vision = client()
    response = client_vision.text_detection(image=image)

    texts = response.text_annotations

    for text in texts:
        t = text.description
        id_text_list.append(t)
    # print(id_text_list)
    scanned_info = id_text_list[0].split('\n')
    # print('********',scanned_info)
    Final_Info = {}
    
    if 'AADHAAR' in id_text_list:
    	find_YOB = scanned_info[[indx for indx, val in enumerate(scanned_info) if 'YOB' in val.upper()][0]]
    	YOB_POS = scanned_info.index(find_YOB)
    	Final_Info = [{'Type': 'AADHAAR'}, {'Name': scanned_info[YOB_POS - 1]}, {'Father Name': ""},
                  {'YOB': int("".join(filter(str.isdigit, scanned_info[YOB_POS])))}, {'AADHAAR': scanned_info[YOB_POS+2]}]
    
    elif 'Permanent' in id_text_list:
        Final_Info = [{'Type': 'PAN'}, {'Name': scanned_info[2]}, {'Father Name': scanned_info[3]},
                      {'DOB': scanned_info[4]}, {'PAN': scanned_info[6]}]

    elif 'Aadhaar' in id_text_list:
        find_DOB = scanned_info[[indx for indx, val in enumerate(scanned_info) if 'DOB' in val.upper()][0]]
        DOB_Pos = scanned_info.index(find_DOB)
        Final_Info = [{'Type': 'AADHAAR'}, {'Name': scanned_info[DOB_Pos - 1]}, {'Father Name': ''},
                      {'DOB': find_DOB[find_DOB.find(': ') + 1:]}, {'AADHAAR': scanned_info[len(scanned_info) - 2]}]
    elif 'GOVERNMENT' in id_text_list:
        find_DOB = scanned_info[[indx for indx, val in enumerate(scanned_info) if 'DOB' in val.upper()][0]]
        DOB_Pos = scanned_info.index(find_DOB)
        Final_Info = [{'Type': 'AADHAAR'}, {'Name': scanned_info[DOB_Pos - 1]}, {'Father Name': ''},
                      {'DOB': find_DOB[find_DOB.find(': ') + 1:]}, {'AADHAAR': scanned_info[DOB_Pos + 2]}]
    else:
        Final_Info = ['ID is Invalid or not clear']

    j_final = simplejson.dumps(Final_Info)
    #print(j_final)
    # Redirect to the home page.
    return j_final
    
    

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END app]
