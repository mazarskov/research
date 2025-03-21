#!/bin/bash

count=$1
rate=$2
conc=$3
output="${count}_${rate}conc${conc}"

pcap_file="${output}.pcap"

echo "Starting packet capture..."
tshark -i lo -w "$pcap_file" &
tshark_pid=$!

perun monitor mqtt_receiver.py --broker localhost --port 1883 --topic test/sensor --count "$count" &
receive_pid=$!
sleep 5
perun monitor mqtt_sender.py --broker localhost --port 1883 --topic test/sensor --rate "$rate" --payload-size 64 --concurrency "$conc" --count "$count" &
send_pid=$!

wait "$receive_pid"
wait "$send_pid"

echo "Stopping packet capture..."
kill "$tshark_pid"

python test_aggregator.py --sender sender_report.txt --receiver receiver_report.txt --output "${output}.txt"

echo "Wiresark file saved"