import json

sample_buffer_size = 16384


def encode_string(string):
    return (string + "\0").encode("utf-8")


def allocate_array_on_stack(instance, arr):
    pointer = instance.exports.stackAlloc(len(arr))

    HEAP8 = instance.exports.memory.uint8_view(offset=pointer)

    for i, c in enumerate(arr):
        HEAP8[i] = c

    return pointer, lambda: HEAP8[0: len(arr)]


def allocate_profile_on_stack(instance, profile):
    cProfiles, _ = allocate_array_on_stack(
        instance,
        encode_string(
            json.dumps({
                "profile": profile
            })
        )
    )

    cProfile, _ = allocate_array_on_stack(
        instance,
        encode_string('profile')
    )

    return cProfile, cProfiles
