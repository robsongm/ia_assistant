import os
from flask import Flask, render_template, request, Response
from google.cloud import speech
from youtube_transcript_api import YouTubeTranscriptApi
#Modelo para usar a partir de videos no computador
import moviepy.editor as mp
import speech_recognition as sr
from dotenv import load_dotenv


app = Flask(__name__)

load_dotenv()

print(os.getenv('SECRET_KEY'))

def localVideoTranscrpit(path):

  # Load the video
  video = mp.VideoFileClip(path)

  # Extract the audio from the video
  audio_file = video.audio
  audio_file.write_audiofile("video_test.wav")

  # Initialize recognizer
  r = sr.Recognizer()

  # Load the audio file
  with sr.AudioFile("video_test.wav") as source:
      data = r.record(source)

  # Convert speech to text
  text = r.recognize_google(data)
  return text

#Modelo para usar a partir de videos no youtube
def extract_transcript_details(youtube_video_url):
  try:
      video_id = youtube_video_url.split("=")[1]
      transcript_text = YouTubeTranscriptApi.get_transcript(video_id, ['en', 'pt'])

      transcript = ""
      for i in transcript_text:
          transcript += " " + i["text"]

      return transcript
  except Exception as e:
      raise e
  

import google.generativeai as genai

def analise(type, message):

    api_key = os.getenv('SECRET_KEY')
    print(api_key)
    genai.configure(api_key=api_key)



    # Set up the model
    generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 0,
    "max_output_tokens": 8192,
    }

    safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    ]
    system_instruction = "Você é uma ux research que analisa entrevistas com usuários para entender suas necessidades, dificuldades, dúvidas e hábitos. Ao receber uma transcrição de uma entrevista você deve categorizar e resumir os temas que foram falados e dizer em qual minuto esse assunto foi falado."

    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                                generation_config=generation_config,
                                system_instruction=system_instruction,
                                safety_settings=safety_settings)
    chat = model.start_chat(history=[])

    if type == 'URL':
        transcrpit = extract_transcript_details(message)
    if type == 'TRANSCRPIT':
        transcrpit = localVideoTranscrpit(message)
    if type == 'TALK':
        transcrpit = message
        
    response = chat.send_message(transcrpit)
    print(response.text)
    return response.text



@app.route('/')
def index():
    return render_template('index.html')


def generate(messages, model_type):
    return_message = ''
    if messages[-1]['content'] == 'Vamos lá? Digite o formato da entrevista que você gostaria de analisar: URL do Youtube ou Texto transcrito' and messages[-1]['role'] == 'assistant':
        return_message = ''
    elif messages[-1]['content'] in ['upload'] and messages[-1]['role'] == 'user':
        return_message = 'UPLOAD_FILE'
    elif messages[-1]['content'] in ['url do youtube', 'youtube', 'Youtube', 'URL do Youtube', 'url', 'URL', 'Url'] and messages[-1]['role'] == 'user':
        return_message = 'Envie a URL do video'
    elif messages[-1]['content'] in ['Envie o transcrpit', 'transcrito', 'Texto transcrito', 'texto'] and messages[-1]['role'] == 'user':
        return_message = 'Envie o transcrpit'
    else:
         return_message = analise('TALK',  messages[-1]['content'] )
    if len(messages) > 1:
        if messages[-2]['content'] in ['Envie a URL do video'] and messages[-2]['role'] == 'assistant':
            return_message =  analise('URL', messages[-1]['content']) + 'Que entrevista bacana! Você  fazer perguntas sobre trechos, trazer citações, adicionar outras entrevistas com esse tema para fazer comparações ou digite “nova conversa” para reiniciar o chat e analisar outras pesquisar'
        elif messages[-2]['content'] in ['Envie o transcrpit'] and messages[-2]['role'] == 'assistant':
            return_message =  analise('TRANSCRPIT', messages[-1]['content']) + 'Que entrevista bacana! Você  fazer perguntas sobre trechos, trazer citações, adicionar outras entrevistas com esse tema para fazer comparações ou digite “nova conversa” para reiniciar o chat e analisar outras pesquisar'
    return return_message


@app.route('/gpt4', methods=['POST'])
def gpt4():
    data = request.get_json()
    messages = data.get('messages', [])
    model_type = data.get('model_type')

    assistant_response = generate(messages, model_type)
    return Response(assistant_response, mimetype='text/event-stream')



if __name__ == '__main__':
    app.run(debug=True)
