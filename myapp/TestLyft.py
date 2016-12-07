from flask import render_template, redirect, request, flash, url_for, json, make_response
from flask_mail import Message
from flask_googlemaps import Map, icons
from google_api import *
from forms import *
from myapp import app, mail, db
from decimal import Decimal

def Lyft():
    jsonarray = {}
    dictstart = {}
    dictend = {}
    finalpath = {}
    count = 0
    Query = Location.query.all();
    global startLat, startLng, jsonarray, finalpath, test, midlength, startid, endId, sequence, endLat, endLng, endId, location

    length = len(Query)

    print length
    for x in range(length):
        if Query[x].is_end_point==0 : # MId Queryints value
           dictmid={"lat":Query[x].lat,"lng":Query[x].lng,"id":Query[x].id}
           jsonarray[Query[x].id]=dictmid

        elif Query[x].is_end_point==1 :# Start points value
            startLat=str(Query[x].lat)
            startLng=str(Query[x].lng)
            startid=str(Query[x].id)

        else:                           # End points value
            endLat=str(Query[x].lat)
            endLng=str(Query[x].lng)
            endId=str(Query[x].id)

#-------------------------------------------------------------------------------------------------------------
    print "jsonarray" + str(jsonarray)

    midlength = len(jsonarray)
    while midlength > 1:
        print"Loop" + str(count)
        way = {}
        for key in jsonarray.iteritems():
            lat = key[1]['lat']
            lng = key[1]['lng']
            id = key[1]['id']
            test = lyftcall(startLat, startLng, lat, lng)
            way[str(startid) + "-" + str(id)] = int(test)
            print "way=" + str(way)
        minvalue = min(way, key=way.get)
        test = int(minvalue.split("-")[-1])
        print "test" + str(test)
        if test in jsonarray: del jsonarray[test]
        print jsonarray
        midlength = len(jsonarray)
        print "midlength" + str(midlength)
        Data = Location.query.filter_by(id=test).first()
        startLat = Data.lat
        startLng = Data.lng
        startid = Data.id
        print str(startLat)
        print str(startLng)
        count = count + 1
        finalpath[count] = minvalue

    count = count + 1
    finalpath[count] = str(test) + "-" + str(jsonarray.keys()[0])
    count = count + 1
    finalpath[count] = str(jsonarray.keys()[0]) + "-" + str(endId)
    print "Finalpath" + str(finalpath)
    test = {}
    sequence = 1
    for key in finalpath.iteritems():
        test[sequence] = str(key[1].split("-")[0])
        sequence = sequence + 1
    location = 0;
    midL = {}
    for key in test.iteritems():
        FinalQuery = Location.query.filter_by(id=int(key[1])).first()
        midL[location] = {'lat': FinalQuery.lat, 'lon': FinalQuery.lng}
        location += 1

    midL[location] = {'lat': endLat, 'lon': endLng}

    print "MIDDLE" + str(midL)

    print "test" + str(test)
    print "way" + str(way)
    print "jsonarray" + str(jsonarray)


    # CREATING STRING FOR THE OPTIMIZED ROUTE

    l= len(midL)
    strng = str(l)

    for x in range(l):
        strng += ',' + str(midL[x]['lat']) + ',' + str(midL[x]['lon'])
    print 'string:'+ strng

    # -----------------------------------------------------------------
    # lyft api logic
    lat = []
    lng = []
    cords = strng.split(',')
    
    # fetching the no of locations to be covered
    no_of_cords = int(cords[0])
    count = 0


    # setting the lat and lng list from the string given as a parameter
    while count < no_of_cords:
        lat.append(cords[(2 * count) + 1])
        lng.append(cords[(2 * count) + 2])

        count += 1

    # dictionary for each type of ride
    lyft = {'min_cost': 0,
            'max_cost': 0,
            'avg_cost': 0,
            'time': 0,
            'distance': 0,
            'type': 'lyft'
            }
    lyft_plus = {'min_cost': 0,
                 'max_cost': 0,
                 'avg_cost': 0,
                 'time': 0,
                 'distance': 0,
                 'type': 'lyft_plus'
                 }
    lyft_premier = {'min_cost': 0,
                    'max_cost': 0,
                    'avg_cost': 0,
                    'time': 0,
                    'distance': 0,
                    'type': 'lyft_premier'
                    }
    # making call for ride between each 2 sets of (lat,lng)
    count = 0
    while count != (no_of_cords - 1):
        payload = {'start_lat': lat[count], 'start_lng': lng[count], 'end_lat': lat[count + 1],
                   'end_lng': lng[count + 1]}
        headers = {
            'Authorization': 'Bearer gAAAAABYOh2rXUfRCrbLM5kt_kICcQvAuyefz_9pJsgGhHQLhKnu3idO-pEgZN6xBWRqXyy0vaOFPse2Rk4i26RCUhKOBvYvnXAW17OwAGpmXdEzG_38O-sYbz9zd_OHdswBrRXFGKy9lBflP0eVWLP3rsCQJd1JuBFJdks2AfawYNAviW1wB2s=',
            'Accept-Language': 'en_US','Content-Type': 'application/json',}
        stop = requests.get(
            'https://api.lyft.com/v1/cost?',
            headers=headers, params=payload)
        # print stop.json()
        result = stop.json()
        count += 1

        # assigning values in the dictionary
        for iteration in result["cost_estimates"]:
            if iteration["ride_type"] == "lyft_plus":
                lyft_plus["min_cost"] += iteration["estimated_cost_cents_min"]
                lyft_plus["max_cost"] += iteration["estimated_cost_cents_max"]
                lyft_plus["time"] += iteration["estimated_duration_seconds"]
                lyft_plus["distance"] += Decimal(iteration["estimated_distance_miles"]* 0.01).quantize(Decimal("0.01"))
                # yield lyft_plus
            elif iteration["ride_type"] == "lyft":
                lyft["min_cost"] += iteration["estimated_cost_cents_min"]
                lyft["max_cost"] += iteration["estimated_cost_cents_max"]
                lyft["time"] += iteration["estimated_duration_seconds"]
                lyft["distance"] += Decimal(iteration["estimated_distance_miles"]* 0.01).quantize(Decimal("0.01"))
                # yield lyft
            elif iteration["ride_type"] == "lyft_premier":
                lyft_premier["min_cost"] += iteration["estimated_cost_cents_min"]
                lyft_premier["max_cost"] += iteration["estimated_cost_cents_max"]
                lyft_premier["time"] += iteration["estimated_duration_seconds"]
                lyft_premier["distance"] += Decimal(iteration["estimated_distance_miles"]* 0.01).quantize(Decimal("0.01"))
                # yield lyft_premier
    # FINDING THE AVERAGE COST
    a = (lyft['max_cost'] + lyft['min_cost']) / 2
    lyft['avg_cost'] = Decimal(a * 0.01).quantize(Decimal("0.01"))
    b = (lyft_plus['max_cost'] + lyft_plus['min_cost']) / 2
    lyft_plus['avg_cost'] = Decimal(b * 0.01).quantize(Decimal("0.01"))
    c = (lyft_premier['max_cost'] + lyft_premier['min_cost']) / 2
    lyft_premier['avg_cost'] = Decimal(c * 0.01).quantize(Decimal("0.01"))

    lyft_premier["min_cost"] = Decimal(lyft_premier["min_cost"]* 0.01).quantize(Decimal("0.01"))
    lyft["min_cost"] = Decimal(lyft["min_cost"]* 0.01).quantize(Decimal("0.01"))
    lyft_plus["min_cost"] = Decimal(lyft_plus["min_cost"]* 0.01).quantize(Decimal("0.01"))
    lyft_premier["max_cost"] = Decimal(lyft_premier["max_cost"]* 0.01).quantize(Decimal("0.01"))
    lyft["max_cost"] = Decimal(lyft["max_cost"]* 0.01).quantize(Decimal("0.01"))
    lyft_plus["max_cost"] = Decimal(lyft_plus["max_cost"]* 0.01).quantize(Decimal("0.01"))

    print "FULL TRIP STATISTICS"
    print "For lyft:", lyft
    print "For lyft_plus:", lyft_plus
    print "For lyft_premier:", lyft_premier
    # all={'lyft':lyft,'lyft_plus':lyft_plus,'lyft_premier':lyft_premier, 'string':strng,'way':way}
    all = {'lyft': lyft, 'lyft_plus': lyft_plus, 'lyft_premier': lyft_premier}
    print all
    print 'RETURNING FROM THE FUNCTION'
    return all



