from plugins .base_plugin .base_plugin import BasePlugin
from PIL import Image ,UnidentifiedImageError
from io import BytesIO
import requests
import logging
from random import randint
from datetime import datetime ,timedelta ,date
from functools import lru_cache
from typing import Dict ,Any
logger =logging .getLogger (__name__ )
class Wpotd (BasePlugin ):
    SESSION =requests .Session ()
    HEADERS ={'User-Agent':'InkyPi/0.0 (https://github.com/fatihak/InkyPi/)'}
    API_URL ="https://en.wikipedia.org/w/api.php"
    def generate_settings_template (self )->Dict [str ,Any ]:
        template_params =super ().generate_settings_template ()
        template_params ['style_settings']=False
        return template_params
    def generate_image (self ,settings :Dict [str ,Any ],device_config :Dict [str ,Any ])->Image .Image :
        logger .info (f"WPOTD plugin settings: {settings }")
        datetofetch =self ._determine_date (settings )
        logger .info (f"WPOTD plugin datetofetch: {datetofetch }")
        data =self ._fetch_potd (datetofetch )
        picurl =data ["image_src"]
        logger .info (f"WPOTD plugin Picture URL: {picurl }")
        image =self ._download_image (picurl )
        if image is None :
            logger .error ("Не удалось загрузить изображение WPOTD.")
            raise RuntimeError ("Не удалось загрузить изображение WPOTD.")
        if settings .get ("shrinkToFitWpotd")=="true":
            dimensions =device_config .get_resolution ()
            if device_config .get_config ("orientation")=="vertical":
                dimensions =dimensions [::-1 ]
            max_width ,max_height =dimensions
            image =self ._shrink_to_fit (image ,max_width ,max_height )
            logger .info (f"Image resized to fit device dimensions: {max_width },{max_height }")
        return image
    def _determine_date (self ,settings :Dict [str ,Any ])->date :
        if settings .get ("randomizeWpotd")=="true":
            start =datetime (2015 ,1 ,1 )
            delta_days =(datetime .today ()-start ).days
            return (start +timedelta (days =randint (0 ,delta_days ))).date ()
        elif settings .get ("customDate"):
            return datetime .strptime (settings ["customDate"],"%Y-%m-%d").date ()
        else :
            return datetime .today ().date ()
    def _download_image (self ,url :str )->Image .Image :
        try :
            if url .lower ().endswith (".svg"):
                logger .warning ("Формат SVG не поддерживается Pillow. Пропуск загрузки изображения.")
                raise RuntimeError ("Неподдерживаемый формат изображения: SVG.")
            response =self .SESSION .get (url ,headers =self .HEADERS ,timeout =10 )
            response .raise_for_status ()
            return Image .open (BytesIO (response .content ))
        except UnidentifiedImageError as e :
            logger .error (f"Unsupported image format at {url }: {str (e )}")
            raise RuntimeError ("Неподдерживаемый формат изображения.")
        except Exception as e :
            logger .error (f"Failed to load WPOTD image from {url }: {str (e )}")
            raise RuntimeError ("Не удалось загрузить изображение WPOTD.")
    def _fetch_potd (self ,cur_date :date )->Dict [str ,Any ]:
        title =f"Template:POTD/{cur_date .isoformat ()}"
        params ={
        "action":"query",
        "format":"json",
        "formatversion":"2",
        "prop":"images",
        "titles":title
        }
        data =self ._make_request (params )
        try :
            filename =data ["query"]["pages"][0 ]["images"][0 ]["title"]
        except (KeyError ,IndexError )as e :
            logger .error (f"Failed to retrieve POTD filename for {cur_date }: {e }")
            raise RuntimeError ("Не удалось получить имя файла POTD.")
        image_src =self ._fetch_image_src (filename )
        return {
        "filename":filename ,
        "image_src":image_src ,
        "image_page_url":f"https://en.wikipedia.org/wiki/{title }",
        "date":cur_date
        }
    def _fetch_image_src (self ,filename :str )->str :
        params ={
        "action":"query",
        "format":"json",
        "prop":"imageinfo",
        "iiprop":"url",
        "titles":filename
        }
        data =self ._make_request (params )
        try :
            page =next (iter (data ["query"]["pages"].values ()))
            return page ["imageinfo"][0 ]["url"]
        except (KeyError ,IndexError ,StopIteration )as e :
            logger .error (f"Failed to retrieve image URL for {filename }: {e }")
            raise RuntimeError ("Не удалось получить URL-адрес изображения.")
    def _make_request (self ,params :Dict [str ,Any ])->Dict [str ,Any ]:
        try :
            response =self .SESSION .get (self .API_URL ,params =params ,headers =self .HEADERS ,timeout =10 )
            response .raise_for_status ()
            return response .json ()
        except Exception as e :
            logger .error (f"Wikipedia API request failed with params {params }: {str (e )}")
            raise RuntimeError ("Запрос API Википедии не выполнен.")
    def _shrink_to_fit (self ,image :Image .Image ,max_width :int ,max_height :int )->Image .Image :
        orig_width ,orig_height =image .size
        if orig_width >max_width or orig_height >max_height :
            if orig_width >=orig_height :
                if orig_width >max_width :
                    new_width =max_width
                    new_height =int (orig_height *max_width /orig_width )
                else :
                    new_width ,new_height =orig_width ,orig_height
            else :
                if orig_height >max_height :
                    new_height =max_height
                    new_width =int (orig_width *max_height /orig_height )
                else :
                    new_width ,new_height =orig_width ,orig_height
            image =image .resize ((new_width ,new_height ),Image .LANCZOS )
            new_image =Image .new ("RGB",(max_width ,max_height ),(255 ,255 ,255 ))
            new_image .paste (image ,((max_width -new_width )//2 ,(max_height -new_height )//2 ))
            return new_image
        else :
            return image