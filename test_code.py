# test_code.py - 测试用的代码文件
"""
这个文件中包含一些有潜在问题的代码，用于测试代码解释器    
"""

def calculate_average(numbers):
    """计算平均值"""
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)  # 潜在问题：numbers为空时会报错

def find_max(numbers):
    """找最大值"""
    max_num = numbers[0]  # 潜在问题：列表为空时会报错
    for num in numbers:
        if num > max_num:
            max_num = num
    return max_num

def is_palindrome(text):
    """检查是否是回文"""
    return text == text[::-1]  # 潜在问题：没有处理大小写和空格

class UserManager:
    """用户管理器"""
    
    def __init__(self):
        self.users = []
    
    def add_user(self, name, age):
        """添加用户"""
        user = {"name": name, "age": age}
        self.users.append(user)
        return user
    
    def get_user(self, name):
        """获取用户"""
        for user in self.users:
            if user["name"] == name:
                return user
        return None  # 找不到返回None
    
    def delete_user(self, name):
        """删除用户"""
        # 潜在问题：在遍历时修改列表
        for i in range(len(self.users)):
            if self.users[i]["name"] == name:
                del self.users[i]
                return True
        return False

def process_data(data):
    """处理数据"""
    # 潜在问题：没有类型检查
    result = []
    for item in data:
        result.append(item * 2)
    return result

if __name__ == "__main__":
    # 测试代码
    print(calculate_average([1, 2, 3, 4, 5]))
    print(find_max([10, 5, 20, 15]))
    print(is_palindrome("A man a plan a canal Panama"))
    
    manager = UserManager()
    manager.add_user("张三", 25)
    manager.add_user("李四", 30)
    print(manager.get_user("张三"))