# --------------------------------------------------------------------------------------------------------------------
def lyftcall(sLat,sLon,eLat,eLon):
    global i, total_min_cost, total_max_cost, ride, locationlist
    payload = {'start_lat': sLat, 'start_lng': sLon, 'end_lat': eLat, 'end_lng': eLon}
    headers = {
        'Authorization': 'Bearer gAAAAABYOh2rXUfRCrbLM5kt_kICcQvAuyefz_9pJsgGhHQLhKnu3idO-pEgZN6xBWRqXyy0vaOFPse2Rk4i26RCUhKOBvYvnXAW17OwAGpmXdEzG_38O-sYbz9zd_OHdswBrRXFGKy9lBflP0eVWLP3rsCQJd1JuBFJdks2AfawYNAviW1wB2s=',
        'Accept-Language': 'en_US',
        'Content-Type': 'application/json',
    }

    cost = requests.get(
        'https://api.lyft.com/v1/cost?',
        headers=headers, params=payload)

    dataX = cost.json()
    lyft = {'min_cost': 0,
            'max_cost': 0,
            'avg_cost': 0,
            'time': 0,
            'distance': 0,
            'type': 'lyft'
            }
    for iteration in dataX["cost_estimates"]:
        if iteration["ride_type"] == "lyft":
            lyft["min_cost"] = iteration["estimated_cost_cents_min"]
            lyft["max_cost"] = iteration["estimated_cost_cents_max"]
            a = (lyft['max_cost'] + lyft['min_cost']) / 200

    print 'a'+str(a)
    return a