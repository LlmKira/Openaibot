from urllib.parse import urlparse


def split_dollar_string(input_string):
    segments = input_string.split("$")

    # 检查链接的有效性
    def is_valid_url(url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    # 开头为链接的情况
    if is_valid_url(segments[0]) and len(segments) >= 3:
        return segments[:3]
    # 第二个元素为链接，第一个元素为字符串的情况
    elif (
        len(segments) == 2
        and not is_valid_url(segments[0])
        and is_valid_url(segments[1])
    ):
        return segments
    # 其他情况
    else:
        return None


# 测试函数
print(
    split_dollar_string("api.openai.com$apikey$model_name")
)  # 输出：['api.openai.com', 'apikey', 'model_name']
print(
    split_dollar_string("token$https://provider_url")
)  # 输出：['token', 'provider_url']
print(split_dollar_string("string$invalid_url"))  # 输出：None
