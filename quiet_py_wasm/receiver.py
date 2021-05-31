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

        cProfiles = allocate_string_on_stack(self.instance, json.dumps({
            "profile": profile
        }))

        cProfile = allocate_string_on_stack(self.instance, 'profile')

        quiet_decoder_options = self.instance.exports.quiet_decoder_profile_str(
            cProfiles, cProfile)
        self.decoder = self.instance.exports.quiet_decoder_create(
            quiet_decoder_options, float(SAMPLE_RATE))
        self.instance.exports.free(quiet_decoder_options)

        self.instance.exports.stackRestore(stack)
        return self

    def receive(self):
        while True:
            loop_stack = self.instance.exports.stackSave()
            samples = stream.read(sample_buffer_size)

            sammplesPointer, _ = allocate_array_on_stack_v2(
                self.instance,
                samples
            )

            outputBytesPointer, getOutputBytes = allocate_array_on_stack_v2(
                self.instance,
                [0] * sample_buffer_size
            )

            self.instance.exports.quiet_decoder_consume(
                self.decoder, sammplesPointer, sample_buffer_size,
            )

            read = self.instance.exports.quiet_decoder_recv(
                self.decoder, outputBytesPointer, sample_buffer_size
            )

            if (read != -1):
                output = bytes(getOutputBytes()).decode("utf-8")
                print(output)

            self.instance.exports.stackRestore(loop_stack)
