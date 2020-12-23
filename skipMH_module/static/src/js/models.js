odoo.define('skipMH_module.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    models.load_fields('res.company', ['street', 'city', 'state_id', 'zip']);
    models.load_fields('res.partner', ['identification_id','skipMH'])

    models.load_models([
        {
            model:  'identification.type',
            fields: ['name'],
            loaded: function(self,identifications){
                console.log(identifications)
                self.identifications = identifications;
            },
        }
    ])

});
