__author__ = 'jonhall'
#
## Generate Current VSI BILLING DETAIL.
##

import SoftLayer,logging
from flask import Flask, render_template, request
from flask_session import Session
from decimal import Decimal

global username,apiKey

######################################
# Enable Logging
######################################

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p',
                    level=logging.WARNING)

app = Flask(__name__)
app.secret_key = 'fherts2(&sdfsdfsdf'

app.config.from_object(__name__)
Session(app)

app.config['SECRET_KEY'] = "cloud2018"


@app.route('/', methods=["GET","POST"])
def input():
    return render_template('input.html')


@app.route('/getItems', methods=["GET", "POST"])
def getItems():
    if request.method == "POST":
        username = request.form['username']
        apiKey = request.form['apiKey']

    client = SoftLayer.Client(username=username, api_key=apiKey, timeout=60)

    try:
        hourlyServiceItems = client['Account'].getHourlyVirtualGuests(mask="billingItem.id")
    except SoftLayer.SoftLayerAPIError as e:
        logging.warning("Account::getHourlyVirtualGuests(): %s, %s" % (e.faultCode, e.faultString))

    logging.warning("Currently %s active billing items." %  (len(hourlyServiceItems)))

    hourlyItems=[]
    for item in hourlyServiceItems:
        id = item['billingItem']['id']
        logging.warning("Getting billing item %s" % id)
        # Get Parent Item Details
        try:
            hourlyServiceItem = client['Billing_Item'].getObject(id=id,
                mask="id, parentId, createDate, currentHourlyCharge, categoryCode, description, cycleStartDate, hostName, domainName, hourlyRecurringFee, hoursUsed, lastBillDate, nextBillDate")
        except SoftLayer.SoftLayerAPIError as e:
            logging.warning("Billing_item::getObject(): %s, %s" % (e.faultCode, e.faultString))

        # Get currentHourlyCharge & hourlyRecurringFee for Associated Children Items
        try:
            hourlyServiceItemsChildren = client['Billing_Item'].getAssociatedChildren(id=id,
                mask="currentHourlyCharge, hourlyRecurringFee")
        except SoftLayer.SoftLayerAPIError as e:
            logging.warning("Billing_Item::getAssociatedChildren(): %s, %s" % (e.faultCode, e.faultString))


        ## Iterate and Sum hourlyRecurringFee & currentHourlyCharge for Parent + children items
        hourlyRecurringFee = Decimal(hourlyServiceItem['hourlyRecurringFee']) + sum(
            Decimal(child['hourlyRecurringFee']) for child in hourlyServiceItemsChildren)

        currentHourlyCharge = Decimal(hourlyServiceItem['currentHourlyCharge']) + sum(
            Decimal(child['currentHourlyCharge']) for child in hourlyServiceItemsChildren)

        hourlyServiceItem['hourlyRecurringFee']=str(hourlyRecurringFee)
        hourlyServiceItem['currentHourlyCharge'] = str(currentHourlyCharge)

        # Append to List
        hourlyItems.append(hourlyServiceItem)

    return render_template("detail.html", detail=hourlyItems)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
