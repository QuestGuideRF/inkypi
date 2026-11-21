import inspect
import importlib
import logging
import sys
from display .abstract_display import AbstractDisplay
from PIL import Image
from pathlib import Path
from plugins .plugin_registry import get_plugin_instance
logger =logging .getLogger (__name__ )
class WaveshareDisplay (AbstractDisplay ):
    def initialize_display (self ):
        logger .info ("Инициализация дисплея Waveshare")
        display_type =self .device_config .get_config ("display_type")
        logger .info (f"Loading EPD display for {display_type } display")
        if not display_type :
            raise ValueError ("Драйвер Waveshare, но «display_type» не указан в конфигурации.")
        module_name =f"display.waveshare_epd.{display_type }"
        epd_dir =Path (__file__ ).parent /"waveshare_epd"
        if str (epd_dir )not in sys .path :
            sys .path .insert (0 ,str (epd_dir ))
        try :
            epd_module =importlib .import_module (module_name )
            self .epd_display =epd_module .EPD ()
            self .epd_display_init =getattr (self .epd_display ,"Init",getattr (self .epd_display ,"init",None ))
            if not callable (self .epd_display_init ):
                raise AttributeError ("Не найден метод инициализации/инициализации")
            self .epd_display_init ()
            display_args_spec =inspect .getfullargspec (self .epd_display .display )
            display_args =display_args_spec .args
        except ModuleNotFoundError :
            raise ValueError (f"Unsupported Waveshare display type: {display_type }")
        except AttributeError :
            raise ValueError (f"Display does not support required methods: {display_type }")
        self .bi_color_display =len (display_args_spec .args )>2
        if not self .device_config .get_config ("resolution"):
            w ,h =int (self .epd_display .width ),int (self .epd_display .height )
            resolution =[w ,h ]if w >=h else [h ,w ]
            self .device_config .update_value (
            "resolution",
            resolution ,
            write =True )
    def display_image (self ,image ,image_settings =[]):
        logger .info ("Отображение изображения на дисплее Waveshare.")
        if not image :
            raise ValueError (f"No image provided.")
        self .epd_display_init ()
        self .epd_display .Clear ()
        if not self .bi_color_display :
            self .epd_display .display (self .epd_display .getbuffer (image ))
        else :
            color_image =Image .new ('1',image .size ,255 )
            self .epd_display .display (
            self .epd_display .getbuffer (image ),
            self .epd_display .getbuffer (color_image )
            )
        logger .info ("Перевод дисплея Waveshare в спящий режим для экономии энергии.")
        self .epd_display .sleep ()