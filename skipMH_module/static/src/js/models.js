odoo.define('skipMH_module.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    var pos_super = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (attributes, options) {
            pos_super.initialize.apply(this, arguments);
            console.log(self.partner);
            return this
        }
    });

    models.load_fields('res.company', ['street', 'city', 'state_id', 'zip']);
    models.load_fields('res.partner', ['identification_id','skipMH'])

    models.load_models([
        {
            model:  'identification.type',
            fields: ['name'],
            loaded: function(self,identifications){
                self.identifications = identifications;
            },
        }
    ])

});
