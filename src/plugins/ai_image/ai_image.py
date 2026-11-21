from plugins .base_plugin .base_plugin import BasePlugin
from openai import OpenAI
from PIL import Image
from io import BytesIO
import base64
import requests
import logging
logger =logging .getLogger (__name__ )
IMAGE_MODELS =["dall-e-3","dall-e-2","gpt-image-1"]
DEFAULT_IMAGE_MODEL ="dall-e-3"
DEFAULT_IMAGE_QUALITY ="standard"
class AIImage (BasePlugin ):
    def generate_settings_template (self ):
        template_params =super ().generate_settings_template ()
        template_params ['api_key']={
        "required":True ,
        "service":"OpenAI",
        "expected_key":"OPEN_AI_SECRET"
        }
        return template_params
    def generate_image (self ,settings ,device_config ):
        api_key =device_config .load_env_key ("OPEN_AI_SECRET")
        if not api_key :
            raise RuntimeError ("Ключ OPEN AI API не настроен.")
        text_prompt =settings .get ("textPrompt","")
        image_model =settings .get ('imageModel',DEFAULT_IMAGE_MODEL )
        if image_model not in IMAGE_MODELS :
            raise RuntimeError ("Предоставлена ​​неверная модель изображения.")
        image_quality =settings .get ('quality',"medium"if image_model =="gpt-image-1"else "standard")
        randomize_prompt =settings .get ('randomizePrompt')=='true'
        image =None
        try :
            ai_client =OpenAI (api_key =api_key )
            if randomize_prompt :
                text_prompt =AIImage .fetch_image_prompt (ai_client ,text_prompt )
            image =AIImage .fetch_image (
            ai_client ,
            text_prompt ,
            model =image_model ,
            quality =image_quality ,
            orientation =device_config .get_config ("orientation")
            )
        except Exception as e :
            logger .error (f"Failed to make Open AI request: {str (e )}")
            raise RuntimeError ("Ошибка запроса на открытие ИИ, проверьте журналы.")
        return image
    @staticmethod
    def fetch_image (ai_client ,prompt ,model ="dall-e-3",quality ="standard",orientation ="horizontal"):
        logger .info (f"Generating image for prompt: {prompt }, model: {model }, quality: {quality }")
        prompt +=(
        ". Изображение должно полностью занимать весь холст без каких-либо рамок. "
        "границы или посевные площади. Никаких пустых мест и искусственного обрамления."
        )
        prompt +=(
        "Сосредоточьтесь на простоте, смелых формах и сильном контрасте, чтобы повысить ясность. "
        "и внешняя привлекательность. Избегайте чрезмерной детализации или сложных градиентов, гарантируя "
        "дизайн хорошо сочетается с плоскими яркими цветами."
        )
        args ={
        "model":model ,
        "prompt":prompt ,
        "size":"1024x1024",
        }
        if model =="dall-e-3":
            args ["size"]="1792x1024"if orientation =="horizontal"else "1024x1792"
            args ["quality"]=quality
        elif model =="gpt-image-1":
            args ["size"]="1536x1024"if orientation =="horizontal"else "1024x1536"
            args ["quality"]=quality
        response =ai_client .images .generate (**args )
        if model in ["dall-e-3","dall-e-2"]:
            image_url =response .data [0 ].url
            response =requests .get (image_url )
            img =Image .open (BytesIO (response .content ))
        elif model =="gpt-image-1":
            image_base64 =response .data [0 ].b64_json
            image_bytes =base64 .b64decode (image_base64 )
            img =Image .open (BytesIO (image_bytes ))
        return img
    @staticmethod
    def fetch_image_prompt (ai_client ,from_prompt =None ):
        logger .info (f"Getting random image prompt...")
        system_content =(
        "Вы творческий помощник, генерирующий чрезвычайно случайные и уникальные подсказки к изображениям. "
        "Избегайте общих тем. Сосредоточьтесь на неожиданных, нетрадиционных и причудливых сочетаниях. "
        "художественного стиля, среды, предметов, периодов времени и настроений. Никаких повторов. Подсказки "
        "должно содержать не более 20 слов и указывать случайного исполнителя, фильм, телешоу или период времени. "
        "for the theme. Do not provide any headers or repeat the request, just provide the "
        "обновленное приглашение в вашем ответе."
        )
        user_content =(
        "Дайте мне совершенно случайное изображение, что-нибудь неожиданное и креативное! "
        "Давайте посмотрим, что может приготовить ваш искусственный интеллект!"
        )
        if from_prompt and from_prompt .strip ():
            system_content =(
            "Вы творческий помощник, специализирующийся на создании высокоописательных "
            "and unique prompts for creating images. When given a short or simple image "
            "описание, ваша задача — переписать его в более подробное, образное, "
            "и описательная версия, которая отражает суть оригинала, в то же время "
            "делая его уникальным и ярким. Избегайте добавления ненужных деталей, но не стесняйтесь "
            "включать творческие и визуальные улучшения. Избегайте общих тем. Сосредоточиться на "
            "неожиданные, нестандартные и причудливые сочетания художественного стиля, среды, "
            "subjects, time periods, and moods. Do not provide any headers or repeat the "
            "запрос, просто укажите обновленное приглашение в ответе. Подсказки "
            "должно содержать не более 20 слов и указывать случайного исполнителя, фильм, телешоу или время. "
            "период для темы."
            )
            user_content =(
            f"Original prompt: \"{from_prompt }\"\n"
            "Перепишите его, чтобы сделать его более подробным, творческим и уникальным, оставаясь при этом "
            "верен первоначальной идее. Включите яркие изображения и описательные детали. "
            "Не меняйте тему подсказки."
            )
        response =ai_client .chat .completions .create (
        model ="gpt-4o",
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
        logger .info (f"Generated random image prompt: {prompt }")
        return prompt