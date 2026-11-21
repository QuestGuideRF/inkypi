class AbstractDisplay :
    def __init__ (self ,device_config ):
        self .device_config =device_config
        self .initialize_display ()
    def initialize_display (self ):
        raise NotImplementedError ("Метод 'initialize_display(...) должен быть предоставлен в подклассе.")
    def display_image (self ,image ,image_settings =[]):
        raise NotImplementedError ("Метод display_image(...) должен быть предоставлен в подклассе.")