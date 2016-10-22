import struct
import numpy as np


def prepare_lists(nums):
    try:
        len(nums)
    except TypeError:
        nums = [nums]
    return nums


class SimpleNine:
    def __init__(self):
        self.pack_lens = [28, 14, 9, 7, 5, 4, 3, 2, 1]
        self.pack_size = [int(28 / l) for l in self.pack_lens]
        self.pack_free = [28 % l for l in self.pack_lens]
        self.pack_code = range(len(self.pack_lens))

    @staticmethod
    def __bits_len(x):
        for i in range(1, 29):
            if x >> i == 0:
                return i
        raise NameError("Simple9: number is too big!")

    def __encode_numbers(self, nums, code):
        nums = prepare_lists(nums)

        res = code << self.pack_free[code]
        for n in nums:
            res = (res << self.pack_lens[code]) | n
        return res

    def encode(self, numbers):
        numbers = prepare_lists(numbers)

        numbers_len = map(SimpleNine.__bits_len, numbers)

        i, packs = 0, []
        while i < len(numbers):
            for code in reversed(self.pack_code):
                if i + self.pack_size[code] > len(numbers):
                    continue

                pack_lens = numbers_len[i: i + self.pack_size[code]]
                if sum(pack_lens) + self.pack_free[code] <= 28 and max(pack_lens) <= self.pack_lens[code]:
                    packs.append(self.__encode_numbers(numbers[i: i + self.pack_size[code]], code))
                    i += self.pack_size[code]
                    break

        packs = np.asarray([struct.unpack("4B", struct.pack("I", pack)) for pack in packs]).reshape(-1)
        return bytearray(list(packs))

    def __decode_numbers(self, nums):
        code = nums >> 28
        mask = 2 ** self.pack_lens[code] - 1

        numbers = []
        for i in range(self.pack_size[code]):
            numbers.append(nums & mask)
            nums >>= self.pack_lens[code]

        return numbers[-1::-1]

    def decode(self, encoded_numbers):
        encoded_numbers = [struct.unpack("I", encoded_numbers[i: i + 4])[0] for i in range(0, len(encoded_numbers), 4)]
        numbers = [self.__decode_numbers(nums) for nums in encoded_numbers]
        return reduce(lambda x, y: x + y, numbers)


class Varbyte:
    def __init__(self):
        pass

    @staticmethod
    def __encode_number(x):
        binary_number = []
        while True:
            binary_number.append(x & 0x7f)
            x >>= 7
            if x == 0:
                break

        binary_number[0] |= 0x80
        binary_number.reverse()
        return binary_number

    def encode(self, numbers):
        numbers = prepare_lists(numbers)

        encoded_numbers = map(Varbyte.__encode_number, numbers)
        return bytearray(reduce(lambda x, y: x + y, encoded_numbers))

    def decode(self, encoded_numbers):
        numbers, number = [], []

        for n in encoded_numbers:
            number.append(n & 0x7f)
            if n & 0x80:
                numbers.append(number)
                number = []
        return [reduce(lambda x, y: 0x80 * x + y, n) for n in numbers]


def encode(seq_to_encode, encoding='varbyte'):
    # See notes about realisation in index.py
    encoder = {
        'varbyte': Varbyte(),
        'simple9': SimpleNine()
    }[encoding]

    # seq = [seq_to_encode[0]]
    # seq += [x - y for x, y in zip(seq_to_encode[1:], seq_to_encode)]
    # return encoder.encode(seq)

    seq = [x - y for x, y in zip(seq_to_encode[1:], seq_to_encode)]
    return encoder.encode(seq)


def decode(seq_to_decode, encoding='varbyte'):
    encoder = {
        'varbyte': Varbyte(),
        'simple9': SimpleNine()
    }[encoding]

    return np.cumsum(encoder.decode(seq_to_decode))


if __name__ == '__main__':
    method = SimpleNine()
    numbers = np.array([2, 4, 15, 191])

    numbers_encoded = method.encode(numbers)
    numbers_decoded = method.decode(numbers_encoded)

    print "numbers:", numbers
    if len(numbers_decoded) > 1:
        print "result:", numbers_decoded == numbers
    else:
        print "result:", numbers_decoded[0] == numbers

    if len(numbers_decoded) > 1:
        print "result:", decode(encode(numbers)) == numbers
