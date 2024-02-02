# ethereum-prices

## Pre-requisites

### AWS Configuration
Create an Access Key for your User in the AWS console (top left, "Security credentials") for the CLI Use Case.

Keep track of the Access Key and its related Secret key. From the command-line run `aws configure`.

Environment variables required for the project:

```
cat > .env <<EOT
TF_VAR_aws_stage=test
AWS_ACCESS_KEY_ID=xxxx
AWS_DEFAULT_REGION=us-east-1
AWS_SECRET_ACCESS_KEY=xxxx
DERIBIT_CLIENT_ID=xxxx
DERIBIT_CLIENT_SECRET=xxxx
SLACK_WEBHOOK_URL=xxxx
TF_VAR_slack_webhook_url=${SLACK_WEBHOOK_URL}
EOT
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
