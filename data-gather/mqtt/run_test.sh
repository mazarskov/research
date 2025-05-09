#!/bin/bash

count=$1
rate=$2
conc=$3
output="${count}_${rate}conc${conc}"

pcap_file="${output}.pcap"

echo "Starting packet capture..."
tshark -i lo -w "$pcap_file" &
tshark_pid=$!

perun monitor data-gather/mqtt/mqtt_receiver.py --broker localhost --port 1883 --topic test/sensor --count "$count" &
receive_pid=$!
sleep 5
perun monitor data-gather/mqtt/mqtt_sender.py --broker localhost --port 1883 --topic test/sensor --rate "$rate" --payload-size 64 --concurrency "$conc" --count "$count" &
send_pid=$!

wait "$receive_pid"
wait "$send_pid"

echo "Stopping packet capture..."
kill "$tshark_pid"

python data-gather/mqtt/test_aggregator.py --sender sender_report.txt --receiver receiver_report.txt --output "${output}.txt"

sleep 1

rm sender_report.txt
rm receiver_report.txt
echo "Wiresark file saved as ${output}.pcap"
echo "Report saved as ${output}.txt"