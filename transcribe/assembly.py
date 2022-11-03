from distutils import text_file
import requests
import sys
import time
import os

#upload
upload_endpoint = "https://api.assemblyai.com/v2/upload"
transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
headers = {'authorization': os.environ.get("ASSEMBLY_API_KEY")}
# headers = {'authorization': "a2cccfe057a84cea8ef69bdbc8b0a2af"}

def upload(filename):
    def read_file(filename, chunk_size=5242880):
        with open(filename, 'rb') as _file:
            while True:
                data = _file.read(chunk_size)
                if not data:
                    break
                yield data

    upload_response = requests.post(upload_endpoint,
                            headers=headers,
                            data=read_file(filename))

    audio_url = upload_response.json()['upload_url']
    return audio_url

#transcribe
def transcribe(audio_url):
    transcript_request = { "audio_url": audio_url }
    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers)
    job_id = transcript_response.json()['id']
    return job_id

#pull (tells ai if it is ready or not)
def pull(transcript_id):
    pulling_endpoint = transcript_endpoint + "/" + transcript_id
    pulling_response = requests.get(pulling_endpoint, headers=headers)
    return pulling_response.json()
 
#save transcription to txt file
def get_transcription_result_url(audio_url):
    transcript_id = transcribe(audio_url)
    while True:
        data = pull(transcript_id)
        
        if data['status'] == 'completed':
            return data, None
        elif data['status'] == 'error':
            return data, data['error']
        
        print("Running...")
        time.sleep(10)

def save_transcript(audio_url, filename):
    data, error = get_transcription_result_url(audio_url)
    
    if data:
        text_filename = filename + ".txt"
        with open(text_filename, "w") as f:
            # f.write(f"{data['text']} : {data['words'][-1]['end']/1000} sec")
            f.write(data['text'])
        print("Transcription saved")
        file = open(text_filename)
        return file.read()
    elif error:
        print("Something went wrong")