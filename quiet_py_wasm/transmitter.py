from .utils import *
import json 
import pyaudio

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
    
    def select_profile(self, profile, clampFrame):
        stack = self.instance.exports.stackSave()

        cProfiles = allocate_string_on_stack(self.instance, json.dumps({
            "profile": profile
        }))

        cProfile = allocate_string_on_stack(self.instance, 'profile')

        opt = self.instance.exports.quiet_encoder_profile_str(cProfiles, cProfile)

        self.encoder = self.instance.exports.quiet_encoder_create(opt, float(SAMPLE_RATE))

        self.instance.exports.free(opt)

        if clampFrame:
            self.frame_length = self.instance.exports.quiet_encoder_clamp_frame_len(self.encoder, sample_buffer_size)
        else:
            self.frame_length = self.instance.exports.quiet_encoder_clamp_frame_len(self.encoder)
        
        self.samples = malloc_array(sample_buffer_size, self.instance)

        self.instance.exports.stackRestore(stack)
        return self

    
    def transmit(self, buf):
        stack = self.instance.exports.stackSave()

        payload = chunks(buf, self.frame_length)

        buffer = self.instance.exports.memory.buffer

        for frame in payload:

            framePointer = allocate_array_on_stack(self.instance, frame)
            self.instance.exports.quiet_encoder_send(self.encoder, framePointer, len(frame))
            written = self.instance.exports.quiet_encoder_emit(self.encoder, self.samples["pointer"], sample_buffer_size)

            byte_buffer = bytearray(buffer)

            raw_bytes = byte_buffer[self.samples['pointer']: self.samples['end']]
            play_bytes(bytes(raw_bytes))           

        self.instance.exports.stackRestore(stack)
        return self
    
    def destroy(self):
        if (not self.destroyed):
            self.instance.exports.free(self.samples["pointer"])
            self.instance.exports.quiet_encoder_destroy(self.encoder)
            self.destroyed = True
        return self

def play_bytes(raw_bytes):
    data = raw_bytes
    stream.write(data)
