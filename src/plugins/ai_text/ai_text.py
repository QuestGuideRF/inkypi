from plugins .base_plugin .base_plugin import BasePlugin
from utils .app_utils import resolve_path
from openai import OpenAI
from PIL import Image ,ImageDraw ,ImageFont
from utils .image_utils import resize_image
from io import BytesIO
from datetime import datetime
import requests
import logging
import textwrap
import os
logger =logging .getLogger (__name__ )
class AIText (BasePlugin ):
    def generate_settings_template (self ):
        template_params =super ().generate_settings_template ()
        template_params ['api_key']={
        "required":True ,
        "service":"OpenAI",
        "expected_key":"OPEN_AI_SECRET"
        }
        template_params ['style_settings']=True
        return template_params
    def generate_image (self ,settings ,device_config ):
        api_key =device_config .load_env_key ("OPEN_AI_SECRET")
        if not api_key :
            raise RuntimeError ("Ключ OPEN AI API не настроен.")
        title =settings .get ("title")
        text_model =settings .get ('textModel')
        if not text_model :
            raise RuntimeError ("Требуется текстовая модель.")
        text_prompt =settings .get ('textPrompt','')
        if not text_prompt .strip ():
            raise RuntimeError ("Требуется текстовая подсказка.")
        try :
            ai_client =OpenAI (api_key =api_key )
            prompt_response =AIText .fetch_text_prompt (ai_client ,text_model ,text_prompt )
        except Exception as e :
            logger .error (f"Failed to make Open AI request: {str (e )}")
            raise RuntimeError ("Ошибка запроса на открытие ИИ, проверьте журналы.")
        dimensions =device_config .get_resolution ()
        if device_config .get_config ("orientation")=="vertical":
            dimensions =dimensions [::-1 ]
        image_template_params ={
        "title":title ,
        "content":prompt_response ,
        "plugin_settings":settings
        }
        image =self .render_image (dimensions ,"ai_text.html","ai_text.css",image_template_params )
        return image
    @staticmethod
    def fetch_text_prompt (ai_client ,model ,text_prompt ):
        logger .info (f"Getting random text prompt from input {text_prompt }, model: {model }")
        system_content =(
        "Вы очень умный помощник по созданию текста. Создавайте краткие, "
        "релевантные и точные ответы, адаптированные к вводу пользователя. Ответ "
        "должно быть 70 слов или меньше."
        "ВАЖНО: Не перефразируйте, не перефразируйте и не вводите введение. Ответить напрямую "
        "к запросу без добавления пояснений или дополнительного контекста "
        "ВАЖНО: Если ответ естественным образом требует новой строки для форматирования, укажите "
        "символ новой строки '\n' явно для каждой новой строки. Для обычных предложений "
        "или абзацы не содержат символ новой строки."
        f"For context, today is {datetime .today ().strftime ('%Y-%m-%d')}"
        )
        user_content =text_prompt
        response =ai_client .chat .completions .create (
        model =model ,
        messages =[
        {
        "role":"system",
        "content":system_content
        },
        {
        "role":"user",
        "content":user_content
        }
        ],
        temperature =1
        )
        prompt =response .choices [0 ].message .content .strip ()
        logger .info (f"Generated random text prompt: {prompt }")
        return prompt