openerp.web_editable_open_dialog = function(instance) {
    instance.web.ListView.include({
        start_edition: function(record, options) {
            var self = this,
                res = this._super.apply(this, arguments);

            return res.then(function() {
                _.each(self.columns, function(column) {
                    if (column.options && _.isString(column.options) && column.options.indexOf('open_dialog') != -1) {
                        if (column.options.indexOf('set_one2many_readonly') != -1) {
                            var $td = self.$el.find('.oe_form_container [data-fieldname=' + column.id + ']');
                            $td.addClass('readonly_open_dialog');
                            $td.click(function(e) {
                                e.preventDefault();
                                e.stopPropagation();
                                self.do_open_one2many_popup(instance.web.py_eval(column.options || '{}'));
                            });
                        } else if (column.options.indexOf('set_one2many') != -1) {
                            var dialog = self.$el.find('.oe_form_container [data-fieldname=' + column.id + '] a.open_dialog');
                            if (dialog.length === 0) {
                                dialog = $("<a class='open_dialog'>...</a>").click(function(e) {
                                    e.preventDefault();
                                    self.do_open_one2many_popup(instance.web.py_eval(column.options || '{}'));
                                });

                                self.$el.find('.oe_form_container [data-fieldname=' + column.id + ']').append(dialog)
                            };
                        } 
                    };
                })
            });
        },
        do_open_one2many_popup: function(options) {
            var self = this,
                field_column = false,
                notify = instance.web.notification,
                pop = new instance.web.form.FormOpenPopup(self);

            if (_.isUndefined(options.open_dialog.field)) {
                field_column = column;
            } else {
                field_column = _.find(self.columns, function(column) { return column.id === options.open_dialog.field});
            }

            if (_.isUndefined(field_column)) {
                return notify.warn('错误', options.open_dialog.field + '字段需要在视图中定义');
            }

            if (_.isUndefined(options.open_dialog.view_id)) {
                return notify.warn('错误', 'options中需要定义view_id来指定具体的视图');
            }

            var views = options.open_dialog.view_id.split('.');
            if (views.length != 2) {
                return notify.warn('错误', 'options中定义的视图id需要指定具体的模块名称');
            }

            var field = self.editor.form.fields[field_column.id],
                history_value = field.get_value();

            new instance.web.Model('ir.model.data').call('get_object_reference', views).then(function(view_id) {
                pop.show_element(
                    self.model,
                    false,
                    self.dataset.get_context(),
                    {
                        view_id: view_id[1],
                        create_function: function(data) {
                            console.warn('pop', data, options, pop);
                            console.warn(options.open_dialog.compute_field);
                            if (!_.isUndefined(options.open_dialog.compute_field)) {
                                var compute_field = options.open_dialog.compute_field,
                                    $compute_field = pop.$el.find('td.oe_list_footer[data-field=' + compute_field + ']'),
                                    compute_result = parseFloat($compute_field.text());

                                if (_.isNaN(compute_field)) {
                                    notify.warn('错误', '需要统计计算的字段没有统计数据或者无法被合计');
                                } else {
                                    self.editor.form.fields[compute_field].set_value(compute_result);
                                };
                            };
                            field.set_value(history_value.concat(data[field_column.id]));
                            pop.check_exit();
                            return $.Deferred();
                        }
                    }
                );

                var set_pop_value = function() {
                    try {
                        pop.view_form.fields.lot_id.set_value(history_value);
                    } catch(e) {
                        setTimeout(set_pop_value, 100);
                    }
                };

                // TODO 使用setTimeout的方式来等待pop加载完毕，不是很好的方法，需要找到一个更好的方法
                setTimeout(set_pop_value, 100);
            });
        },
    });
}