openerp.web_editable_list_length = function(instance) {
    instance.web.ListView.include({
        cancel_edition: function(ids) {
            var options_length = this.get_options_length();
            if (options_length) {
                if (this.records.length - 1 < options_length) {
                    this.show_add_button('fast');
                };
            };

            console.warn('length', this.records.length);

            return this._super.apply(this, arguments);
        },
        do_delete: function(ids) {
            var options_length = this.get_options_length();
            if (options_length) {
                if (this.records.length - 1 < options_length) {
                    this.show_add_button('fast');
                };
            };

            return this._super.apply(this, arguments);
        },
        start_edition: function(record, options){
            var self = this,
                res = this._super.apply(this, arguments);

            return res.then(function() {
                var options_length = self.get_options_length();
                if (options_length) {
                    if (self.records.length >= options_length) {
                        self.hide_add_button('fast');
                    };
                };
            });
        },
        get_options_length: function() {
            if (this.ViewManager && this.ViewManager.ActionManager) {
                var actionManager = this.ViewManager.ActionManager,
                    options = actionManager.options;

                if (!_.isUndefined(options) && !_.isUndefined(options.list_length)) {
                    return options.list_length;
                }
            }
            return false
        },
        show_add_button: function() {
            this.$el.find('.oe_form_field_one2many_list_row_add').show();
        },
        hide_add_button: function() {
            this.$el.find('.oe_form_field_one2many_list_row_add').hide();
        },
    });

    instance.web.ListView.List.include({
        pad_table_to: function(count) {
            this._super.apply(this, arguments);

            var self = this;
            setTimeout(function() {
                var options_length = self.view.get_options_length();
                if (options_length && self.records.length >= options_length) {
                    self.view.hide_add_button('fast');
                }
            })
        },
    });
};
