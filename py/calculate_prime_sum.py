def calculate_prime_sum(upper_bound):
    if not isinstance(upper_bound, int) or upper_bound < 0:
        raise ValueError("输入必须是一个非负整数")
    is_prime = [True] * (upper_bound + 1)
    is_prime[0] = is_prime[1] = False
    p = 2
    while p * p <= upper_bound:
        if is_prime[p]:
            for i in range(p * p, upper_bound + 1, p):
                is_prime[i] = False
        p += 1
    prime_sum = 0
    for i in range(upper_bound + 1):
        if is_prime[i]:
            prime_sum += i
    return prime_sum

def main(upper_bound):
    try:
        upper_bound = int(upper_bound)
        result = calculate_prime_sum(upper_bound)
        return str(result)
    except ValueError as e:
        return str(e)
