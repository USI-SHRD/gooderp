# -*- coding: utf-8 -*-
import functools


def safe_division(divisor, dividend):
    return dividend != 0 and divisor / dividend or 0


def create_name(method):
    @functools.wraps(method)
    def func(self, vals):
        if vals.get('name', '/') == '/':
            vals.update({'name': self.env['ir.sequence'].get(self._name) or '/'})

        return method(self, vals)

    return func


def inherits_after(res_back=True, collect_before_res=False):
    def wrapper(method):
        @functools.wraps(method)
        def func(self, *args, **kwargs):

            res_before = execute_inherits_func(self, method.func_name, args, kwargs)

            # if collect_before_res:
            #     if not kwargs.get('context'):
            #         kwargs['context'] = {}

            #     kwargs.get('context').update({'res_before': res_before})

            res_after = method(self, *args, **kwargs)

            if res_back:
                return res_after
            else:
                return res_before

        return func
    return wrapper


def inherits(res_back=True):
    def wrapper(method):
        @functools.wraps(method)
        def func(self, *args, **kwargs):

            res_after = method(self, *args, **kwargs)
            res_before = execute_inherits_func(self, method.func_name, args, kwargs)

            if res_back:
                return res_after
            else:
                return res_before

        return func
    return wrapper


def execute_inherits_func(self, method_name, args, kwargs):
    if self._inherits and len(self._inherits) != 1:
        raise ValueError(u'错误，当前对象不存在多重继承，或者存在多个多重继承')

    model, field = self._inherits.items()[0]
    values = self.read([field])
    field_ids = map(lambda value: value[field][0], values)

    models = self.env[model].browse(field_ids)
    return getattr(models, method_name)(*args, **kwargs)
