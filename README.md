# ethereum-prices

## Pre-requisites

### AWS Configuration
Create an Access Key for your User in the AWS console (top left, "Security credentials") for the CLI Use Case.

Keep track of the Access Key and its related Secret key. From the command-line run `aws configure`.

Environment variables required for the project:

```shell
cat > .env <<EOT
TF_VAR_aws_stage=test
TF_VAR_aws_region=us-east-1
AWS_ACCESS_KEY_ID=xxxx
AWS_DEFAULT_REGION=us-east-1
AWS_SECRET_ACCESS_KEY=xxxx
DERIBIT_CLIENT_ID=xxxx
DERIBIT_CLIENT_SECRET=xxxx
SLACK_WEBHOOK_URL=xxxx
TF_VAR_slack_webhook_url=${SLACK_WEBHOOK_URL}
EOT
```

Manually setting variables from `.env`:

```shell
export $(cat .env | grep -v '^#' | xargs)
```

Manually initialize terraform:
```shell
export TF_VAR_aws_stage="test"
export TF_VAR_aws_region="us-east-1"
export TF_VAR_aws_account_id="$(aws sts get-caller-identity | jq -r '.Account')"
```

## Testing

`poetry run pytest`

## Scripts

`poetry run aggregate-prices --bucket-name=test-binance-prices-255120844515 --instrument-code=BTCUSDT --count-years=6`

`poetry run deribit-account -i $DERIBIT_CLIENT_ID -s $DERIBIT_CLIENT_SECRET --currency ETH`
