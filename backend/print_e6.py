import sys
lines = open('tests/test_delivery_zones_and_checkout.py', encoding='utf-8').readlines()
sys.stdout.buffer.write(''.join(lines[510:530]).encode('utf-8'))
