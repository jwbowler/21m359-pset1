#core.py

import kivy
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.clock import Clock
import traceback


class BaseWidget(Widget):
   """Has some common core functionality we want in all
   our apps - handling key up/down, closing the app, and update on every frame.
   The subclass of BaseWidget can optionally define these methods, which will
   get called if defined:
      def on_key_down(self, keycode, modifiers):
      def on_key_up(self, keycode):
      def on_close(self):
      def on_update(self):
   """

   def __init__(self, **kwargs):
      super(BaseWidget, self).__init__(**kwargs)

      if hasattr(self.__class__, 'on_init'):
         Clock.schedule_once(self._init, 0)

      # keyboard up / down messages
      self.down_keys = []
      kb = Window.request_keyboard(target=self, callback=None)
      if hasattr(self.__class__, 'on_key_down'):
         kb.bind(on_key_down=self._key_down)
      if hasattr(self.__class__, 'on_key_up'):
         kb.bind(on_key_up=self._key_up)

      # get called when app is about to shut down
      if hasattr(self.__class__, 'on_close'):
         Window.bind(on_close=self._close)

      # create a clock to poll us every frame
      if hasattr(self.__class__, 'on_update'):
         Clock.schedule_interval(self._update, 0)

   def _key_down(self, keyboard, keycode, text, modifiers):
      if not keycode[1] in self.down_keys:
         self.down_keys.append(keycode[1])
      self.on_key_down(keycode, modifiers)

   def _key_up(self, keyboard, keycode):
      if keycode[1] in self.down_keys:
         self.down_keys.remove(keycode[1])
      self.on_key_up(keycode)

   def _close(self, *args):
      self.on_close()

   def _update(self, dt):
      self.on_update()

g_terminate_funcs = []

def register_terminate_func(f) :
   global g_terminate_funcs
   g_terminate_funcs.append(f)

def run(widget):
   """Pass in a widget, and this will automatically run it. Will also
   run termination functions (g_terminate_funcs) at the end of the run,
   even if it was caused by a program crash
   """

   class MainApp(App):
      def build(self):
         return widget()

   try:
      MainApp().run()
   except:
      traceback.print_exc()

   global g_terminate_funcs
   for t in g_terminate_funcs: 
      t()

