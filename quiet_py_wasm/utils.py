from wasmer import Store, Module, Instance

sample_buffer_size = 16384


def chunks(arr, n):
    for i in range(0, len(arr), n):
        yield arr[i:i + n]


def encode(string):
    return [int(x) for x in (string).encode("utf-8")]


def allocate_array_on_stack(instance, arr):
    ret = instance.exports.stackAlloc(len(arr))

    HEAP8 = instance.exports.memory.uint8_view(offset=ret)

    for i, c in enumerate(arr):
        HEAP8[i] = c
    return ret


def allocate_array_on_stack_v2(instance, arr):
    pointer = instance.exports.stackAlloc(len(arr))

    HEAP8 = instance.exports.memory.uint8_view(offset=pointer)

    for i, c in enumerate(arr):
        HEAP8[i] = c

    def get_values_uint8():
        return HEAP8[0: len(arr)]

    return pointer, get_values_uint8


def allocate_string_on_stack(instance, string):
    return allocate_array_on_stack(instance, encode(string + "\0"))


def malloc_array(bufferSize, instance):
    pointer = instance.exports.malloc(4 * bufferSize)
    return {
        "pointer": pointer,
        "end": pointer + 4 * bufferSize,
    }
