> 此设计已经被完成，并过时。
>
>

## 函数注册管理器

组件注册关键词：`@register(keywords, **kwargs)`,检测到关键词后，注册函数和对应的message。

```python
class Exp:
    function
    keyword
    message
```

内部构建一个表用于回调。

检测到关键词，调用对应的组件函数，传入message，返回message然后回载。

    def register(self, target):
        def add_register_item(key, value):
            if not callable(value):
                raise Exception(f"register object must be callable! But receice:{value} is not callable!")
            if key in self._dict:
                print(f"warning: \033[33m{value.__name__} has been registered before, so we will overriden it\033[0m")
            self[key] = value
            return value

        if callable(target):            # 如果传入的目标可调用，说明之前没有给出注册名字，我们就以传入的函数或者类的名字作为注册名
            return add_register_item(target.__name__, target)
        else:                           # 如果不可调用，说明额外说明了注册的可调用对象的名字
            return lambda x : add_register_item(target, x)

```python
@resigner.register("search")
class Search(BaseModel):
    function: ...

    def func_message(self, message_text):
        """
        如果合格则返回message，否则返回None，表示不处理
        """
        if ...:
            return self.function
        else:
            return None

    async def __call__(self, *args, **kwargs):
        """
        处理message，返回message
        """
        return ...
```
