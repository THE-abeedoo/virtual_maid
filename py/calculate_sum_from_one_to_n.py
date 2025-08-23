def calculate_sum_from_one_to_n(n):
    if not isinstance(n, int) or n < 1:
        return '输入必须是大于等于1的整数。'
    return sum(range(1, n + 1))


def main(n):
    try:
        n = int(n)
        result = calculate_sum_from_one_to_n(n)
        if isinstance(result, str):
            return result
        return str(result)
    except ValueError:
        return '输入必须是有效的整数。'