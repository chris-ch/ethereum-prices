import lambdas.aggregateprices as aggregateprices


def handler(event, context):
    return aggregateprices.handler(event, context)
