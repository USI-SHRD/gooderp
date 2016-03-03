# -*- coding: utf-8 -*-
import functools


def safe_division(divisor, dividend):
    return dividend != 0 and divisor / dividend or 0


def create_name(method):
    @functools.wraps(method)
    def func(self, cr, uid, vals, context=None):
        if vals.get('name', '/') == '/':
            vals.update({'name': self.pool.get('ir.sequence').get(
                cr, uid, self._name, context=context) or '/'})

        return method(self, cr, uid, vals, context=context)

    return func


def inherits_after(res_back=True, collect_before_res=False):
    def wrapper(method):
        @functools.wraps(method)
        def func(self, cr, uid, ids, *args, **kwargs):
            if isinstance(ids, (long, int)):
                ids = [ids]

            res_before = execute_inherits_func(self, cr, uid, ids, method.func_name, args, kwargs)

            if collect_before_res:
                if not kwargs.get('context'):
                    kwargs['context'] = {}

                kwargs.get('context').update({'res_before': res_before})

            res_after = method(self, cr, uid, ids, *args, **kwargs)

            if res_back:
                return res_after
            else:
                return res_before

        return func
    return wrapper


def inherits(res_back=True):
    def wrapper(method):
        @functools.wraps(method)
        def func(self, cr, uid, ids, *args, **kwargs):
            if isinstance(ids, (long, int)):
                ids = [ids]

            res_after = method(self, cr, uid, ids, *args, **kwargs)
            res_before = execute_inherits_func(self, cr, uid, ids, method.func_name, args, kwargs)

            if res_back:
                return res_after
            else:
                return res_before

        return func
    return wrapper


def execute_inherits_func(self, cr, uid, ids, method_name, args, kwargs):
    if self._inherits and len(self._inherits) != 1:
        raise ValueError(u'错误，当前对象不存在多重继承，或者存在多个多重继承')

    model, field = self._inherits.items()[0]
    values = self.read(cr, uid, ids, [field], context=kwargs.get('context', {}))
    field_ids = map(lambda value: value[field][0], values)

    return getattr(self.pool.get(model), method_name)(cr, uid, field_ids, *args, **kwargs)
