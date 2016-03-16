openerp.web_one2many_reconstruction = function(instance) {
    var QWeb = instance.web.qweb;

    instance.web.form.FieldOne2Many_Reconstruction = instance.web.form.AbstractField.extend({
        init: function(field_manager, node) {
            this._super.apply(this, arguments);

            this.columns = [];

            this.dataset = new instance.web.form.One2ManyDataSet(this, this.field.relation);
            this.dataset.o2m = this;
            this.dataset.parent_view = this.view;
            this.dataset.child_name = this.name;
            this.context = this.build_context().eval()

            this.on('change:effective_readonly', this, this.change_editable);
        },
        loading_views: function() {
            var self = this,
                view_loaded_def,
                tree_view = (self.field.views || {}).tree;

            if (_.isUndefined(tree_view)) {
                view_loaded_def = instance.web.fields_view_get({
                    'model': self.dataset._model,
                    'view_id': false,
                    'view_type': 'tree',
                    'toolbar': false,
                    'context': self.context,
                });
            } else {
                view_loaded_def = $.Deferred();
                $.when().then(function() {
                    view_loaded_def.resolve(tree_view);
                });
            };

            return this.alive(view_loaded_def).done(function(r) {
                self.loading_tree_view(r);
            });
        },

        loading_tree_view: function(data) {
            var self = this;
            self.fields_view = data,
            self.name = "" + self.fields_view.arch.attrs.string;

            self.setup_columns(self.fields_view.arch.children, self.fields_view.fields);
            // console.warn(QWeb.render('web_one2many_reconstruction.one2many', {columns: self.columns}));
            self.$el.html(QWeb.render('web_one2many_reconstruction.one2many', {columns: self.columns}))
            console.warn(self.$el);

            console.warn(self.columns);
        },

        setup_columns: function(children, fields) {
            var self = this,
                registry = instance.web.list.columns;

            this.columns.splice(0, this.columns.length - 1);
            this.columns = _.map(children, function(field) {
                var id = field.attrs.name;
                return registry.for_(id, fields[id], field);
            });

            this.visible_columns = _.filter(this.columns, function (column) {
                return column.invisible !== '1';
            });
        },

        change_editable: function() {
            var self = this,
                readonly = this.get('effective_readonly');

            console.warn('readonly', readonly);
        },

        render_value: function() {
            this.loading_views();
        },
    });

    instance.web.form.widgets = instance.web.form.widgets.extend({
        'one2many_reconstruction' : 'instance.web.form.FieldOne2Many_Reconstruction',
    });
};