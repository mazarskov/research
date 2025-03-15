#!/bin/bash

count=$1
rate=$2
output="${count}_${rate}.txt"

perun monitor http_test_receiver.py --port 8080 --count "$count" &
sleep 5
perun monitor http_test_sender.py --url http://localhost:8080 --rate "$rate" --payload-size 64 --count "$count" &

wait 

python test_aggregator.py --sender sender_report.txt --receiver receiver_report.txt --output "$output"