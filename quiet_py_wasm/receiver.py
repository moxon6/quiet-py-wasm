import pyaudio
from queue import Queue
from .utils import *

FORMAT = pyaudio.paFloat32
CHANNELS = 1
SAMPLE_RATE = 48000

p = pyaudio.PyAudio()


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

        q = Queue()

        def callback(in_data, frame_count, time_info, status):
            q.put(in_data)
            return (None, pyaudio.paContinue)

        p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=sample_buffer_size,
            stream_callback=callback
        )

        stack = self.instance.exports.stackSave()

        unicodeBytesPointer, getUnicodeBytes = allocate_array_on_stack(
            self.instance,
            [0] * sample_buffer_size
        )

        pre_loop_stack = self.instance.exports.stackSave()
        while True:
            try:
                frame = q.get()

                audioSampleBytesPointer, _ = allocate_array_on_stack(
                    self.instance,
                    frame
                )

                self.instance.exports.quiet_decoder_consume(
                    self.quiet_decoder, audioSampleBytesPointer, sample_buffer_size,
                )

                read = self.instance.exports.quiet_decoder_recv(
                    self.quiet_decoder, unicodeBytesPointer, sample_buffer_size
                )

                if (read != -1):
                    output = bytes(getUnicodeBytes()[:read]).decode(
                        "utf-8", 'ignore')
                    yield output

                self.instance.exports.stackRestore(pre_loop_stack)
            except KeyboardInterrupt:
                break
        self.instance.exports.stackRestore(stack)
