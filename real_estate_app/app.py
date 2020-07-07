from real_estate_app import Map
from real_estate_app import config

from real_estate_model import ModelPipeline

from bokeh.io import curdoc
from bokeh.layouts import row
from bokeh.layouts import column

from bokeh.models.widgets.markups import Div
from bokeh.models import Select

import requests


class RealEstateApp:
    """An app used to display predictions of real estate data in Aarhus."""

    def __init__(self):
        """Initialize the app."""

        self.model = ModelPipeline.load()

        self.zipcodes = ['8000', '8200', '8210', '8230']

        self.selected_zipcode = None
        self.selected_road = None
        self.selected_address = None
        self.selected_prediction = None

        self.map = Map(
            latitude_min=config.AARHUS_LATITUDE_MIN,
            latitude_max=config.AARHUS_LATITUDE_MAX,
            longitude_min=config.AARHUS_LONGITUDE_MIN,
            longitude_max=config.AARHUS_LONGITUDE_MAX,
        )

        # Startup.
        self.layout = row(
            children=[],
            width=config.WIDTH,
        )
        self.map.refresh_plots()
        self.refresh_plots()

    def refresh_plots(self):
        """Main function used to create all plots."""
        zipcode = Select(
            title="Postnummer:",
            value=self.selected_zipcode,
            options=self.zipcodes,
        )
        zipcode.on_change(
            'value',
            self.zipcode_handler,
        )
        search = column(
            children=[zipcode]
        )
        if self.selected_zipcode is not None:
            road = Select(
                title="Vej:",
                value=self.selected_road,
                options=sorted(list(self.roads)),
            )
            road.on_change(
                'value',
                self.road_handler,
            )
            search.children.append(road)
            if self.selected_road is not None:

                address = Select(
                    title="Addresse:",
                    value=self.selected_address,
                    options=sorted(list(self.addresses)),
                )
                address.on_change(
                    'value',
                    self.address_handler,
                )
                search.children.append(address)
                if self.selected_prediction is not None:
                    formatted_price = (
                        f'{round(self.selected_prediction):,}'
                        .format(',', '.')
                    )
                    predicted_price = Div(
                        text=(
                            f"<p>Predicted price: {formatted_price} DKK</p>"
                        )
                    )
                    search.children.append(predicted_price)

        self.layout.children = [
            search,
            self.map.layout,
        ]

    def zipcode_handler(self, attr, old, new):
        self.selected_road = None
        self.selected_address = None
        self.selected_prediction = None
        self.selected_zipcode = new
        self.get_roads()
        self.refresh_plots()

    def road_handler(self, attr, old, new):
        self.selected_road = new
        self.selected_address = None
        self.selected_prediction = None
        self.get_addresses()
        self.refresh_plots()

    def address_handler(self, attr, old, new):
        self.selected_address = new
        self.selected_prediction = self.predict()
        print(self.selected_prediction)
        self.refresh_plots()

    def get_addresses(self):
        self.addresses_response = requests.get(
            'https://dawa.aws.dk/adresser',
            params={
                'navngivenvej_id': self.roads[self.selected_road]['id'],
            }
        ).json()
        self.addresses = dict(map(
            lambda response: (response['adressebetegnelse'], response),
            self.addresses_response,
        ))

        self.map.set_bbox(*self.roads[self.selected_road]['bbox'])
        self.map.set_address_source_data(self.addresses_response)
        self.map.refresh_plots()

    def get_roads(self):
        self.road_response = requests.get(
            'https://dawa.aws.dk/navngivneveje',
            params={
                'postnr': self.selected_zipcode,
            }
        ).json()
        self.roads = dict(map(
            lambda response: (response['navn'], response),
            self.road_response,
        ))

    def predict(self, addressid=None) -> float:
        if addressid is None:
            addressid = self.addresses[self.selected_address]['id']
            longitude, latitude = (
                self.addresses[self.selected_address]['adgangsadresse']['adgangspunkt']['koordinater']
            )

        bbr_response = requests.get(
            'https://dawa.aws.dk/bbrlight/enheder',
            params={
                'adresseid': addressid,
            }
        )
        if bbr_response.status_code == 200:
            bbr = bbr_response.json()[0]
            return float(self.model.predict({
                'rooms': bbr['VAERELSE_ANT'],
                'size': bbr['BEBO_ARL'],
                'build_year': bbr['BEBO_ARL'],
                'latitude':  latitude,
                'longitude': longitude,
            }))


planning_tool = RealEstateApp()
curdoc().add_root(planning_tool.layout)
curdoc().title = "Real Estate Model"
