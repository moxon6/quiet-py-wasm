import pyaudio
import json
from .utils import *

FORMAT = pyaudio.paFloat32
CHANNELS = 1
SAMPLE_RATE = 48000

p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    input=True,
    frames_per_buffer=sample_buffer_size
)


class Receiver:
    def __init__(self, instance):
        self.destroyed = False
        self.instance = instance

    def select_profile(self, profile):
        stack = self.instance.exports.stackSave()
        cProfile, cProfiles = allocate_profile_on_stack(self.instance, profile)

        quiet_decoder_options = self.instance.exports.quiet_decoder_profile_str(
            cProfiles,
            cProfile
        )

        self.quiet_decoder = self.instance.exports.quiet_decoder_create(
            quiet_decoder_options,
            float(SAMPLE_RATE)
        )

        self.instance.exports.free(quiet_decoder_options)
        self.instance.exports.stackRestore(stack)
        return self

    def receive(self):

        unicodeBytesPointer, getUnicodeBytes = allocate_array_on_stack(
            self.instance,
            [0] * sample_buffer_size
        )

        while True:
            stack = self.instance.exports.stackSave()

            audioSampleBytesPointer, _ = allocate_array_on_stack(
                self.instance,
                stream.read(sample_buffer_size)
            )

            self.instance.exports.quiet_decoder_consume(
                self.quiet_decoder, audioSampleBytesPointer, sample_buffer_size,
            )

            read = self.instance.exports.quiet_decoder_recv(
                self.quiet_decoder, unicodeBytesPointer, sample_buffer_size
            )

            if (read != -1):
                output = bytes(getUnicodeBytes()).decode("utf-8")
                print(output)

            self.instance.exports.stackRestore(stack)
