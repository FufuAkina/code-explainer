def calculate_average(numbers):
    """计算平均值"""
    total = sum(numbers)
    return total / len(numbers)

result = calculate_average([1, 2, 3, 4, 5])
print(f"平均值: {result}")
