#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-12-27 07:22:21
# @Author  : Dahir Muhammad Dahir

from typing import List


def get_fullname(first_name: str, last_name: str):
    full_name = f"{first_name.title()} {last_name.title()}"
    return full_name


def process_items(items: List[str]):
    for item in items:
        print(item)
# print(get_fullname("dahir", "muhammad"))
