#!/usr/bin/python3

#This is a python3 script that gets the TV guide from the HDhomerun API

#Please keep in mind you need a physical device with a valid key to use this script. This is unofficial and is not supported or endorced by HDhomerun. Please use it at your own risk.


#Set this if you do not want to use the HDhomerun discover API. 
HDHOMERUN_PATH=""

#The output file
OUTPUT="out.xml"

import requests
import xml.etree.ElementTree as ET
import datetime

def getJSON(httpUrl):
    print("fetching "+httpUrl.split("?")[0])
    #initial fetch
    try:
        resp = requests.get(url=httpUrl)
    except:
        print("failed to get "+httpUrl)
        return -1
    #parse as json
    try:
        data = resp.json()
    except:
        print("failed to parse json")
        return -2
    return data



if (HDHOMERUN_PATH == ""):
    print("attempting to get HDhomerun from discover API")
    #fetch json from API
    result = getJSON("https://api.hdhomerun.com/discover") 
    if(type(result) != int):
        if(len(result) > 0):
            for device in result:
                print("found device %s at %s attempting to connect" % (device["DeviceID"], device["LocalIP"]))
                result2 = getJSON(device["DiscoverURL"])
                if (result2 != int):
                    print("successfully fetched disvover json from device")
                    print("Device is a %s. Setting URL to %s" % (result2["FriendlyName"], result2["BaseURL"]))
                    HDHOMERUN_PATH=result2["BaseURL"]
                else:
                    print("failed to connect to device %s" % device["DeviceID"])
            if(HDHOMERUN_PATH == ""):
                #reached if no devices could be contacted
                print("Could not connect to any devices")
                exit(3)
        else:
            print("no devices found")
            exit(2)

    else:
        print("failed to connect to API")
        exit(1)


def convertToIso(timestamp):
    year = str(timestamp.year)
    month = str(timestamp.month)
    if len(month) < 2:
        month = "0"+month
    day = str(timestamp.day)
    if len(day) < 2:
        day = "0"+day
    hour = str(timestamp.hour)
    if len(hour) < 2:
        hour = "0"+hour
    minute = str(timestamp.minute)
    if len(minute) < 2:
        minute="0"+minute
    second = str(timestamp.second)
    if len(second) < 2:
        second="0"+second
    return "%s%s%s%s%s%s" % (year,month,day,hour,minute,second)

#at this point HDHOMERUN_PATH is assumed to be a url
#get discover
result = getJSON(HDHOMERUN_PATH+"/discover.json")
if (type(result) != int):
    print("connected to %s id %s" % (result["FriendlyName"], result["DeviceID"]))
    print("getting auth key")
    key = result["DeviceAuth"]
    print("connecting to HDhomerun API to fetch guide")
    result2 = getJSON("https://api.hdhomerun.com/api/guide.php?DeviceAuth=%s" % (key))
    if (type(result2) != int):
        print("received guide in XML form")
        print("starting conversion")
        timestamp = datetime.datetime.now()
        guide = ET.Element('tv')
        guide.set("source-info-name", "HDhomerun API")
        guide.set("date", convertToIso(timestamp))
        for channel in result2:
            #define channel as channel number
            channelTag = ET.SubElement(guide, 'channel')
            channelTag.set("id", channel["GuideNumber"])
        #set display names
            displayInfo = ET.SubElement(channelTag, "display-name")
            displayInfo.text = channel["GuideNumber"]
            
            if("GuideName" in channel):
                displayInfo2 = ET.SubElement(channelTag, "display-name")
                displayInfo2.text = channel["GuideName"]

                displayInfo3 = ET.SubElement(channelTag, "display-name")
                displayInfo3.text = channel["GuideNumber"] + " " + channel["GuideName"]
            
            if("Affiliate" in channel):
                displayInfo4 = ET.SubElement(channelTag, "display-name")
                displayInfo4.text = channel["Affiliate"]

            #set tv program information
            for content in channel["Guide"]:
                contentTag = ET.SubElement(guide, 'programme')
                contentTag.set("channel", channel["GuideNumber"])
                contentTag.set("start", convertToIso(datetime.datetime.utcfromtimestamp(int(content["StartTime"]))))
                contentTag.set("stop", convertToIso(datetime.datetime.utcfromtimestamp(int(content["EndTime"]))))
                
                titleTag = ET.SubElement(contentTag, "title")
                titleTag.text = content["Title"]
                
                if "Synopsis" in content:
                    descTag = ET.SubElement(contentTag, "desc")
                    descTag.text = content["Synopsis"]
                
                if("OriginalAirdate" in content):
                    orgTag = ET.SubElement(contentTag, "previously-shown")
                    orgTag.set("start", convertToIso(datetime.datetime.utcfromtimestamp(int(content["OriginalAirdate"]))))

                if "ImageURL" in content:
                    iconTag = ET.SubElement(contentTag, "icon")
                    iconTag.set("src", content["ImageURL"])



                if("EpisodeNumber" in content):
                    episodeNumberTag = ET.SubElement(contentTag, "EpisodeNumber")
                    episodeNumberTag.set("system", "common")
                    episodeNumberTag.text = content["EpisodeNumber"]
                    
                if("EpisodeTitle" in content):
                    subTitleTag = ET.SubElement(contentTag, "sub-title")
                    subTitleTag.text = content["EpisodeTitle"]



        #write out
        print("writing to "+OUTPUT)
        b_xml = ET.tostring(guide)
        with open(OUTPUT, "wb") as f:
            f.write(b_xml)
            

            

    else:
        print("connection failed")
        exit(4)
else:
    print("failed to connect")
    exit(3)

