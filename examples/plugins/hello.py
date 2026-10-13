"""Example plugin. Copy to ~/.mudra/plugins/hello.py"""
import datetime


def register(api):
    @api.on_voice("what time is it")
    def _time():
        api.say(datetime.datetime.now().strftime("It is %I %M %p"))

    @api.on_gesture("fist")
    def _fist():
        print("fist detected - control paused")
