# Protocol testing

This is an open-source tool to compare MQTT, CoAP, HTTPs various stats. 

## Getting started

UV package and project manager highly recommended and all instructions are provided with the assumption of you having uv.

[UV installation and usage guide](https://docs.astral.sh/uv/getting-started/)

Wireshark is needed for this benchmark

[Wirehshark download](https://www.wireshark.org/download.html)

Mosquitto is needed for MQTT testing

[Mosquitto download](https://mosquitto.org/download/)

After installing run `uv venv` from root directory of this repository

Run `source .venv/bin/activate` to activate the virtual env

Run `uv pip install -r requirements.txt` to install the needed packages

Run `net start mosquitto` or directly from executable to start Mosquitto

## Running benchmarks (NO GUI)

Go to the folder of the protocol you want to test(CoAP, HTTP, MQTT)<br>`cd data-gather/coap` <br>`cd data-gather/http`<br>`cd data-gather/mqtt`

Benchmark script is structred in the following way:

`bash run_test_no_cpu.sh <count> <rate> <concurrency>`

Count - amount of messages to send

Rate - rate at which to send them

Concurrency - number of proccesses that will do the sending

Example of a benchmark which sends **100** messages at **10** msg/s with **1** concurrent proccess:<br>`bash run_test_no_cpu.sh 100 10 1`

**If you are on and Linux based distro using an Intel CPU** you can run the benchmark with additional CPU usage stastics by running `run_test.sh` insted of `run_test_no_cpu.sh`

## Results

If you ran with no cpu usage stats you will get two files, one text file and one Wireshark file
## EVERYTHING UNDER THIS LINE IS OUTDATED

### Commands to run HTTP tester(in this order)

### Run receiver
`python3 http_test_receiver.py --port 8080 --count 100`

### Run sender
`python3 http_test_sender.py --url http://localhost:8080 --rate 10 --payload-size 500`



### Run aggregator
`python3 test_aggregator.py --sender sender_report.txt --receiver receiver_report.txt --output results.txt`


### Commands to run MQTT tester(in this order)

### Run the broker
`net start mosquitto`
or run directly
`C:\Program Files\mosquitto\mosquitto.exe -v`

### Run receiver
`python3 mqtt_receiver.py --broker localhost --port 1883 --topic test/sensor --count 100`

### Run sender
`python3 mqtt_sender.py --broker localhost --port 1883 --topic test/sensor --count 100 --concurrency 10 --rate 10 --payload-size 500`

### Run aggregator
`python3 test_aggregator.py --sender sender_report.txt --receiver receiver_report.txt --output results.txt`


### Commands to run CoAP tester(in this order)

### Run receiver
`python3 coap_receiver.py --host localhost --port 5683 --resource test --count 100`

### Run sender
`python3 coap_sender.py --host localhost --port 5683 --resource test --count 100 --time 10 --rate 10 --payload-size 500 --concurrency 1`

### Run aggregator
`python3 test_aggregator.py --sender sender_report.txt --receiver receiver_report.txt --output results.txt`