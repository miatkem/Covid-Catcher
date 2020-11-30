import requests
import os
import flask
from flask import request
from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), "api-keys.env")
load_dotenv(dotenv_path)

def get_sites(lat,lng):
    url = ('https://discover.search.hereapi.com/v1/discover?apikey='+os.environ['SITE_API_KEY']+'&q=COVID&at='+str(lat)+','+str(lng)+'&limit=3')
    response=requests.get(url)
    data = response.json()
    sites = []
    for x in data['items']:
        title = x['title']
        address = x['address']
        position = x['position']
        if 'houseNumber' not in address.keys():
            address['houseNumber'] = ''
        if 'street' not in address.keys():
            address['street'] = ''
        if 'city' not in address.keys():
            address['city'] = ''
        if 'state' not in address.keys():
            address['state'] = ''
        if 'postalCode' not in address.keys():
            address['postalCode'] = ''
        entireAddress = address['houseNumber']+" "+address['street']+", "+address['city']+", "+address['state']+" "+address['postalCode']
        latitude = position['lat']
        longitude = position['lng']
        if 'contacts' not in x.keys():
            phone = ''
            web = ''
        else:
            for i in x['contacts']:
                phone = i['phone'][0]['value']
                web = i['www'][0]['value']
        if 'distance' not in x.keys():
            meter = 0
        meter = x['distance']
        miles = meter*0.00062137119224
        miles = str(miles)[0:4]
        sites.append(TestingSites(title,entireAddress,latitude,longitude,phone,web,miles))
    return sites
class TestingSites:
    """Testing Site Information"""
    def __init__(self,title,entireAddress,latitude,longitude,phone,web,miles):
        self.title=title
        self.entireAddress=entireAddress
        self.latitude=latitude
        self.longitude=longitude
        self.phone=phone
        self.web=web
        self.miles=miles