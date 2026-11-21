import logging
from inky .auto import auto
from display .abstract_display import AbstractDisplay
logger =logging .getLogger (__name__ )
class InkyDisplay (AbstractDisplay ):
    def initialize_display (self ):
        self .inky_display =auto ()
        self .inky_display .set_border (self .inky_display .BLACK )
        if not self .device_config .get_config ("resolution"):
            self .device_config .update_value (
            "resolution",
            [int (self .inky_display .width ),int (self .inky_display .height )],
            write =True )
    def display_image (self ,image ,image_settings =[]):
        logger .info ("Отображение изображения на чернильном дисплее.")
        if not image :
            raise ValueError (f"No image provided.")
        self .inky_display .set_image (image )
        self .inky_display .show ()