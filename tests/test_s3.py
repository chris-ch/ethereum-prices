import logging
import unittest
import boto3
import pandas 

from binanceprices import create_file, fetch_file

class S3AccessTestCase(unittest.TestCase):
    def setUp(self):
        self._account_id = boto3.client('sts').get_caller_identity().get('Account')
        self._aws_stage = "test"

    def test_addition(self):
        self.assertEqual(1+2, 3)

    def test_s3_load_existing_object(self):
        s3 = boto3.resource('s3')
        data = fetch_file(s3, f"{self._aws_stage}-binance-prices-{self._account_id}", "ETHUSDT/2023/2023-12.csv.zip")
        df = pandas.read_csv(data, compression="zip")
        self.assertEqual(df.index.size, 744)

    def test_s3_load_non_existing_object(self):
        s3 = boto3.resource('s3')
        data = fetch_file(s3, f"{self._aws_stage}-binance-prices-{self._account_id}", "dummy")
        self.assertIsNone(data)

    def test_s3_write_object(self):
        df = pandas.DataFrame([{"id": 1, "name": "abc"}, {"id": 2, "name": "def"}])
        s3 = boto3.resource('s3')
        create_file(s3, f"{self._aws_stage}-unit-testing-{self._account_id}", "abc-test", df)

    def tearDown(self):
        pass
