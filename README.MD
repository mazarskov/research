## Commands to run HTTP tester

### First run receiver
`python http_test_receiver.py --port 8080 --count 100`

### Then run sender
`python http_test_sender.py --url http://localhost:8080 --count 100 --concurrency 100`

### Then run aggregator
`python http_test_aggregator.py --sender sender_report.txt --receiver receiver_report.txt --output results.txt`