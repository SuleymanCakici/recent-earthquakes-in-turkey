from flask import  Flask, jsonify, request

import pandas as pd
import re

from urllib.request import urlopen
import json
from bs4 import BeautifulSoup

import warnings
warnings.simplefilter("ignore")
# ------------------------------------------------------------------------------------------------------------
def getDataFromKandilli():
    try:
        result = []
        data = urlopen('http://www.koeri.boun.edu.tr/scripts/sondepremler.asp').read()
        soup = BeautifulSoup(data, 'html.parser', from_encoding='utf8')
        data = soup.find_all('pre')
        data = str(data).strip().split('--------------')[2]
        data = data.split('\n')
        data = data[1:-2]
        
        indices = range(len(data))
        for i in indices:
            row = str(data[i].strip())
            row = re.sub(r'[\s]+', ' ', row)
            rowList = row.split(' ')
            json_data = json.dumps({
                "id": i+1,
                "date": rowList[0],
                "hour": rowList[1],
                "latitude": float(rowList[2]),
                "longitude": float(rowList[3]),
                "depth": float(rowList[4]),
                "size": float(rowList[6]),
                "province": rowList[8],
                "city": re.sub(r'[()]','', rowList[9]) if rowList[9] != 'İlksel' else re.sub(r'\)', '', re.sub(r'.*\(','', rowList[8])), 
                "attribute": rowList[-1]
            }, sort_keys=False)

            result.append(json.loads(json_data))
    except:
        result = None
    return result
# ------------------------------------------------------------------------------------------------------------
app = Flask(__name__)
# ------------------------------------------------------------------------------------------------------------
@app.route('/recentEQ', methods=['GET'])
def main():
    # Get data sent via JSON or browser as ../suitable?customerIdx=P00002C00001&tableWeight=1&moreThanOne=1
    reqInfo = request.get_json() if (request.is_json) else request.args.to_dict()
    # Get the argument names sent via the request...
    reqKeys = reqInfo.keys()
    # Get parameters from relevant arguments of the request...
    size = float(reqInfo['size']) if 'size' in reqKeys else None
    location = reqInfo['city'] if 'city' in reqKeys else None
    showMsg = bool(reqInfo['showMsg']) if 'showMsg' in reqKeys else False
    # Fetch recent earthquake data from Kandilli Observatory... 
    data = getDataFromKandilli()
    # Return an error message in case any problems are encountered...
    if data == None:        
        return pd.DataFrame(data=['Oopps...'],columns=['Message'])
    # Convert data to dataframe...
    df = pd.DataFrame(data=data, index=None)
    # Filter by size if requested...
    if size is not None:
        df = df[df['size'] >= size]
    # Filter by location if requested...
    if location is not None:
        df = df[df['city'] == location.upper().strip()]
    # Convert JSON data for sharing...
    dfJSON = json.loads(df.to_json(orient='split'))
    dfKeys = dfJSON['columns']
    dfData = dfJSON['data']
    # Prepare data to be shared...
    resData = []
    for data in dfData:
        jsonData = {}
        for i in range(len(dfKeys)):
            jsonData.update({dfKeys[i]:data[i]})

        jsonDataOrdered = json.dumps(jsonData, sort_keys=False)
        resData.append(json.loads(jsonDataOrdered))
    # Share the data according to 'showMsg' parameter...
    if showMsg is True:
        msg = []
        for i in range(len(resData)):
            msg.append(f'{resData[i]["date"]} {resData[i]["hour"]} tarihinde {resData[i]["city"]} ilinde {resData[i]["size"]} büyüklüğünde {resData[i]["attribute"]} bir deprem meydana geldi.')
        return msg
    else:
        return resData
# ------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=5000)