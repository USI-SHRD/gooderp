openerp.web_editable_open_dialog = function(instance) {
    instance.web.ListView.include({
        start_edition: function(record, options) {
            var self = this,
                res = this._super.apply(this, arguments);

            console.log(self);
            return res.then(function() {
                _.each(self.columns, function(column) {
                    if (column.options && _.isString(column.options) && column.options.indexOf('set_one2many') != -1 && column.options.indexOf('open_dialog') != -1) {
                        var dialog = self.$el.find('.oe_form_container [data-fieldname=' + column.id + '] a.open_dialog');
                        if (dialog.length === 0) {
                            dialog = $("<a class='open_dialog'>...</a>").click(function(e) {
                                e.preventDefault();
                                var options = instance.web.py_eval(column.options || '{}'),
                                    notify = instance.web.notification,
                                    pop = new instance.web.form.FormOpenPopup(self);

                                console.warn('options', options);
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

                                new instance.web.Model('ir.model.data').call('get_object_reference', views).then(function(result) {
                                    console.log('result', result);
                                })

                                pop.show_element(
                                    'wh.move.line',
                                    false,
                                    self.dataset.get_context(),
                                    {
                                        title: '你好',
                                        view_id: 288,
                                        write_function: function(id, data, options) {
                                            console.warn('write_function', id, data, options);

                                            return $.Deferred();
                                        },
                                        create_function: function(data, options) {
                                            console.warn('create_function', data, options);
                                            return $.Deferred();
                                        }
                                    }
                                );

                                // pop.on('write_completed', self, function(){
                                //     console.warn('write_completed', this, self);
                                // });

                                // pop.on('create_completed', self, function() {
                                //     console.warn('create_completed', this, self);
                                // });


                            });

                            self.$el.find('.oe_form_container [data-fieldname=' + column.id + ']').append(dialog)
                        }

                    };
                })
            });
        }
    });
}