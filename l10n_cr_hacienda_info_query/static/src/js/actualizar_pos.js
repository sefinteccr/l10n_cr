odoo.define('l10n_cr_hacienda_info_query.pos', function (require) {
    "use strict";

    const models = require('point_of_sale.models');
    var screens = require("point_of_sale.screens");

    models.load_fields('res.partner', ['economic_activities_ids', 'activity_id']);

    models.load_models([{
        model: 'economic.activity',
        fields: [],
        domain: ['|', ['active', '=', false], ['active', '=', true]],
        loaded: function (self, activities) {
            self.economic_activities = activities;
        },
    }]);

    screens.PaymentScreenWidget.include({

        renderElement: function () {
            this._super.apply(this, arguments);

            const self = this;
            setTimeout(function () {
                self.customer_changed();
            }, 0);
        },

        customer_changed: function () {
            this._super.apply(this, arguments);

            const order = this.pos.get_order();
            const client = this.pos.get_client();
            const container = document.getElementById("economic_activity_container");
            const select = document.getElementById("economic_activity_select");

            if (!container || !select) {
                return;
            }

            if (client && client.economic_activities_ids && client.economic_activities_ids.length > 0) {
                container.style.display = "block";
                select.innerHTML = ""; 

                this.pos.economic_activities.forEach(activity => {
                    if (client.economic_activities_ids.includes(activity.id)) {
                        const option = document.createElement("option");
                        option.value = activity.id;
                        option.textContent = activity.code + '-' + activity.name;

                        if ((client.activity_id && client.activity_id[0] === activity.id) ||
                            (!client.activity_id && select.options.length === 0)) {
                            option.selected = true;
                            if (order) {
                                order.set_economic_activity_id(activity.id);
                            }
                        }
                        select.appendChild(option);
                    }
                });

                select.onchange = function (e) {
                    const selectedId = parseInt(e.target.value);
                    if (order) {
                        order.set_economic_activity_id(selectedId);
                    }
                };

            } else {
                container.style.display = "none";
                select.innerHTML = "";
                if (order) {
                    order.set_economic_activity_id(null);
                }
            }
        },
    });

});


function obtener_nombre(vat) {
    var end_point = window.location.origin + '/cedula/' + vat;
    httpGetClientData(end_point);
}

function httpGetClientData(theUrl) {
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            var obj = JSON.parse(xmlhttp.responseText);

            document.getElementsByName("name")[0].value = obj.nombre;
            document.getElementsByName("identification_id")[0].value = parseInt(obj.identification_id);
            document.getElementsByName("email")[0].value = obj.email;

            if (obj.actividades && Array.isArray(obj.actividades) && obj.actividades.length > 0) {
                document.getElementsByName("economic_activities_ids")[0].value = obj.actividades.map(activity => activity.id);

                let select = document.getElementById("economic_activity_select");
                if (select) {
                    select.innerHTML = "";
                    obj.actividades.forEach((activity, index) => {
                        const option = document.createElement("option");
                        option.value = activity.id;
                        option.textContent = activity.code + '-' + activity.descripcion;
                        if (index === 0) {
                            option.selected = true;
                        }
                        select.appendChild(option);
                    });
                }
            } else {
                let select = document.getElementById("economic_activity_select");
                if (select) {
                    select.innerHTML = "";
                    const option = document.createElement("option");
                    option.value = "";
                    option.textContent = "Sin actividades económicas registradas";
                    option.selected = true;
                    select.appendChild(option);
                }
                document.getElementsByName("economic_activities_ids")[0].value = "";
            }
        }
    };

    xmlhttp.open("GET", theUrl, true);
    xmlhttp.send();
}
function consultarActividadEconomica(vat) {
    var end_point = window.location.origin + '/economic_activities/' + vat;
    httpEconomicActivities(end_point);
}
function httpEconomicActivities(theUrl) {
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            var obj = JSON.parse(xmlhttp.responseText);
            if (obj.actividades && Array.isArray(obj.actividades) && obj.actividades.length > 0) {
                document.getElementsByName("economic_activities_ids")[0].value = obj.actividades.map(activity => activity.id);

                let select = document.getElementById("economic_activity_select");
                if (select) {
                    select.innerHTML = "";
                    obj.actividades.forEach((activity, index) => {
                        const option = document.createElement("option");
                        option.value = activity.id;
                        option.textContent = activity.code + '-' + activity.descripcion;
                        if (index === 0) {
                            option.selected = true;
                        }
                        select.appendChild(option);
                    });
                }
            } else {
                let select = document.getElementById("economic_activity_select");
                if (select) {
                    select.innerHTML = "";
                    const option = document.createElement("option");
                    option.value = "";
                    option.textContent = "Sin actividades económicas registradas";
                    option.selected = true;
                    select.appendChild(option);
                }
                document.getElementsByName("economic_activities_ids")[0].value = "";
            }
        }
    };

    xmlhttp.open("GET", theUrl, true);
    xmlhttp.send();
}

