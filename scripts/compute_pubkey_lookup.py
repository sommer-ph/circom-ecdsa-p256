import math
from compute_p256_math import double, add, get_long

# Fixed public key coordinates from generated key
QX = 66432692286261411630769223098970693805397596870633670159153355502222145619968
QY = 63182586149833488067701290985084360701345487374231728189741684364091950142361


def get_pows(x, y, exp):
    pows = []
    cx, cy = x, y
    for _ in range(exp):
        pows.append((cx, cy))
        cx, cy = double(cx, cy)
    return pows


def get_pow_val(pows, exp):
    bits = []
    while exp > 0:
        bits.append(exp % 2)
        exp //= 2
    is_nonzero = False
    curr = None
    for idx, b in enumerate(bits):
        if b:
            if not is_nonzero:
                is_nonzero = True
                curr = pows[idx]
            else:
                curr = add(curr[0], curr[1], pows[idx][0], pows[idx][1])
    return curr


def get_table_str(n, k, stride):
    num_strides = math.ceil(n * k / stride)
    ret = f"function get_q_pow_stride{stride}_table(n, k) {{\n"
    ret += f"    assert(n == {n} && k == {k});\n"
    ret += f"    var powers[{num_strides}][{2**stride}][2][{k}];\n"
    EXP = 256 + stride
    pows = get_pows(QX, QY, EXP)
    for s in range(num_strides):
        for idx in range(2 ** stride):
            exp = idx * (2 ** (s * stride))
            if exp > 0:
                px, py = get_pow_val(pows, exp)
                lx = get_long(n, k, px)
                ly = get_long(n, k, py)
                for r in range(k):
                    ret += f"    powers[{s}][{idx}][0][{r}] = {lx[r]};\n"
                for r in range(k):
                    ret += f"    powers[{s}][{idx}][1][{r}] = {ly[r]};\n"
            else:
                for r in range(k):
                    ret += f"    powers[{s}][{idx}][0][{r}] = 0;\n"
                for r in range(k):
                    ret += f"    powers[{s}][{idx}][1][{r}] = 0;\n"
    ret += "    return powers;\n}"
    return ret


def get_dummy_str(n, k):
    x, y = QX, QY
    for _ in range(255):
        x, y = double(x, y)
    lx = get_long(n, k, x)
    ly = get_long(n, k, y)
    ret = "function get_q_dummy_point(n, k) {\n"
    ret += f"    assert(n == {n} && k == {k});\n"
    ret += "    var ret[2][100];\n"
    for r in range(k):
        ret += f"    ret[0][{r}] = {lx[r]};\n"
    for r in range(k):
        ret += f"    ret[1][{r}] = {ly[r]};\n"
    ret += "    return ret;\n}"
    return ret


if __name__ == "__main__":
    n = 43
    k = 6
    stride = 8
    out = "pragma circom 2.1.5;\n\n"
    out += get_table_str(n, k, stride) + "\n\n" + get_dummy_str(n, k) + "\n"
    with open('../circuits/public_key_lookup.circom', 'w') as f:
        f.write(out)
