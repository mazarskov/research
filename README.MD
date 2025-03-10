## Commands to run HTTP tester(in this order)

### Run receiver
`python3 http_test_receiver.py --port 8080 --count 100`

### Run sender
`python3 http_test_sender.py --url http://localhost:8080 --rate 10 --payload-size 500`



### Run aggregator
`python3 test_aggregator.py --sender sender_report.txt --receiver receiver_report.txt --output results.txt`


## Commands to run MQTT tester(in this order)

### Run the broker
`net start mosquitto`
or run directly
`C:\Program Files\mosquitto\mosquitto.exe -v`

### Run receiver
`python3 mqtt_receiver.py --broker localhost --port 1883 --topic test/sensor --count 1000`

### Run sender
`python3 mqtt_sender.py --broker localhost --port 1883 --topic test/sensor --count 1000 --concurrency 100`

### Run aggregator
`python3 test_aggregator.py --sender sender_report.txt --receiver receiver_report.txt --output results.txt`


## Commands to run CoAP tester(in this order)

### Run receiver
`python3 coap_receiver.py --host localhost --port 5683 --resource test --count 10000`

### Run sender
`python3 coap_sender.py --host localhost --port 5683 --resource test --count 10000 --concurrency 100`

### Run aggregator
`python3 test_aggregator.py --sender sender_report.txt --receiver receiver_report.txt --output results.txt`