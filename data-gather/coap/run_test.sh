#!/bin/bash

count=$1
rate=$2
output="${count}_${rate}.txt"

perun monitor coap_receiver.py --host localhost --port 5683 --resource test --count "$count" &
sleep 5
perun monitor coap_sender.py --host localhost --port 5683 --resource test --rate "$rate" --payload-size 64 --concurrency 10 --count "$count" &

wait 

python test_aggregator.py --sender sender_report.txt --receiver receiver_report.txt --output "$output"