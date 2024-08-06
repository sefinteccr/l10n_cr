odoo.define('skipMH_module.screens', function (require) {
"use strict";

var core = require('web.core');
var screens = require('point_of_sale.screens');
var gui = require('point_of_sale.gui');


var skipMHScreenWidget = screens.ScreenWidget.extend({
    template: 'skipMHScreenWidget',

    click_skipMH: function(){
        debugger;
        var partner = this.partner.skipMH;
        order.set_to_invoice(!order.is_to_invoice());
        if (partner) {
            this.$('.js_skipMH').addClass('highlight');
        } else {
            this.$('.js_skipMH').removeClass('highlight');
        }
    },
    renderElement: function() {
        var self = this;
        this._super();
        this.$('skipMH').click(function(){
            debugger;
            self.click_skipMH();
        });
        this.$('allowcredit').click(function(){
            debugger;
            self.click_skipMH();
        });
    }
});
});