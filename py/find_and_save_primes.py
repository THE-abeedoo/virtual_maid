import os
import csv

def find_and_save_primes(start, end, file_path):
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError('起始值和结束值必须为整数。')
    if start < 2 or end < start:
        raise ValueError('起始值必须大于等于2，且结束值必须大于等于起始值。')
    primes = []
    for num in range(start, end + 1):
        if num < 2:
            continue
        for i in range(2, int(num**0.5) + 1):
            if num % i == 0:
                break
        else:
            primes.append(num)
    try:
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['质数'])
            for prime in primes:
                writer.writerow([prime])
        return f'已成功将 {start} 到 {end} 范围内的质数保存到 {file_path}。'
    except Exception as e:
        return f'保存文件时出错：{e}'


def main(start, end, desktop_path):
    if not isinstance(start, int) or not isinstance(end, int) or not isinstance(desktop_path, str):
        return '参数格式错误，请输入两个整数和一个字符串。'
    file_path = os.path.join(desktop_path, 'primes.csv')
    return find_and_save_primes(start, end, file_path)