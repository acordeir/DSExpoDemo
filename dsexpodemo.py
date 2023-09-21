# -*- coding: utf-8 -*-
"""DSExpoDemo.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/16WmcCr5RIpymkubeX46C5mPoEFoC_1ku
"""


from huggingface_hub import notebook_login

#My API key which has access to Llama2 models: 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
#notebook_login()

import torch
import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import pipeline
import locale
import scrubadub
import nltk
nltk.download('punkt')
import regex as re
import textwrap
from langchain import HuggingFacePipeline
from langchain import PromptTemplate,  LLMChain
import cv2
import matplotlib.pyplot as plt
import numpy as np
import math
from pypdf import PdfReader



tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf",
                                         token = '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')

model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-chat-hf",
                                             device_map='auto',
                                             torch_dtype=torch.float16,
                                             token = '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')

# Use a pipeline for later

'''
summarize_pipe = pipeline("summarization",
                model=model,
                tokenizer= tokenizer
                )
'''

generation_pipe = pipeline("text-generation",
                model=model,
                tokenizer= tokenizer,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                max_new_tokens = 512,
                do_sample=True,
                top_k=30,
                num_return_sequences=1,
                eos_token_id=tokenizer.eos_token_id
                )


B_INST, E_INST = "[INST]", "[/INST]"
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
DEFAULT_SYSTEM_PROMPT = """\
You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.

If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information."""


def get_prompt(instruction, new_system_prompt=DEFAULT_SYSTEM_PROMPT ):
    SYSTEM_PROMPT = B_SYS + new_system_prompt + E_SYS
    prompt_template =  B_INST + SYSTEM_PROMPT + instruction + E_INST
    return prompt_template

def parse_text(text):
        wrapped_text = textwrap.fill(text, width=100)
        print(wrapped_text +'\n\n')


#summarize_llm = HuggingFacePipeline(pipeline = summarize_pipe, model_kwargs = {'temperature':0.1})
generation_llm = HuggingFacePipeline(pipeline = generation_pipe, model_kwargs = {'temperature':0.1})

system_prompt1 = "You are an advanced assistant that excels at summarization. "
instruction1 = "Summarize the following text, be sure to include all important information:\n\n {text}"
template1 = get_prompt(instruction1, system_prompt1)

system_prompt2 = "You are an advanced assistant that excels at text generation"
instruction2 = "Write {length} words based on the following text:\n\n {text}"
template2 = get_prompt(instruction2, system_prompt2)

summarize_prompt = PromptTemplate(template=template1, input_variables=["text"])
summarize_llm_chain = LLMChain(prompt=summarize_prompt, llm=generation_llm)

generation_prompt = PromptTemplate(template=template2, input_variables=["length", "text"])
generation_llm_chain = LLMChain(prompt=generation_prompt, llm=generation_llm)

"""## Text Cleaner"""

def privatize_text(text):
  #Phone numbers
  phone_pattern = '^\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\s*$'
  text1 = re.sub(phone_pattern, '{{PHONE NUMBER}}', text)
  print(text1)
  #Social Security Number
  ss_pattern = '^(?!(000|666|9))\d{3}-(?!00)\d{2}-(?!0000)\d{4}$'
  text2 = re.sub(ss_pattern, '{{SOCIAL SECURITY NUMBER}}', text1)
  #Email Address
  email_pattern = '^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$'
  text3 = re.sub(email_pattern, '{{EMAIL}}', text2)

  scrubber = scrubadub.Scrubber()
  scrubber.add_detector(scrubadub.detectors.TextBlobNameDetector)
  privatized_text = scrubber.clean(text3)
  return privatized_text

"""## Image Privatize"""


