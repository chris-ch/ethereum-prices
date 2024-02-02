# ethereum-prices

## Pre-requisites

### AWS Configuration
Create an Access Key for your User in the AWS console (top left, "Security credentials") for the CLI Use Case.

Keep track of the Access Key and its related Secret key. From the command-line run `aws configure`.

Environment variables required for the project:

```
export AWS_ACCESS_KEY_ID=
export AWS_DEFAULT_REGION=
export AWS_SECRET_ACCESS_KEY=
export DERIBIT_CLIENT_ID=
export DERIBIT_CLIENT_SECRET=
export SLACK_WEBHOOK_URL=
```

Manually initialize terraform:
```
export TF_VAR_aws_stage=test\n" >> /home/python/.bashrc
export TF_VAR_aws_region=us-east-1\n" >> /home/python/.bashrc
export TF_VAR_aws_account_id=$(aws sts get-caller-identity | jq -r '.Account')\n" >> /home/python/.bashrc
```

## Testing

`poetry run pytest`

## Scripts

`poetry run aggregate-prices --bucket-name=test-binance-prices-255120844515 --instrument-code=BTCUSDT --count-years=6`
