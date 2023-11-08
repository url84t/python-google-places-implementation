from googleplaces import GooglePlaces, types, lang
from geopy.geocoders import Nominatim
import datetime
import csv
import configparser
import sys

# Load the config file config.ini
config = configparser.ConfigParser()
config.read('config.ini')
config.sections()

API_KEY = config['DEFAULT']['API_KEY']
PAGES = int(config['GOOGLE_PLACES']['PAGES'])
QUERY = config['GOOGLE_PLACES']['QUERY']
LOCATION = str(config['GOOGLE_PLACES']['LOCATION'])

print(f"===== Your Configuration =====")
print(f"API_KEY: {API_KEY}")
print(f"PAGES: {PAGES}")
print(f"QUERY: {QUERY}")
print(f"LOCATION: {LOCATION}")

# Ask user input if user wants to continue
while True:
    print("Do you want to continue? This may incur charges on your GCP account. (y/n)")
    answer = input()
    if answer == 'y':
        break
    elif answer == 'n':
        print("Exiting...")
        exit()
    else:
        print("Invalid input. Please try again.")


def query_places(query, location, next_page_token=None):
    google_places = GooglePlaces(API_KEY)
    query_result = google_places.text_search(
        location=location, query=query, pagetoken=next_page_token)

    if query_result.has_attributions:
        print(query_result.html_attributions)

    query_places_result = {}
    places_list = []

    for query_place in query_result.places:
        # Returned places from a query are place summaries.
        print(query_place.name)
        print(query_place.geo_location)
        print(query_place.place_id)

        # The following method has to make a further API call.
        query_place.get_details()
        # Referencing any of the attributes below, prior to making a call to
        # get_details() will raise a googleplaces.GooglePlacesAttributeError.
        print(query_place.details)  # A dict matching the JSON response from Google.
        address_parts = extract_address_details(query_place.details['address_components'])
        print(query_place.local_phone_number)
        print(query_place.international_phone_number)
        print(query_place.website)
        print(query_place.url)

        # Store the data in a dictionary
        data = {
            'name': query_place.name,
            'geo_location': query_place.geo_location,
            'place_id': query_place.place_id,
            'address1': address_parts['address1'],
            'city': address_parts['city'],
            'state': address_parts['state'],
            'postal_code': address_parts['postal_code'],
            'formatted_address': query_place.formatted_address,
            'details': query_place.details,
            'local_phone_number': query_place.local_phone_number,
            'international_phone_number': query_place.international_phone_number,
            'website': query_place.website,
            'url': query_place.url,
            'rating': query_place.rating,
        }

        places_list.append(data)  # Returns a list of dictionaries

    if query_result.has_next_page_token:
        next_page = query_result.next_page_token
    else:
        next_page = None

    query_places_result['next_page_token'] = next_page
    query_places_result['places_list'] = places_list

    return query_places_result


def extract_address_details(address_components):
    """
    extract_address_details extracts address parts from the details of the google maps api response

    :param address_components: a dict representing the details['address_components'] response from the google maps api
    :return: a dict of the address components
    """

    # initialise subpremise
    subpremise = None

    # set up the loop parameters for each component
    count = len(address_components)
    looplist = range(0, count)

    #loop through the indices of the address components
    for i in looplist:

        #set up the loop parameters for the component types
        tcount = len(address_components[i]['types'])
        tlooplist = range(0, tcount)
        
        #loop through the indices of the address component types
        for t in tlooplist:

            #match the type, pull the short_name from the appropriate component as a string
            match address_components[i]['types'][t]:
                case "subpremise":
                    subpremise = str(address_components[i]['short_name'])
                case "street_number":
                    street_number = str(address_components[i]['short_name'])
                case "route":
                    route = str(address_components[i]['short_name'])
                case "locality":
                    city = str(address_components[i]['short_name'])
                case "administrative_area_level_1":
                    state = str(address_components[i]['short_name'])
                case "postal_code":
                    postal_code = str(address_components[i]['short_name'])

    #assemble the street address
    address1 = street_number + " " + route

    #add subpremise if it exists
    if subpremise:
        address1 += " " + subpremise

    #populate the return values
    data = {
        'address1': address1,
        'city': city,
        'state': state,
        'postal_code': postal_code
    }
    
    return data


result_list = []
page_number = 1
result_next_page = None

while page_number <= PAGES:
    try:
        result = query_places(next_page_token=result_next_page, query=QUERY, location=LOCATION)
        result_places_list = result['places_list']
        result_next_page = result['next_page_token']
        result_list.extend(result_places_list)
    except Exception as e:
        print(f"Error: Page {page_number} - {e}")
    page_number += 1

# Save JSON data to log file
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Save the data from places list to a CSV file
# filename = '{QUERY} in {LOCATION} ({PAGES} pages) {timestamp}.csv'

with open(f'{QUERY} in {LOCATION} ({PAGES} pages) {timestamp}.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(
        ['name', 'geo_location', 'place_id', 'address1', 'city', 'state', 'postal_code', 'formatted_address', 'details', 'local_phone_number', 'international_phone_number', 'website',
         'url', 'rating'])
    for place in result_list:
        writer.writerow(
            [place['name'], place['geo_location'], place['place_id'], place['address1'], place['city'], place['state'], place['postal_code'], place['formatted_address'], place['details'], place['local_phone_number'],
             place['international_phone_number'], place['website'], place['url'], place['rating']])
