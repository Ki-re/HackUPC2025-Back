import requests
def ObtainFlights(market:str, locale:str, currency:str, airportDeparture:str, airportArrival:str, dateDeparture:str, dateArrival:str, adults:int) -> dict: 
    """
    Params
    ======
    (pongo ejemplos que da la API)
    market: mecado en el que se encuentra el cliente (e.g. UK)
    locale: no sé qué es, parece que es el idioma (e.g. en-GB)
    currency: moneda en la que se muestra la información (e.g. GBP)
    airportDeparture: código IASA del aeropuerto de salida (e.g. BCN)
    airportArrival: código IASA del aeropuerto de llegada (e.g. CDG)
    dateDeparture: día del vuelo de ida en formato YYYY-MM-DD (e.g. 2025-5-23)
    dateArrival: día del vuelo de vuelta en el mismo formato (se entiende que se hace comprobación previa de que dateArrival > dateDeparture)
    adults: cuántos adultos vuelan (1-8)

    Returns
    ======
    dictionary: se devuelve un diccionario con el siguiente formato 
    best:, cheapest:, fastest:, 
    donde cada uno tiene una lista con la siguiente información 
    ["precio itinerario", "hora de salida del vuelo 1", "duración del vuelo 1", "compañía aérea 1", "hora salida vuelo 2", "duración vuelo 2", "compañía aérea 2"]
    """

    API_key = "sh967490139224896692439644109194"
    url = "https://partners.api.skyscanner.net/apiservices/v3/flights/live/search/create"

    headers = {
        "x-api-key": API_key,
        "Content-Type": "application/json"
    }

    dateDepartureYear, dateDepartureMonth, dateDepartureDay = dateDeparture.split("-")
    dateArrivalYear, dateArrivalMonth, dateArrivalDay = dateArrival.split("-")

    # Esto se tiene que hacer porque no puede haber un 0 si la fecha del día o del mes es 
    # 01 o 05 y tiene que ser solo 1 o 5 ==> en caso de que hubiese un 01 o 05 me quedo con el útlimo número 
    # si solo hubiese un 0, entonces al hacer [-1] se seguiría quedando el 0
    if (dateDepartureDay[0] == "0"): dateDepartureDay = dateDepartureDay[-1]
    if (dateDepartureMonth[0] == "0"): dateDepartureMonth = dateDepartureMonth[-1]
    if (dateArrivalDay[0] == "0"): dateArrivalDay = dateArrivalDay[-1]
    if (dateArrivalMonth[0] == "0"): dateArrivalMonth = dateArrivalMonth[-1]

    data = {
    "query": {
        "market": market,
        "locale": locale,
        "currency": currency,
        "query_legs": [
            {
                "origin_place_id": {"iata": airportDeparture},
                "destination_place_id": {"iata": airportArrival},
                "date": {
                    "year": dateDepartureYear,
                    "month": dateDepartureMonth,
                    "day": dateDepartureDay
                }
            },
            {
               "origin_place_id": {"iata": airportArrival},
                "destination_place_id": {"iata": airportDeparture},
                "date": {
                    "year": dateArrivalYear,
                    "month": dateArrivalMonth,
                    "day": dateArrivalDay
                }
            },
        ],
        "adults": adults,
        "cabin_class": "CABIN_CLASS_ECONOMY"
        }
    }


    response = requests.post(url, headers=headers, json=data)
    print(response.status_code)
    response = response.json()
    
    # Así obtengo lo que SkyScanner considera que es el mejor, más barato y más rápido itinerario 
    itineraryBest = response["content"]["sortingOptions"]["best"][0]["itineraryId"]
    itineraryCheapest = response["content"]["sortingOptions"]["cheapest"][0]["itineraryId"]
    itineraryFastests = response["content"]["sortingOptions"]["fastest"][0]["itineraryId"]

    # Obtengo los precios respectivos 
    precioBest = response["content"]["results"]["itineraries"][itineraryBest]["pricingOptions"][0]["price"]["amount"]
    precioCheapest = response["content"]["results"]["itineraries"][itineraryCheapest]["pricingOptions"][0]["price"]["amount"]
    precioFastest = response["content"]["results"]["itineraries"][itineraryFastests]["pricingOptions"][0]["price"]["amount"]

    # Ahora hay que obtener los "legs", que son como los viajes individuales de cada itinerario (entiendo que ida y vuelta)
    leg1_intineraryBest = response["content"]["results"]["itineraries"][itineraryBest]["legIds"][0]
    leg2_intineraryBest = response["content"]["results"]["itineraries"][itineraryBest]["legIds"][1]
    leg1_intineraryCheapest = response["content"]["results"]["itineraries"][itineraryCheapest]["legIds"][0]
    leg2_intineraryCheapest = response["content"]["results"]["itineraries"][itineraryCheapest]["legIds"][1]
    leg1_intineraryFastest = response["content"]["results"]["itineraries"][itineraryFastests]["legIds"][0]
    leg2_intineraryFastest = response["content"]["results"]["itineraries"][itineraryFastests]["legIds"][1]

    # AHORA HAREMOS UN DICCIONARIO CON {best:, cheapest:, fastest:}, Y SEGUIRÁ  
    # ["precio itinerario", "hora de salida del vuelo 1", "duración del vuelo 1", "compañía aérea 1", "hora salida vuelo 2", "duración vuelo 2", "compañía aérea 2"]
    # CON HORA SALIDA VUELO EN FORMATO HH:MM 

    # Salidas de los aviones 
    salida_leg1_best = str(response["content"]["results"]["legs"][leg1_intineraryBest]["departureDateTime"]["hour"]) + ":" + str(response["content"]["results"]["legs"][leg1_intineraryBest]["departureDateTime"]["minute"])    
    salida_leg2_best = str(response["content"]["results"]["legs"][leg2_intineraryBest]["departureDateTime"]["hour"]) + ":" + str(response["content"]["results"]["legs"][leg2_intineraryBest]["departureDateTime"]["minute"])    
    salida_leg1_cheapest = str(response["content"]["results"]["legs"][leg1_intineraryCheapest]["departureDateTime"]["hour"]) + ":" + str(response["content"]["results"]["legs"][leg1_intineraryCheapest]["departureDateTime"]["minute"])    
    salida_leg2_cheapest = str(response["content"]["results"]["legs"][leg2_intineraryCheapest]["departureDateTime"]["hour"]) + ":" + str(response["content"]["results"]["legs"][leg2_intineraryCheapest]["departureDateTime"]["minute"])    
    salida_leg1_fastest = str(response["content"]["results"]["legs"][leg1_intineraryFastest]["departureDateTime"]["hour"]) + ":" + str(response["content"]["results"]["legs"][leg1_intineraryFastest]["departureDateTime"]["minute"])
    salida_leg2_fastest = str(response["content"]["results"]["legs"][leg2_intineraryFastest]["departureDateTime"]["hour"]) + ":" + str(response["content"]["results"]["legs"][leg2_intineraryFastest]["departureDateTime"]["minute"])

    # Duración vuelos 
    duracion_leg1_best = response["content"]["results"]["legs"][leg1_intineraryBest]["durationInMinutes"]
    duracion_leg2_best = response["content"]["results"]["legs"][leg2_intineraryBest]["durationInMinutes"]
    duracion_leg1_cheapest = response["content"]["results"]["legs"][leg1_intineraryCheapest]["durationInMinutes"]
    duracion_leg2_cheapest = response["content"]["results"]["legs"][leg2_intineraryCheapest]["durationInMinutes"]
    duracion_leg1_fastest = response["content"]["results"]["legs"][leg1_intineraryFastest]["durationInMinutes"]
    duracion_leg2_fastest = response["content"]["results"]["legs"][leg2_intineraryFastest]["durationInMinutes"]

    # Compañías aéreas 
    compania_leg1_best = response["content"]["results"]["carriers"][str(response["content"]["results"]["legs"][leg1_intineraryBest]["operatingCarrierIds"][0])]["name"]
    compania_leg2_best = response["content"]["results"]["carriers"][str(response["content"]["results"]["legs"][leg2_intineraryBest]["operatingCarrierIds"][0])]["name"]
    compania_leg1_cheapest = response["content"]["results"]["carriers"][str(response["content"]["results"]["legs"][leg1_intineraryCheapest]["operatingCarrierIds"][0])]["name"]
    compania_leg2_cheapest = response["content"]["results"]["carriers"][str(response["content"]["results"]["legs"][leg2_intineraryCheapest]["operatingCarrierIds"][0])]["name"]
    compania_leg1_fastest = response["content"]["results"]["carriers"][str(response["content"]["results"]["legs"][leg1_intineraryFastest]["operatingCarrierIds"][0])]["name"]
    compania_leg2_fastest = response["content"]["results"]["carriers"][str(response["content"]["results"]["legs"][leg2_intineraryFastest]["operatingCarrierIds"][0])]["name"]

    best = [int(precioBest)/1000, salida_leg1_best, duracion_leg1_best, compania_leg1_best, salida_leg2_best, duracion_leg2_best, compania_leg2_best]
    cheapest = [int(precioCheapest)/1000, salida_leg1_cheapest, duracion_leg1_cheapest, compania_leg1_cheapest, salida_leg2_cheapest, duracion_leg2_cheapest, compania_leg2_cheapest]
    fastest = [int(precioFastest)/1000, salida_leg1_fastest, duracion_leg1_fastest, compania_leg1_fastest, salida_leg2_fastest, duracion_leg2_fastest, compania_leg2_fastest]

    dictionary = {
        "best": best,
        "cheapest": cheapest, 
        "fastest": fastest
    }
    
    return dictionary