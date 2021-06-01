from .utils import *
import pyaudio


def chunks(arr, n):
    for i in range(0, len(arr), n):
        yield arr[i:i + n]


FORMAT = pyaudio.paFloat32
CHANNELS = 1
SAMPLE_RATE = 48000

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                output=True)


class Transmitter:
    def __init__(self, instance):
        self.destroyed = False
        self.instance = instance

    def select_profile(self, profile):
        stack = self.instance.exports.stackSave()
        cProfile, cProfiles = allocate_profile_on_stack(self.instance, profile)

        quiet_encoder_options = self.instance.exports.quiet_encoder_profile_str(
            cProfiles,
            cProfile
        )

        self.encoder = self.instance.exports.quiet_encoder_create(
            quiet_encoder_options,
            float(SAMPLE_RATE)
        )

        self.frame_length = self.instance.exports.quiet_encoder_clamp_frame_len(
            self.encoder,
            sample_buffer_size
        )

        self.instance.exports.free(quiet_encoder_options)
        self.instance.exports.stackRestore(stack)
        return self

    def transmit(self, buf):
        stack = self.instance.exports.stackSave()

        audioSampleBytesPointer, getAudioSampleBytes = allocate_array_on_stack(
            self.instance,
            [0] * sample_buffer_size * 4
        )

        payload = chunks(buf, self.frame_length)

        pre_loop_stack = self.instance.exports.stackSave()
        for frame in payload:

            unicodeBytesPointer, _ = allocate_array_on_stack(
                self.instance,
                frame
            )

            self.instance.exports.quiet_encoder_send(
                self.encoder,
                unicodeBytesPointer,
                len(frame)
            )

            self.instance.exports.quiet_encoder_emit(
                self.encoder,
                audioSampleBytesPointer,
                sample_buffer_size
            )

            play_bytes(bytes(getAudioSampleBytes()))
            self.instance.exports.stackRestore(pre_loop_stack)

        self.instance.exports.stackRestore(stack)
        return self

    def destroy(self):
        if (not self.destroyed):
            self.instance.exports.quiet_encoder_destroy(self.encoder)
            self.destroyed = True
        return self


def play_bytes(raw_bytes):
    data = raw_bytes
    stream.write(data)
