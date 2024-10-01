from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import ReceivedRequest
from .ibapi_service import start_ibapi_connection, usFuture, usStk, mktOrder

import time, threading, logging
from django.db import transaction
from django.core.exceptions import ValidationError

# Create a lock for the IBAPI app object
app_lock = threading.Lock()
# Initialize the IBAPI connection (this will run once when the app starts)
app = start_ibapi_connection() #potentially have to move this function to apps.py and use ready() function
# To log errors
logger = logging.getLogger(__name__)

# Index view to show the status of the app
def index(request):
    recent_requests = ReceivedRequest.objects.all().order_by('-timestamp')[:5]
    return render(request, 'index.html', {'recent_requests': recent_requests})

# Webhook view to process incoming POST requests and save them to the database
@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("\nReceived POST data:", data)

            # Initialize tradeReqId to None for now
            trade_id = None

            #Just simple examples to simulate placing orders based on the exchange and symbol. No kill switch or portfolio related info implemented here!
            with app_lock:  # Ensure that only one thread interacts with the app at a time. This is to make sure it places orders one by one
                # Simulate placing orders based on the exchange and symbol
                if data.get('secmgs') == "secret-message":
                    if data.get('exchange') == "CME_MINI":
                        app.reqIds(3)
                        time.sleep(0.2)
                        trade_id = app.nextValidOrderId  # Save the returned tradeReqId
                        app.placeOrder(trade_id, usFuture("NQZ4"), mktOrder(data['direction'], 2))
                        #app.placeOrder(app.nextValidOrderId, usFuture("MNQZ4"), mktOrder(data['direction'], 2))
                        #app.placeOrder(app.nextValidOrderId, usStk("MNST"), mktOrder(data['direction'], 1))
                        print(f"{data['direction']}ing: NQU4")
                    elif data.get('exchange') == "NASDAQ":
                        app.reqIds(3)
                        time.sleep(0.2)
                        trade_id = app.nextValidOrderId  # Save the returned tradeReqId
                        app.placeOrder(trade_id, usStk("TSLA"), mktOrder(data['direction'], 1844))
                        print(f"{data['direction']}ing: TSLA")

            # Wrap the database save operation in an atomic block to ensure safe saving on database when webhooks all come at once
            with transaction.atomic():
                # Create and save the received request in the database
                received_request = ReceivedRequest(
                    strat_name=data.get('stratName'),
                    alert=data.get('alert'),
                    exchange=data.get('exchange'),
                    symbol=data.get('symbol'),
                    price=data.get('price'),
                    direction=data.get('direction'),
                    tradeReqId=trade_id  # Assign tradeReqId
                )
                received_request.save()

            return JsonResponse({"status": "Order received and processed"})
        
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return JsonResponse({"error": "Invalid input: " + str(e)}, status=400)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return JsonResponse({"error": "Internal server error"}, status=500)
        
    return JsonResponse({"error": "Invalid request method"}, status=400)


# View to display received POST requests from the database
def show_requests(request):
    requests = ReceivedRequest.objects.all().order_by('-timestamp')
    return render(request, 'show_requests.html', {'requests': requests})

def delete_request(request):
    if request.method == 'POST':
        try:
            request_id = request.POST.get('id')
            received_request = ReceivedRequest.objects.get(id=request_id)
            received_request.delete()
            return JsonResponse({'status': 'success'})
        except ReceivedRequest.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Request not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

# Trades page displays 20 most recent trades
def trades(request):
    trades_list = []
    consolidated_trades = []

    with app_lock:
        app.request_recent_trades()
        time.sleep(2) 
        # returns the 20 most recent trades
        trades_list = app.get_recent_trades()[:20]

        # Fetch consolidated trades
        consolidated_trades = app.get_consolidated_trades()
        #print(f"Fetched trades: {trades_list}")  # Debug print to check if trades are being fetched
        #print(f"Consolidated trades: {consolidated_trades}")  # Debug print for consolidated trades

    return render(request, 'trades.html', {
        'trades': trades_list,
        'consolidated_trades': consolidated_trades
    })

# AJAX view to refresh the trades data
def refresh_trades(request):
    if request.method == 'GET':
        trades_list = []
        consolidated_trades = []
        with app_lock:
            # Trigger request for recent trades from IBAPI
            app.request_recent_trades()
            time.sleep(2)
            # Returns the recent 20 trades
            trades_list = app.get_recent_trades()[:20]
            # Get the consolidated trades
            consolidated_trades = app.get_consolidated_trades()

        return JsonResponse({
            'status': 'success', 
            'trades': trades_list,
            'consolidated_trades': consolidated_trades
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def documentation(request):
    return render(request, 'documentation.html')