def privatize_img(image):
  #Used as reference: https://huggingface.co/spaces/sciling/Face_and_Plate_License_Blur/tree/main/models

  plate_blur = 100
  face_blur = 100

  #model_face = torch.load('face_model.pt')
  #model_face.eval()
  '''
  model_plate = yolov5.load('keremberke/yolov5m-license-plate', device="cpu")
  # # set model parameters
  model_plate.conf = 0.25  # NMS confidence threshold
  model_plate.iou = 0.45  # NMS IoU threshold
  model_plate.agnostic = False  # NMS class-agnostic
  model_plate.multi_label = False  # NMS multiple labels per box
  model_plate.max_det = 1000  # maximum number of detections per image

  results_plate = model_plate(image, augment=True)
  boxes_plate_list = results_plate.pred[0][:, :4].cpu().numpy().tolist()
  for box in boxes_plate_list:
      ROI = image[int(box[1]):int(box[3]), int(box[0]):int(box[2])]

      blur_value = (int(plate_blur) * 2 - 1)
      blur = cv2.GaussianBlur(ROI, (blur_value, blur_value), 20, cv2.BORDER_DEFAULT)
      # Insert ROI back into image
      image[int(box[1]):int(box[3]), int(box[0]):int(box[2])] = blur

  # Converting BGR image into a RGB image
  #image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
  '''
  image = np.array(image)

  face_detect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml')
  face_data = face_detect.detectMultiScale(image, 1.3, 5)

  # Draw rectangle around the faces which is our region of interest (ROI)
  for (x, y, w, h) in face_data:
      p1 = (int(x), int(y))
      p2 = (int(x+w), int(y+h))

      circle_center = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
      circle_radius = int(math.sqrt(w * w + h * h) // 2)

      ROI = np.zeros(image.shape, dtype='uint8')
      cv2.circle(ROI, circle_center, circle_radius, (255, 255, 255), -1)
      # applying a gaussian blur over this new rectangle area
      blur_value = (int(face_blur) * 2 - 1)
      blur = cv2.GaussianBlur(image, (blur_value, blur_value), 20, cv2.BORDER_DEFAULT)

      image = np.where(ROI > 0, blur, image)

  return image

def plotImages(img):
    plt.imshow(img)
    plt.axis('off')
    plt.style.use('seaborn')
    plt.show()

"""## PDF Reader"""


def preview_text(file):
  reader = PdfReader(file)
  page = reader.pages[0]
  text = page.extract_text()
  wrapped_text = textwrap.shorten(text, width=300)
  return str(wrapped_text)

def privatize_summarize(file = None, input_type = 'Use File', text_input = None, summarize = False, privatize = False):
  if input_type == 'Use File':
    if file is None:
      return 'Please include a file or select "Use Text".'
    filepath = file.name
    reader = PdfReader(filepath)
    number_of_pages = len(reader.pages)
    summaries = []
    for p in reader.pages:
      text = p.extract_text()

      if summarize:
        summary = summarize_llm_chain.run(text)
      else:
        summary = text

      if privatize:
        summary = privatize_text(summary)

      summaries.append(summary)
    return '\n'.join(summaries)
  else:
    if summarize:
      summary = summarize_llm_chain.run(text_input)
    else:
      summary = text_input

    if privatize:
      summary = privatize_text(summary)
    return summary

privatize_summarize(file = None, input_type = 'Use Text', text_input = 'This is a test', privatize = True)

def upload(file_name):
  text = preview_text(file_name)
  return file_name, text

"""## Gradio App"""

import gradio as gr

with gr.Blocks() as demo:
  with gr.Tab('Privatize PDF'):
    with gr.Row():
      with gr.Row():
        aps_button = gr.Button("APS Demo")
        ca_button = gr.Button("Client Agreement Demo")
        mr_button = gr.Button("Medical Record Demo")
        pr_button = gr.Button("Payroll Demo")
      pdf_input = gr.File()
      preview_input = gr.Textbox(label = 'Preview', lines = 4)

    with gr.Accordion("Generate Your Own Text", open = False):
      with gr.Row():
        prompt_input = gr.Textbox(label = 'Prompt')
        generate_text_button = gr.Button("Generate Text")
        input_type = gr.Radio(["Use File", "Use Text"], label="Input Type", value = 'Use File')
      doc_length = gr.Slider(label = 'Length of document', minimum = 50, maximum = 500)
      with gr.Row():
        text_input = gr.Textbox(label = 'Text Input', lines = 3, min_width = 1000, max_lines = 100)
        clear_text_button = gr.ClearButton()


    with gr.Row():
      summarize_button = gr.Button("Summarize")
      privatize_button = gr.Button("Privatize")
      summarize_privatize_button = gr.Button("Summarize & Privatize")

    pdf_summary = gr.Textbox(label = 'Document Summary', lines = 5)


  with gr.Tab('Privatize Image'):
    with gr.Row():
      image_input = gr.Image(source="upload", type="numpy", optional=False)
      image_output = gr.Image()
    image_button = gr.Button("Privatize")


  aps_button.click(lambda x: 'APS_Demo_DSExpo.pdf', ca_button, outputs = pdf_input)
  ca_button.click(lambda x: 'ClientAgreement_Demo_DSExpo.pdf', ca_button, outputs = pdf_input)
  mr_button.click(lambda x: 'MedicalRecord_Demo_DSExpo.pdf', mr_button, outputs = pdf_input)
  pr_button.click(lambda x: 'Payroll_Demo_DSExpo.pdf', pr_button, outputs = pdf_input)

  pdf_input.change(lambda x: preview_text(x.name), inputs = pdf_input, outputs = preview_input)

  generate_text_button.click(lambda doc_length, prompt_input: generation_llm_chain.run({'length':doc_length, 'text' : prompt_input}), inputs = [doc_length, prompt_input], outputs = text_input)
  clear_text_button.click(lambda x: '', inputs = clear_text_button, outputs = text_input)

  image_button.click(privatize_img, inputs = image_input, outputs = image_output)

  privatize_button.click(lambda pdf_input, input_type, text_input: privatize_summarize(pdf_input, input_type, text_input, privatize = True), inputs = [pdf_input, input_type, text_input], outputs = pdf_summary)
  summarize_button.click(lambda pdf_input, input_type, text_input: privatize_summarize(pdf_input, input_type, text_input, summarize = True), inputs = [pdf_input, input_type, text_input], outputs = pdf_summary)
  summarize_privatize_button.click(lambda pdf_input, input_type, text_input: privatize_summarize(pdf_input, input_type, text_input, summarize = True, privatize = True), inputs = [pdf_input, input_type, text_input], outputs = pdf_summary)

demo.launch()
