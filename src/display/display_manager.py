import fnmatch
import json
import logging
from utils .image_utils import resize_image ,change_orientation ,apply_image_enhancement
from display .mock_display import MockDisplay
logger =logging .getLogger (__name__ )
try :
    from display .inky_display import InkyDisplay
except ImportError :
    logger .info ("Чернильный дисплей недоступен, аппаратная поддержка отключена")
try :
    from display .waveshare_display import WaveshareDisplay
except ImportError :
    logger .info ("Отображение Waveshare недоступно, аппаратная поддержка отключена")
class DisplayManager :
    def __init__ (self ,device_config ):
        self .device_config =device_config
        display_type =device_config .get_config ("display_type",default ="inky")
        if display_type =="mock":
            self .display =MockDisplay (device_config )
        elif display_type =="inky":
            self .display =InkyDisplay (device_config )
        elif fnmatch .fnmatch (display_type ,"ЭПД*в*"):
            self .display =WaveshareDisplay (device_config )
        else :
            raise ValueError (f"Unsupported display type: {display_type }")
    def display_image (self ,image ,image_settings =[]):
        if not hasattr (self ,"display"):
            raise ValueError ("Не инициализирован действительный экземпляр дисплея.")
        logger .info (f"Saving image to {self .device_config .current_image_file }")
        image .save (self .device_config .current_image_file )
        image =change_orientation (image ,self .device_config .get_config ("orientation"))
        image =resize_image (image ,self .device_config .get_resolution (),image_settings )
        if self .device_config .get_config ("inverted_image"):image =image .rotate (180 )
        image =apply_image_enhancement (image ,self .device_config .get_config ("image_settings"))
        self .display .display_image (image ,image_settings )