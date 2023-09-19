# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 上午12:26
# @Author  : sudoskys
# @File    : test_funtion.py
# @Software: PyCharm
import json
from typing import Optional, Literal

from pydantic import BaseModel


class Function(BaseModel):
    class Parameters(BaseModel):
        type: str = "object"
        properties: dict = {}

    name: str
    description: Optional[str] = None
    parameters: Parameters = Parameters(type="object")
    required: list[str]

    def add_property(self, property_name: str,
                     property_type: Literal["string", "integer", "number", "boolean", "object"],
                     property_description: str,
                     enum: Optional[tuple] = None,
                     required: bool = False
                     ):
        self.parameters.properties[property_name] = {}
        self.parameters.properties[property_name]['type'] = property_type
        self.parameters.properties[property_name]['description'] = property_description
        if enum:
            self.parameters.properties[property_name]['enum'] = tuple(enum)
        if required:
            self.required.append(property_name)


if __name__ == '__main__':
    f = Function(name="call", description="make a call", required=[])
    f.add_property(
        property_name="user_name",
        property_type="string",
        property_description="user name for calling",
        enum=("Li", "Susi"),
        required=True
    )
    print(json.dumps(f.dict(), indent=4))
